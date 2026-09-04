from django.db import migrations

MANAGER = "revenue_manager"
PARTNER = "channel_partner"

# Le partenaire garde change_hotel parce que sans elle l'admin refuse le POST
# du formset, alors que les champs de l'hotel lui restent en lecture seule.
PARTNER_PERMS = [
    "view_hotel",
    "change_hotel",
    "view_channel",
    "view_channelrule",
    "add_rateplan",
    "change_rateplan",
    "delete_rateplan",
    "view_rateplan",
]


def create_groups(apps, schema_editor):
    from django.apps import apps as installed
    from django.contrib.auth.management import create_permissions

    create_permissions(installed.get_app_config("rates"), verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    rates = Permission.objects.filter(content_type__app_label="rates")

    manager, _ = Group.objects.get_or_create(name=MANAGER)
    manager.permissions.set(rates)

    partner, _ = Group.objects.get_or_create(name=PARTNER)
    partner.permissions.set(rates.filter(codename__in=PARTNER_PERMS))


def drop_groups(apps, schema_editor):
    apps.get_model("auth", "Group").objects.filter(name__in=[MANAGER, PARTNER]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("rates", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(create_groups, drop_groups)]
