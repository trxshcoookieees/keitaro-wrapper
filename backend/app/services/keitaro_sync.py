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

    remote_campaigns = []
    offset = 0
    limit = 100

    while True:
        campaigns = await client.get(
            "/campaigns",
            params={"offset": offset, "limit": limit},
        )

        remote_campaigns.extend(campaigns)

        if len(campaigns) < limit:
            break

        offset += limit

    remote_campaign_ids = {
        campaign["id"]
        for campaign in remote_campaigns
    }

    imported_campaigns = 0
    imported_streams = 0

    for campaign_data in remote_campaigns:
        campaign = db.scalar(
            select(Campaign).where(
                Campaign.keitaro_id == campaign_data["id"]
            )
        )

        if campaign is None:
            campaign = Campaign(
                keitaro_id=campaign_data["id"],
                name=campaign_data["name"],
                is_active=campaign_data["state"] == "active",
            )
            db.add(campaign)
            db.flush()
        elif campaign.is_dirty:
            continue
        else:
            campaign.name = campaign_data["name"]
            campaign.is_active = campaign_data["state"] == "active"

        imported_campaigns += 1

        streams_data = await client.get(
            f"/campaigns/{campaign_data['id']}/streams"
        )

        remote_stream_ids = {
            stream_data["id"]
            for stream_data in streams_data
        }

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

            remote_offer_ids = set()

            for offer_data in stream_data.get("offers", []):
                offer_id = offer_data["offer_id"]
                remote_offer_ids.add(offer_id)

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

            for offer in stream.offers:
                if offer.offer_id not in remote_offer_ids:
                    offer.is_active = False
                    offer.share = 0

            imported_streams += 1

        local_streams = db.scalars(
            select(Stream).where(
                Stream.campaign_id == campaign.id,
                Stream.keitaro_id.is_not(None),
                )
        ).all()

        for stream in local_streams:
            if stream.keitaro_id not in remote_stream_ids and not stream.is_dirty:
                stream.keitaro_id = None
                stream.is_active = False

    local_campaigns = db.scalars(
        select(Campaign).where(Campaign.keitaro_id.is_not(None))
    ).all()

    for campaign in local_campaigns:
        if campaign.keitaro_id not in remote_campaign_ids and not campaign.is_dirty:
            campaign.keitaro_id = None
            campaign.is_active = False

            for stream in campaign.streams:
                stream.keitaro_id = None

    db.commit()

    return {
        "campaigns": imported_campaigns,
        "streams": imported_streams,
    }