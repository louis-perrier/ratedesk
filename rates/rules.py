from decimal import Decimal

# Un contrat porte deux choses de nature differente. Les bornes sont opposables,
# le preavis d'annulation n'est qu'une valeur de depart que le partenaire peut changer.


def defaults(rule):
    return {
        "price": rule.floor_price,
        "min_stay_nights": rule.min_stay_nights,
        "cancellation_days": rule.default_cancellation_days,
    }


def violations(rule, rack_rate, *, price=None, min_stay_nights=None):
    found = {}

    if price is not None:
        if price < rule.floor_price:
            found.setdefault("price", []).append(
                f"Your contract sets a floor of {rule.floor_price} on this hotel."
            )
        elif rack_rate:
            off = (Decimal(rack_rate) - Decimal(price)) / Decimal(rack_rate) * 100
            if off > rule.max_discount_pct:
                found.setdefault("price", []).append(
                    f"That is {off:.0f}% off the rack rate of {rack_rate}. "
                    f"Your contract allows {rule.max_discount_pct}%."
                )

    if min_stay_nights is not None and min_stay_nights < rule.min_stay_nights:
        nights = "night" if rule.min_stay_nights == 1 else "nights"
        found.setdefault("min_stay_nights", []).append(
            f"{rule.channel} requires at least {rule.min_stay_nights} {nights} on this hotel."
        )

    return found
