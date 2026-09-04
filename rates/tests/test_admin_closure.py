from django.test import TestCase
from django.urls import reverse

from rates.models import RatePlan
from . import factories

PREFIX = "rate_plans"


class PartnerClosure(TestCase):
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
        return reverse("admin:rates_hotel_change", args=[(hotel or self.hotel).pk])

    def formset(self, **overrides):
        data = {
            f"{PREFIX}-TOTAL_FORMS": "1",
            f"{PREFIX}-INITIAL_FORMS": "1",
            f"{PREFIX}-MIN_NUM_FORMS": "0",
            f"{PREFIX}-MAX_NUM_FORMS": "1000",
            f"{PREFIX}-0-id": str(self.plan.pk),
            f"{PREFIX}-0-name": "Flexible",
            f"{PREFIX}-0-channel": str(self.booking.pk),
            f"{PREFIX}-0-price": "210.00",
            f"{PREFIX}-0-min_stay_nights": "2",
            f"{PREFIX}-0-cancellation_days": "3",
            f"{PREFIX}-0-active": "on",
        }
        data.update(overrides)
        return data

    def test_a_hotel_without_a_contract_is_not_reachable(self):
        self.assertEqual(self.client.get(self.url(self.elsewhere)).status_code, 302)

    def test_the_changelist_hides_a_hotel_without_a_contract(self):
        response = self.client.get(reverse("admin:rates_hotel_changelist"))
        self.assertContains(response, self.hotel.name)
        self.assertNotContains(response, self.elsewhere.name)

    def test_a_forged_channel_leaves_the_rate_plan_where_it_was(self):
        self.client.post(self.url(), self.formset(**{f"{PREFIX}-0-channel": str(self.expedia.pk)}))
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.channel, self.booking)

    def test_a_price_under_the_floor_is_refused_on_save(self):
        response = self.client.post(self.url(), self.formset(**{f"{PREFIX}-0-price": "150.00"}))
        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(str(self.plan.price), "210.00")

    def test_a_compliant_price_goes_through(self):
        response = self.client.post(self.url(), self.formset(**{f"{PREFIX}-0-price": "205.00"}))
        self.assertEqual(response.status_code, 302)
        self.plan.refresh_from_db()
        self.assertEqual(str(self.plan.price), "205.00")

    def test_the_channel_choices_are_limited_to_his_own(self):
        response = self.client.get(self.url())
        formset = response.context["inline_admin_formsets"][0].formset
        self.assertEqual(list(formset.forms[0].fields["channel"].queryset), [self.booking])

    def test_a_partner_cannot_add_or_delete_a_hotel(self):
        self.assertEqual(self.client.get(reverse("admin:rates_hotel_add")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:rates_hotel_delete", args=[self.hotel.pk])).status_code, 403)

    def test_a_rate_plan_of_another_channel_stays_hidden(self):
        theirs = factories.plan(self.hotel, self.expedia, name="Theirs")
        response = self.client.get(self.url())
        self.assertNotContains(response, "Theirs")
        self.assertTrue(RatePlan.objects.filter(pk=theirs.pk).exists())


class ManagerReach(TestCase):
    def setUp(self):
        self.hotel = factories.hotel()
        self.booking = factories.channel()
        self.rule = factories.rule(self.booking, self.hotel)
        self.plan = factories.plan(self.hotel, self.booking)
        self.client.force_login(factories.manager())

    def test_a_manager_is_not_bound_by_a_contract(self):
        url = reverse("admin:rates_hotel_change", args=[self.hotel.pk])
        response = self.client.post(url, {
            "name": self.hotel.name,
            "city": self.hotel.city,
            "rack_rate": "240.00",
            "active": "on",
            f"{PREFIX}-TOTAL_FORMS": "1",
            f"{PREFIX}-INITIAL_FORMS": "1",
            f"{PREFIX}-MIN_NUM_FORMS": "0",
            f"{PREFIX}-MAX_NUM_FORMS": "1000",
            f"{PREFIX}-0-id": str(self.plan.pk),
            f"{PREFIX}-0-name": "Flexible",
            f"{PREFIX}-0-channel": str(self.booking.pk),
            f"{PREFIX}-0-price": "90.00",
            f"{PREFIX}-0-min_stay_nights": "1",
            f"{PREFIX}-0-cancellation_days": "1",
            f"{PREFIX}-0-active": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.plan.refresh_from_db()
        self.assertEqual(str(self.plan.price), "90.00")


class ChangePage(TestCase):
    def setUp(self):
        self.hotel = factories.hotel()
        self.booking = factories.channel()
        self.rule = factories.rule(self.booking, self.hotel)
        self.user = factories.partner(self.booking)
        self.client.force_login(self.user)

    def test_the_page_carries_the_script_and_its_endpoint(self):
        response = self.client.get(reverse("admin:rates_hotel_change", args=[self.hotel.pk]))
        self.assertContains(response, "rate-validation-config")
        self.assertContains(response, "rates/inline-validation.js")
        self.assertContains(response, reverse("admin:rates_hotel_check_rate", args=[self.hotel.pk]))

    def test_an_empty_line_is_offered_with_the_contract_values(self):
        response = self.client.get(reverse("admin:rates_hotel_change", args=[self.hotel.pk]))
        formset = response.context["inline_admin_formsets"][0].formset
        self.assertEqual(formset.forms[-1].initial["price"], self.rule.floor_price)

    def test_the_add_page_carries_no_inline(self):
        manager = factories.manager()
        self.client.force_login(manager)
        response = self.client.get(reverse("admin:rates_hotel_add"))
        self.assertEqual(response.context["inline_admin_formsets"], [])
