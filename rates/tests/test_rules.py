from decimal import Decimal

from django.test import TestCase

from rates import rules
from . import factories


class RuleChecks(TestCase):
    def setUp(self):
        self.hotel = factories.hotel()
        self.rule = factories.rule(factories.channel(), self.hotel)

    def check(self, **values):
        return rules.violations(self.rule, self.hotel.rack_rate, **values)

    def test_price_under_the_contract_floor_is_reported(self):
        found = self.check(price=Decimal("150.00"))
        self.assertIn("price", found)

    def test_discount_over_the_contract_cap_is_reported(self):
        # 240 de plein tarif, plafond a 20 %, donc 191 est au-dessus du plancher mais trop remise.
        found = self.check(price=Decimal("185.00"))
        self.assertIn("price", found)
        self.assertIn("23%", found["price"][0])

    def test_stay_under_the_contract_minimum_is_reported(self):
        self.assertIn("min_stay_nights", self.check(min_stay_nights=1))

    def test_missing_values_report_nothing(self):
        self.assertEqual(self.check(), {})

    def test_compliant_values_report_nothing(self):
        self.assertEqual(self.check(price=Decimal("210.00"), min_stay_nights=2), {})
