from django import forms

from . import rules
from .models import RatePlan


class RatePlanForm(forms.ModelForm):
    class Meta:
        model = RatePlan
        fields = ["name", "channel", "price", "min_stay_nights", "cancellation_days", "active"]

    def __init__(self, *args, rule=None, locked_channel=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.rule = rule
        self.rack_rate = rule.hotel.rack_rate if rule else None

        # self.fields est une copie profonde de base_fields, donc propre a cette instance.
        # La meme ecriture sur base_fields fuirait vers les autres requetes.
        if locked_channel is not None:
            field = self.fields["channel"]
            field.queryset = field.queryset.filter(pk=locked_channel.pk)
            field.disabled = True
            self.initial.setdefault("channel", locked_channel.pk)

        if rule is not None and self.instance.pk is None:
            for name, value in rules.defaults(rule).items():
                self.initial.setdefault(name, value)

    def clean(self):
        cleaned = super().clean()
        if self.rule is None:
            return cleaned
        found = rules.violations(
            self.rule,
            self.rack_rate,
            price=cleaned.get("price"),
            min_stay_nights=cleaned.get("min_stay_nights"),
        )
        for name, messages in found.items():
            for message in messages:
                self.add_error(name, message)
        return cleaned
