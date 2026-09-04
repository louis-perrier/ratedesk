from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.urls import path, reverse

from .access import partner_channel, rule_for
from .forms import RatePlanForm
from .models import Channel, ChannelPartner, ChannelRule, Hotel, RatePlan


class RatePlanInline(admin.TabularInline):
    model = RatePlan
    form = RatePlanForm

    class Media:
        js = ["rates/inline-validation.js"]
        css = {"all": ["rates/admin.css"]}

    def get_extra(self, request, obj=None, **kwargs):
        return 1 if partner_channel(request.user) else 0

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        channel = partner_channel(request.user)
        return qs.filter(channel=channel) if channel else qs


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    inlines = [RatePlanInline]
    list_display = ["name", "city", "rack_rate", "active"]
    list_filter = ["active", "city"]
    search_fields = ["name", "city"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        channel = partner_channel(request.user)
        if channel:
            return qs.filter(channel_rules__channel=channel).distinct()
        return qs

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def get_formset_kwargs(self, request, obj, inline, prefix):
        kwargs = super().get_formset_kwargs(request, obj, inline, prefix)
        if isinstance(inline, RatePlanInline):
            channel = partner_channel(request.user)
            kwargs["form_kwargs"] = {"rule": rule_for(channel, obj), "locked_channel": channel}
        return kwargs

    def get_readonly_fields(self, request, obj=None):
        if partner_channel(request.user):
            return ["name", "city", "rack_rate", "active"]
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request):
        return partner_channel(request.user) is None

    def has_delete_permission(self, request, obj=None):
        return partner_channel(request.user) is None

    def get_urls(self):
        checked = self.admin_site.admin_view(self.check_rate)
        return [path("<path:object_id>/check-rate/", checked, name="rates_hotel_check_rate")] + super().get_urls()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["validate_url"] = reverse("admin:rates_hotel_check_rate", args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context)

    def check_rate(self, request, object_id):
        if request.method != "POST":
            return HttpResponseBadRequest("POST expected")

        hotel = self.get_object(request, unquote(object_id))
        if hotel is None:
            return JsonResponse({"errors": {}}, status=404)

        # admin_view ne controle que is_staff, la permission de modele se verifie ici.
        if not self.has_change_permission(request, hotel):
            return HttpResponseForbidden("change permission required")

        channel = partner_channel(request.user)
        form = RatePlanForm(
            request.POST, rule=rule_for(channel, hotel), locked_channel=channel
        )
        form.is_valid()

        # Sans ce filtre, une ligne a peine commencee se couvrirait de "this field is required".
        filled = {name for name, value in request.POST.items() if value.strip()}
        return JsonResponse({"errors": {f: e for f, e in form.errors.items() if f in filled}})

    def save_formset(self, request, form, formset, change):
        channel = partner_channel(request.user)
        objects = formset.save(commit=False)
        for obj in objects:
            if channel:
                obj.channel = channel
            obj.save()
        # save(commit=False) laisse les suppressions et les m2m a la charge de l'appelant.
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "commission_rate"]


@admin.register(ChannelRule)
class ChannelRuleAdmin(admin.ModelAdmin):
    list_display = ["channel", "hotel", "floor_price", "max_discount_pct", "min_stay_nights"]
    list_filter = ["channel"]


@admin.register(ChannelPartner)
class ChannelPartnerAdmin(admin.ModelAdmin):
    list_display = ["user", "channel"]
