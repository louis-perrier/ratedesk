from decimal import Decimal

from django.contrib.auth.models import Group, User

from rates.access import MANAGER_GROUP, PARTNER_GROUP
from rates.models import Channel, ChannelPartner, ChannelRule, Hotel, RatePlan


def hotel(name="Le Grand Pavois", rack_rate="240.00"):
    return Hotel.objects.create(name=name, city="La Rochelle", rack_rate=Decimal(rack_rate))


def channel(code="booking", name="Booking.com"):
    return Channel.objects.create(name=name, code=code, commission_rate=Decimal("0.150"))


def rule(channel, hotel, floor="180.00", discount=20, stay=2, cancel=3):
    return ChannelRule.objects.create(
        channel=channel,
        hotel=hotel,
        floor_price=Decimal(floor),
        max_discount_pct=discount,
        min_stay_nights=stay,
        default_cancellation_days=cancel,
    )


def plan(hotel, channel, name="Flexible", price="210.00", stay=2, cancel=3):
    return RatePlan.objects.create(
        hotel=hotel,
        channel=channel,
        name=name,
        price=Decimal(price),
        min_stay_nights=stay,
        cancellation_days=cancel,
    )


def partner(channel, username="booking"):
    user = User.objects.create_user(username, password="demo", is_staff=True)
    user.groups.set([Group.objects.get(name=PARTNER_GROUP)])
    ChannelPartner.objects.create(user=user, channel=channel)
    return user


def manager(username="manager"):
    user = User.objects.create_user(username, password="demo", is_staff=True)
    user.groups.set([Group.objects.get(name=MANAGER_GROUP)])
    return user
