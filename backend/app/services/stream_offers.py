from app.models import StreamOffer


def rebalance_offers(offers: list[StreamOffer]) -> None:
    active_offers = sorted(
        (offer for offer in offers if offer.is_active),
        key=lambda offer: offer.id or 0,
    )

    if len(active_offers) == 1:
        active_offers[0].share = 100
        return

    pinned_offers = [
        offer for offer in active_offers
        if offer.is_pinned
    ]

    unpinned_offers = [
        offer for offer in active_offers
        if not offer.is_pinned
    ]

    pinned_share = sum(offer.share for offer in pinned_offers)

    if pinned_share > 100:
        raise ValueError(
            "Total share of pinned offers exceeds 100%"
        )

    remaining_share = 100 - pinned_share

    if not unpinned_offers:
        if remaining_share != 0:
            raise ValueError(
                "All offers are pinned, but their total share is less than 100%"
            )
        return

    base_share, remainder = divmod(
        remaining_share,
        len(unpinned_offers),
    )

    for index, offer in enumerate(unpinned_offers):
        offer.share = base_share + (1 if index < remainder else 0)

    for offer in offers:
        if not offer.is_active:
            offer.share = 0