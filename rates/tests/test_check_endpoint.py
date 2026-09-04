from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from rates.models import RatePlan
from . import factories

PREFIX = "rate_plans"


class CheckEndpoint(TestCase):
    def setUp(self):
        self.hotel = factories.hotel()
        self.elsewhere = factories.hotel(name="Villa Bellevue", rack_rate="380.00")
        self.booking = factories.channel()
        self.expedia = factories.channel(code="expedia", name="Expedia")
        self.rule = factories.rule(self.booking, self.hotel)
        self.plan = factories.plan(self.hotel, self.booking)
        self.user = factories.partner(self.booking)
        self.client.force_login(self.user)

    def url(self, hotel=None):
        return reverse("admin:rates_hotel_check_rate", args=[(hotel or self.hotel).pk])

    def check(self, **overrides):
        data = {"name": "Flexible", "price": "210.00", "min_stay_nights": "2", "cancellation_days": "3"}
        data.update(overrides)
        return self.client.post(self.url(), data)

    def test_an_anonymous_visitor_is_sent_to_the_login_page(self):
        self.assertEqual(Client().post(self.url(), {}).status_code, 302)

    def test_a_staff_user_without_the_permission_is_refused(self):
        User.objects.create_user("intern", password="demo", is_staff=True)
        other = Client()
        other.login(username="intern", password="demo")
        self.assertEqual(other.post(self.url(), {}).status_code, 403)

    def test_a_get_is_refused(self):
        self.assertEqual(self.client.get(self.url()).status_code, 400)

    def test_a_hotel_without_a_contract_answers_404(self):
        self.assertEqual(self.client.post(self.url(self.elsewhere), {}).status_code, 404)

    def test_a_price_under_the_floor_comes_back_as_an_error(self):
        errors = self.check(price="150.00").json()["errors"]
        self.assertIn("price", errors)

    def test_untouched_fields_are_not_reported_as_required(self):
        errors = self.client.post(self.url(), {"price": "150.00"}).json()["errors"]
        self.assertEqual(list(errors), ["price"])

    def test_a_forged_channel_does_not_change_the_verdict(self):
        mine = self.check(price="150.00").json()["errors"]["price"]
        forged = self.check(price="150.00", channel=str(self.expedia.pk)).json()["errors"]["price"]
        self.assertEqual(mine, forged)

    def test_nothing_is_written(self):
        before = list(RatePlan.objects.values_list("price", flat=True))
        self.check(price="150.00")
        self.assertEqual(list(RatePlan.objects.values_list("price", flat=True)), before)

    def test_the_verdict_matches_what_saving_would_say(self):
        live = self.check(price="150.00").json()["errors"]["price"]

        saved = self.client.post(reverse("admin:rates_hotel_change", args=[self.hotel.pk]), {
            f"{PREFIX}-TOTAL_FORMS": "1",
            f"{PREFIX}-INITIAL_FORMS": "1",
            f"{PREFIX}-MIN_NUM_FORMS": "0",
            f"{PREFIX}-MAX_NUM_FORMS": "1000",
            f"{PREFIX}-0-id": str(self.plan.pk),
            f"{PREFIX}-0-name": "Flexible",
            f"{PREFIX}-0-channel": str(self.booking.pk),
            f"{PREFIX}-0-price": "150.00",
            f"{PREFIX}-0-min_stay_nights": "2",
            f"{PREFIX}-0-cancellation_days": "3",
            f"{PREFIX}-0-active": "on",
        })
        formset = saved.context["inline_admin_formsets"][0].formset
        self.assertEqual(live, formset.forms[0].errors["price"])
