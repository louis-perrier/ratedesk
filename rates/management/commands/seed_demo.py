from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from rates.access import MANAGER_GROUP, PARTNER_GROUP
from rates.models import Channel, ChannelPartner, ChannelRule, Hotel, RatePlan

PASSWORD = "demo"

HOTELS = [
    ("Le Grand Pavois", "La Rochelle", "240.00"),
    ("Villa Bellevue", "Nice", "380.00"),
]

CHANNELS = [
    ("Booking.com", "booking", "0.150"),
    ("Expedia", "expedia", "0.180"),
    ("Direct", "direct", "0.000"),
]

# Expedia n'a volontairement pas de contrat sur Villa Bellevue : son partenaire
# ne doit pas voir cet hotel du tout.
RULES = [
    ("booking", "Le Grand Pavois", "180.00", 20, 2, 3),
    ("booking", "Villa Bellevue", "300.00", 15, 2, 5),
    ("expedia", "Le Grand Pavois", "195.00", 15, 1, 2),
]

PLANS = [
    ("Le Grand Pavois", "booking", "Flexible", "210.00", 2, 3),
    ("Le Grand Pavois", "expedia", "Non refundable", "209.00", 1, 2),
    ("Villa Bellevue", "booking", "Early bird", "330.00", 2, 5),
]


class Command(BaseCommand):
    help = "Fill the database with two hotels, three channels and the demo accounts."

    def handle(self, *args, **options):
        hotels = {}
        for name, city, rack in HOTELS:
            hotels[name], _ = Hotel.objects.update_or_create(
                name=name, defaults={"city": city, "rack_rate": Decimal(rack)}
            )

        channels = {}
        for name, code, commission in CHANNELS:
            channels[code], _ = Channel.objects.update_or_create(
                code=code, defaults={"name": name, "commission_rate": Decimal(commission)}
            )

        for code, hotel, floor, discount, stay, cancel in RULES:
            ChannelRule.objects.update_or_create(
                channel=channels[code],
                hotel=hotels[hotel],
                defaults={
                    "floor_price": Decimal(floor),
                    "max_discount_pct": discount,
                    "min_stay_nights": stay,
                    "default_cancellation_days": cancel,
                },
            )

        for hotel, code, name, price, stay, cancel in PLANS:
            RatePlan.objects.update_or_create(
                hotel=hotels[hotel],
                channel=channels[code],
                name=name,
                defaults={
                    "price": Decimal(price),
                    "min_stay_nights": stay,
                    "cancellation_days": cancel,
                },
            )

        self.account("manager", MANAGER_GROUP)
        for code in ("booking", "expedia"):
            user = self.account(code, PARTNER_GROUP)
            ChannelPartner.objects.update_or_create(user=user, defaults={"channel": channels[code]})

        self.stdout.write(f"Accounts ready. Password for all of them: {PASSWORD}")

    def account(self, username, group):
        user, _ = User.objects.update_or_create(username=username, defaults={"is_staff": True})
        user.set_password(PASSWORD)
        user.save()
        user.groups.set([Group.objects.get(name=group)])
        return user
