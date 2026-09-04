from decimal import Decimal

from django.test import TestCase

from rates.forms import RatePlanForm
from . import factories


class ContractAwareForm(TestCase):
    def setUp(self):
        self.hotel = factories.hotel()
        self.channel = factories.channel()
        self.other = factories.channel(code="expedia", name="Expedia")
        self.rule = factories.rule(self.channel, self.hotel)

    def bound(self, **overrides):
        data = {
            "name": "Flexible",
            "channel": self.channel.pk,
            "price": "210.00",
            "min_stay_nights": 2,
            "cancellation_days": 3,
        }
        data.update(overrides)
        return data

    def test_a_new_line_starts_on_the_contract_values(self):
        form = RatePlanForm(rule=self.rule, locked_channel=self.channel)
        self.assertEqual(form.initial["price"], Decimal("180.00"))
        self.assertEqual(form.initial["min_stay_nights"], 2)
        self.assertEqual(form.initial["cancellation_days"], 3)

    def test_the_form_refuses_what_the_rules_refuse(self):
        form = RatePlanForm(self.bound(price="150.00"), rule=self.rule, locked_channel=self.channel)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_a_posted_channel_is_ignored_when_the_channel_is_locked(self):
        form = RatePlanForm(
            self.bound(channel=self.other.pk), rule=self.rule, locked_channel=self.channel
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["channel"], self.channel)

    def test_an_existing_line_keeps_its_own_channel(self):
        existing = factories.plan(self.hotel, self.other)
        form = RatePlanForm(instance=existing, rule=self.rule, locked_channel=self.channel)
        self.assertEqual(form.initial["channel"], self.other.pk)

    def test_without_a_rule_nothing_is_enforced(self):
        form = RatePlanForm(self.bound(price="1.00"), rule=None)
        self.assertTrue(form.is_valid(), form.errors)
