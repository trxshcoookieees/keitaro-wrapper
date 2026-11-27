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

    if "domain_id" in data:
        campaign.domain_id = data["domain_id"]

    if "group_id" in data:
        campaign.group_id = data["group_id"]

    if "traffic_source_id" in data:
        campaign.traffic_source_id = data["traffic_source_id"]


def _mark_campaign_deleted(campaign: Campaign) -> None:
    campaign.keitaro_id = None
    campaign.is_active = False
    campaign.is_dirty = False

    for stream in campaign.streams:
        stream.keitaro_id = None
        stream.is_active = False
        stream.is_dirty = False


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
    force: bool = False,
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

        if stream is not None and stream.is_dirty and not force:
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
        stream.is_dirty = False
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
        if (
            stream.keitaro_id not in remote_stream_ids
            and (force or not stream.is_dirty)
        ):
            stream.keitaro_id = None
            stream.is_active = False
            stream.is_dirty = False

    return imported_streams


async def sync_campaign(
    db: Session,
    campaign: Campaign,
    force: bool = False,
) -> None:
    if campaign.keitaro_id is None:
        return

    if campaign.is_dirty and not force:
        return

    client = KeitaroClient()

    try:
        campaign_data = await client.get(
            f"/campaigns/{campaign.keitaro_id}"
        )
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            _mark_campaign_deleted(campaign)

            db.commit()
            return

        raise

    _apply_campaign_fields(campaign, campaign_data)
    campaign.is_dirty = False

    offers_by_id = await _load_offers_by_id(client)
    await _sync_streams(db, campaign, client, offers_by_id, force=force)

    db.commit()


def _serialize_stream(stream: Stream) -> dict:
    return {
        "name": stream.name,
        "type": stream.type,
        "schema": stream.schema,
        "action_type": stream.action_type,
        "action_payload": stream.action_payload,
        "filter_or": stream.filter_or,
        "filters": stream.filters or [],
        "offers": [
            {
                "offer_id": offer.offer_id,
                "share": offer.share,
                "state": "active",
            }
            for offer in stream.offers
            if offer.is_active
        ],
    }


async def push_stream(db: Session, stream: Stream) -> None:
    if stream.keitaro_id is None:
        raise ValueError("Stream is not synchronized with Keitaro")

    client = KeitaroClient()

    await client.put(
        f"/streams/{stream.keitaro_id}",
        _serialize_stream(stream),
    )

    stream_data = await client.get(f"/streams/{stream.keitaro_id}")
    offers_by_id = await _load_offers_by_id(client)

    _apply_stream_fields(stream, stream_data)
    _sync_stream_offers(
        db,
        stream,
        stream_data.get("offers", []),
        offers_by_id,
    )

    stream.is_dirty = False
    db.commit()


async def cancel_stream(db: Session, stream: Stream) -> None:
    if stream.keitaro_id is None:
        raise ValueError("Stream is not synchronized with Keitaro")

    client = KeitaroClient()

    stream_data = await client.get(f"/streams/{stream.keitaro_id}")
    offers_by_id = await _load_offers_by_id(client)

    _apply_stream_fields(stream, stream_data)
    _sync_stream_offers(
        db,
        stream,
        stream_data.get("offers", []),
        offers_by_id,
    )

    stream.is_dirty = False
    db.commit()


def _serialize_stream_for_create(
    stream: Stream,
    campaign_keitaro_id: int,
) -> dict:
    payload = {
        "campaign_id": campaign_keitaro_id,
        "name": stream.name,
        "type": stream.type,
        "schema": stream.schema,
        "action_type": stream.action_type,
        "filter_or": stream.filter_or,
        "filters": stream.filters or [],
    }

    if stream.action_payload:
        payload["action_payload"] = stream.action_payload

    if stream.schema == "landings":
        payload["offers"] = [
            {
                "offer_id": offer.offer_id,
                "share": offer.share,
                "state": "active",
            }
            for offer in stream.offers
            if offer.is_active
        ]

    return payload


async def restore_campaign(db: Session, campaign: Campaign) -> None:
    if campaign.keitaro_id is not None:
        raise ValueError("Campaign is already synchronized with Keitaro")

    if (
        campaign.domain_id is None
        or campaign.group_id is None
        or campaign.traffic_source_id is None
    ):
        raise ValueError(
            "Campaign has no saved domain, group or traffic source"
        )

    client = KeitaroClient()

    offers_catalog = await client.get("/offers")
    offers_by_id = {
        offer["id"]: offer["name"]
        for offer in offers_catalog
    }

    missing_offer_ids = sorted({
        offer.offer_id
        for stream in campaign.streams
        for offer in stream.offers
        if offer.is_active and offer.offer_id not in offers_by_id
    })

    if missing_offer_ids:
        raise ValueError(
            "Offers are missing in Keitaro: "
            + ", ".join(str(offer_id) for offer_id in missing_offer_ids)
        )

    domains = await client.get("/domains")

    if not any(
        domain["id"] == campaign.domain_id
        for domain in domains
    ):
        raise ValueError("Saved domain is missing in Keitaro")

    groups = await client.get(
        "/groups",
        params={"type": "campaigns"},
    )

    if not any(
        group["id"] == campaign.group_id
        for group in groups
    ):
        raise ValueError("Saved group is missing in Keitaro")

    sources = await client.get("/traffic_sources")

    if not any(
        source["id"] == campaign.traffic_source_id
        for source in sources
    ):
        raise ValueError("Saved traffic source is missing in Keitaro")

    for stream in campaign.streams:
        if stream.schema == "landings" and not any(
            offer.is_active for offer in stream.offers
        ):
            raise ValueError(
                f"Stream '{stream.name}' has no active offers to restore"
            )

    created_campaign = await client.post(
        "/campaigns",
        data={
            "name": campaign.name,
            "domain_id": campaign.domain_id,
            "group_id": str(campaign.group_id),
            "traffic_source_id": campaign.traffic_source_id,
        },
    )

    try:
        campaign.keitaro_id = created_campaign["id"]

        for stream in sorted(
            campaign.streams,
            key=lambda item: item.id,
        ):
            created_stream = await client.post(
                "/streams",
                data=_serialize_stream_for_create(
                    stream,
                    created_campaign["id"],
                ),
            )

            stream.keitaro_id = created_stream["id"]
            _apply_stream_fields(stream, created_stream)
            stream.is_active = True
            _sync_stream_offers(
                db,
                stream,
                created_stream.get("offers", []),
                offers_by_id,
            )
            stream.is_dirty = False

        _apply_campaign_fields(campaign, created_campaign)
        campaign.is_active = True
        campaign.is_dirty = False

        db.commit()
    except Exception:
        db.rollback()

        try:
            await client.delete(
                f"/campaigns/{created_campaign['id']}"
            )
        except Exception:
            pass

        raise


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
                domain_id=campaign_data.get("domain_id"),
                group_id=campaign_data.get("group_id"),
                traffic_source_id=campaign_data.get("traffic_source_id"),
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
        if campaign.keitaro_id not in remote_campaign_ids:
            _mark_campaign_deleted(campaign)

    unsynchronized_campaigns = db.scalars(
        select(Campaign).where(Campaign.keitaro_id.is_(None))
    ).all()

    for campaign in unsynchronized_campaigns:
        _mark_campaign_deleted(campaign)

    db.commit()

    return {
        "campaigns": imported_campaigns,
        "streams": imported_streams,
    }
