from .models import ChannelRule

MANAGER_GROUP = "revenue_manager"
PARTNER_GROUP = "channel_partner"


def partner_channel(user):
    partner = getattr(user, "channel_partner", None)
    return partner.channel if partner else None


def rule_for(channel, hotel):
    if channel is None or hotel is None:
        return None
    return (
        ChannelRule.objects.select_related("channel", "hotel")
        .filter(channel=channel, hotel=hotel)
        .first()
    )
