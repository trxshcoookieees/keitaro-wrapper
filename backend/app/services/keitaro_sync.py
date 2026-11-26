import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Campaign, Stream, StreamOffer
from app.services.keitaro import KeitaroClient


async def _load_offers_by_id(client: KeitaroClient) -> dict[int, str]:
    offers_catalog = await client.get("/offers")

    return {
        offer["id"]: offer["name"]
        for offer in offers_catalog
    }


def _apply_campaign_fields(campaign: Campaign, data: dict) -> None:
    campaign.name = data["name"]
    campaign.is_active = data.get("state") == "active"


def _apply_stream_fields(stream: Stream, data: dict) -> None:
    stream.name = data["name"]
    stream.type = data["type"]
    stream.schema = data["schema"]
    stream.action_type = data["action_type"]
    stream.action_payload = data.get("action_payload")
    stream.filter_or = data.get("filter_or", False)
    stream.filters = data.get("filters", [])
    stream.is_active = data.get("state") == "active"


def _sync_stream_offers(
    db: Session,
    stream: Stream,
    offers_data: list[dict],
    offers_by_id: dict[int, str],
) -> None:
    existing_offers = {
        offer.offer_id: offer
        for offer in stream.offers
    }

    remote_offer_ids = set()

    for offer_data in offers_data:
        offer_id = offer_data["offer_id"]
        remote_offer_ids.add(offer_id)

        offer = existing_offers.get(offer_id)

        if offer is None:
            offer = StreamOffer(
                stream_id=stream.id,
                offer_id=offer_id,
            )
            db.add(offer)
            existing_offers[offer_id] = offer

        offer.offer_name = offers_by_id.get(
            offer_id,
            f"Offer {offer_id}",
        )
        offer.share = offer_data["share"]
        offer.is_active = offer_data.get("state") == "active"

    for offer in stream.offers:
        if offer.offer_id not in remote_offer_ids:
            offer.is_active = False
            offer.share = 0


async def _sync_streams(
    db: Session,
    campaign: Campaign,
    client: KeitaroClient,
    offers_by_id: dict[int, str],
) -> int:
    streams_data = await client.get(
        f"/campaigns/{campaign.keitaro_id}/streams"
    )

    remote_stream_ids = {
        stream_data["id"]
        for stream_data in streams_data
    }

    imported_streams = 0

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

        _apply_stream_fields(stream, stream_data)
        _sync_stream_offers(
            db,
            stream,
            stream_data.get("offers", []),
            offers_by_id,
        )

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

    return imported_streams


async def sync_campaign(db: Session, campaign: Campaign) -> None:
    if campaign.keitaro_id is None:
        return

    if campaign.is_dirty:
        return

    client = KeitaroClient()

    try:
        campaign_data = await client.get(
            f"/campaigns/{campaign.keitaro_id}"
        )
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            campaign.keitaro_id = None
            campaign.is_active = False

            for stream in campaign.streams:
                stream.keitaro_id = None

            db.commit()
            return

        raise

    _apply_campaign_fields(campaign, campaign_data)

    offers_by_id = await _load_offers_by_id(client)
    await _sync_streams(db, campaign, client, offers_by_id)

    db.commit()


async def sync_campaigns(db: Session):
    client = KeitaroClient()

    offers_by_id = await _load_offers_by_id(client)

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
                is_active=campaign_data.get("state") == "active",
            )
            db.add(campaign)
            db.flush()
        elif campaign.is_dirty:
            continue
        else:
            _apply_campaign_fields(campaign, campaign_data)

        imported_campaigns += 1

        imported_streams += await _sync_streams(
            db,
            campaign,
            client,
            offers_by_id,
        )

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
