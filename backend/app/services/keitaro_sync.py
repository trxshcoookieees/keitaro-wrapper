from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Campaign, Stream, StreamOffer
from app.services.keitaro import KeitaroClient


async def sync_campaigns(db: Session):
    client = KeitaroClient()

    offers_catalog = await client.get("/offers")
    offers_by_id = {
        offer["id"]: offer["name"]
        for offer in offers_catalog
    }

    offset = 0
    limit = 100
    imported_campaigns = 0
    imported_streams = 0

    while True:
        campaigns = await client.get(
            "/campaigns",
            params={"offset": offset, "limit": limit},
        )

        if not campaigns:
            break

        for campaign_data in campaigns:
            campaign = db.scalar(
                select(Campaign).where(
                    Campaign.keitaro_id == campaign_data["id"]
                )
            )

            if campaign is None:
                campaign = Campaign(
                    keitaro_id=campaign_data["id"],
                    name=campaign_data["name"],
                )
                db.add(campaign)
                db.flush()
            else:
                campaign.name = campaign_data["name"]

            imported_campaigns += 1

            streams_data = await client.get(
                f"/campaigns/{campaign_data['id']}/streams"
            )

            for stream_data in streams_data:
                stream = db.scalar(
                    select(Stream).where(
                        Stream.keitaro_id == stream_data["id"]
                    )
                )

                if stream is not None and stream.is_dirty:
                    continue

                if stream is None:
                    stream = Stream(
                        keitaro_id=stream_data["id"],
                        campaign_id=campaign.id,
                        name=stream_data["name"],
                    )
                    db.add(stream)
                    db.flush()

                stream.name = stream_data["name"]
                stream.type = stream_data["type"]
                stream.schema = stream_data["schema"]
                stream.action_type = stream_data["action_type"]
                stream.action_payload = stream_data.get("action_payload")
                stream.filter_or = stream_data.get("filter_or", False)
                stream.filters = stream_data.get("filters", [])
                stream.is_active = stream_data["state"] == "active"

                existing_offers = {
                    offer.offer_id: offer
                    for offer in stream.offers
                }

                for offer_data in stream_data.get("offers", []):
                    offer_id = offer_data["offer_id"]
                    offer = existing_offers.get(offer_id)

                    if offer is None:
                        offer = StreamOffer(
                            stream_id=stream.id,
                            offer_id=offer_id,
                            offer_name=offers_by_id.get(
                                offer_id,
                                f"Offer {offer_id}",
                            ),
                        )
                        db.add(offer)

                    offer.offer_name = offers_by_id.get(
                        offer_id,
                        f"Offer {offer_id}",
                    )
                    offer.share = offer_data["share"]
                    offer.is_active = offer_data["state"] == "active"

                imported_streams += 1

        db.commit()

        if len(campaigns) < limit:
            break

        offset += limit

    return {
        "campaigns": imported_campaigns,
        "streams": imported_streams,
    }