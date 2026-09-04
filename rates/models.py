from django.conf import settings
from django.db import models


class Hotel(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    rack_rate = models.DecimalField(max_digits=8, decimal_places=2)  # plein tarif, base des remises
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Channel(models.Model):
    name = models.CharField(max_length=80)
    code = models.SlugField(max_length=20, unique=True)
    commission_rate = models.DecimalField(max_digits=4, decimal_places=3)  # fraction, 0.150 = 15 %

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ChannelRule(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="rules")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="channel_rules")
    floor_price = models.DecimalField(max_digits=8, decimal_places=2)
    max_discount_pct = models.PositiveSmallIntegerField()  # entier, 20 = 20 %
    min_stay_nights = models.PositiveSmallIntegerField(default=1)
    default_cancellation_days = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["channel", "hotel"], name="one_rule_per_channel_and_hotel"),
        ]

    def __str__(self):
        return f"{self.channel} on {self.hotel}"


class RatePlan(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rate_plans")
    channel = models.ForeignKey(Channel, on_delete=models.PROTECT, related_name="rate_plans")
    name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    min_stay_nights = models.PositiveSmallIntegerField(default=1)
    cancellation_days = models.PositiveSmallIntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["channel__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.channel})"


class ChannelPartner(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="channel_partner"
    )
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="partners")

    def __str__(self):
        return f"{self.user} for {self.channel}"
