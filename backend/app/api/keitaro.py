from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

import httpx

from app.database import get_db
from app.schemas.campaign import CampaignCreate, CampaignCreateResponse, CampaignResponse
from app.models import Campaign, Stream, StreamOffer
from app.services.keitaro_sync import (
    cancel_stream,
    push_stream,
    restore_campaign,
    sync_campaign,
    sync_campaigns,
)
from app.services.keitaro import KeitaroClient
from app.services.stream_offers import rebalance_offers

router = APIRouter(
    prefix="/keitaro",
    tags=["Keitaro"],
)


def _get_campaign_with_streams(
        db: Session,
        campaign_id: int,
) -> Campaign | None:
    return db.scalar(
        select(Campaign)
        .where(Campaign.id == campaign_id)
        .options(
            selectinload(Campaign.streams).selectinload(Stream.offers)
        )
    )


async def _keitaro_get(
        endpoint: str,
        params: dict | None = None,
):
    client = KeitaroClient()

    try:
        return await client.get(endpoint, params=params)
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API",
        )


@router.get("/domains")
async def get_domains():
    return await _keitaro_get("/domains")


@router.get("/groups")
async def get_groups(type: str = Query(default="campaigns")):
    return await _keitaro_get(
        "/groups",
        params={"type": type},
    )


@router.get("/traffic-sources")
async def get_traffic_sources():
    return await _keitaro_get("/traffic_sources")


@router.get("/offers")
async def get_offers(search: str | None = Query(default=None)):
    client = KeitaroClient()

    try:
        offers = await client.get("/offers")

        if search:
            search_lower = search.lower()

            offers = [
                offer
                for offer in offers
                    if search_lower in offer["name"].lower()
                    or search_lower in str(offer["id"])
            ]

        return offers

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}"
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API"
        )

@router.get("/campaigns")
async def get_campaigns(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=500),
):
    client = KeitaroClient()

    try:
        return await client.get(
            "/campaigns",
            params={"offset": offset, "limit": limit}
        )
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API"
        )

@router.get("/campaigns/{campaign_id}/streams")
async def get_campaign_streams(campaign_id: int):
    client = KeitaroClient()

    try:
        return await client.get(f"/campaigns/{campaign_id}/streams")
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API"
        )


@router.post("/sync")
async def sync_keitaro_data(db: Session = Depends(get_db)):
    try:
        return await sync_campaigns(db)
    except httpx.HTTPStatusError as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API",
        )
    except Exception:
        db.rollback()
        raise

@router.post(
    "/local/campaigns/{campaign_id}/sync",
    response_model=CampaignResponse,
)
async def sync_local_campaign(
        campaign_id: int,
        db: Session = Depends(get_db),
):
    campaign = db.get(Campaign, campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    if campaign.keitaro_id is None:
        raise HTTPException(
            status_code=409,
            detail="Campaign is not synchronized with Keitaro",
        )

    try:
        await sync_campaign(db, campaign, force=True)
    except httpx.HTTPStatusError as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API",
        )
    except Exception:
        db.rollback()
        raise

    return _get_campaign_with_streams(db, campaign_id)


@router.post(
    "/local/campaigns/{campaign_id}/restore",
    response_model=CampaignResponse,
)
async def restore_local_campaign(
        campaign_id: int,
        db: Session = Depends(get_db),
):
    campaign = _get_campaign_with_streams(db, campaign_id)

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found",
        )

    try:
        await restore_campaign(db, campaign)
    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )
    except httpx.HTTPStatusError as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API",
        )
    except Exception:
        db.rollback()
        raise

    return _get_campaign_with_streams(db, campaign_id)


@router.post(
    "/local/streams/{stream_id}/push",
    response_model=CampaignResponse,
)
async def push_local_stream(
        stream_id: int,
        db: Session = Depends(get_db),
):
    stream = db.get(Stream, stream_id)

    if stream is None:
        raise HTTPException(
            status_code=404,
            detail="Stream not found",
        )

    try:
        await push_stream(db, stream)
    except ValueError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Stream is not synchronized with Keitaro",
        )
    except httpx.HTTPStatusError as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API",
        )
    except Exception:
        db.rollback()
        raise

    return _get_campaign_with_streams(db, stream.campaign_id)


@router.post(
    "/local/streams/{stream_id}/cancel",
    response_model=CampaignResponse,
)
async def cancel_local_stream(
        stream_id: int,
        db: Session = Depends(get_db),
):
    stream = db.get(Stream, stream_id)

    if stream is None:
        raise HTTPException(
            status_code=404,
            detail="Stream not found",
        )

    try:
        await cancel_stream(db, stream)
    except ValueError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Stream is not synchronized with Keitaro",
        )
    except httpx.HTTPStatusError as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API",
        )
    except Exception:
        db.rollback()
        raise

    return _get_campaign_with_streams(db, stream.campaign_id)


@router.post(
    "/local/streams/{stream_id}/offers/{offer_id}/restore",
    response_model=CampaignResponse,
)
def restore_stream_offer(
        stream_id: int,
        offer_id: int,
        db: Session = Depends(get_db),
):
    stream = db.get(Stream, stream_id)

    if stream is None:
        raise HTTPException(
            status_code=404,
            detail="Stream not found",
        )

    offer = db.scalar(
        select(StreamOffer).where(
            StreamOffer.stream_id == stream_id,
            StreamOffer.offer_id == offer_id,
        )
    )

    if offer is None:
        raise HTTPException(
            status_code=404,
            detail="Offer not found in stream",
        )

    if offer.is_active:
        raise HTTPException(
            status_code=409,
            detail="Offer is already active",
        )

    offer.is_active = True

    rebalance_offers(stream.offers)

    stream.is_dirty = True

    db.commit()

    return _get_campaign_with_streams(db, stream.campaign_id)


@router.post(
    "/local/streams/{stream_id}/offers/{offer_id}/delete",
    response_model=CampaignResponse,
)
def delete_stream_offer(
        stream_id: int,
        offer_id: int,
        db: Session = Depends(get_db),
):
    stream = db.get(Stream, stream_id)

    if stream is None:
        raise HTTPException(
            status_code=404,
            detail="Stream not found",
        )

    offer = db.scalar(
        select(StreamOffer).where(
            StreamOffer.stream_id == stream_id,
            StreamOffer.offer_id == offer_id,
        )
    )

    if offer is None:
        raise HTTPException(
            status_code=404,
            detail="Offer not found in stream",
        )

    if not offer.is_active:
        raise HTTPException(
            status_code=409,
            detail="Offer is already deleted",
        )

    offer.is_active = False
    offer.share = 0

    rebalance_offers(stream.offers)

    stream.is_dirty = True

    db.commit()

    return _get_campaign_with_streams(db, stream.campaign_id)


@router.post("/campaigns", response_model=CampaignCreateResponse)
async def create_campaign(
        data: CampaignCreate,
        db: Session = Depends(get_db)
):
    client = KeitaroClient()

    try:
        keitaro_campaign = await client.post(
            "/campaigns",
            data={
                "name": data.name,
                "domain_id": data.domain_id,
                "group_id": str(data.group_id),
                "traffic_source_id": data.traffic_source_id,
            },
        )

        campaign = Campaign(
            keitaro_id=keitaro_campaign["id"],
            name=keitaro_campaign["name"],
            domain_id=data.domain_id,
            group_id=data.group_id,
            traffic_source_id=data.traffic_source_id,
        )

        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        geo_stream = await client.post(
            "/streams",
            data={
                "campaign_id": campaign.keitaro_id,
                "name": "GEO",
                "type": "regular",
                "schema": "redirect",
                "action_type": "http",
                "action_payload": "https://google.com",
                "filters": [
                    {
                        "name": "country",
                        "mode": "accept",
                        "payload": data.geo_codes,
                    }
                ],
            },
        )

        geo_stream_record = Stream(
            keitaro_id=geo_stream["id"],
            campaign_id=campaign.id,
            name=geo_stream["name"],
            type=geo_stream["type"],
            schema=geo_stream["schema"],
            action_type=geo_stream["action_type"],
            action_payload=geo_stream.get("action_payload"),
            filters=geo_stream.get("filters", []),
            is_active=True,
        )

        db.add(geo_stream_record)
        db.commit()

        offer_count = len(data.offer_ids)
        base_share, remainder = divmod(100, offer_count)

        offers = [
            {
                "offer_id": offer_id,
                "share": base_share + (1 if index < remainder else 0),
                "state": "active",
            }
            for index, offer_id in enumerate(data.offer_ids)
        ]

        offers_stream = await client.post(
            "/streams",
            data={
                "campaign_id": campaign.keitaro_id,
                "name": "Offers",
                "type": "default",
                "schema": "landings",
                "action_type": "http",
                "offers": offers,
            },
        )

        offers_stream_record = Stream(
            keitaro_id=offers_stream["id"],
            campaign_id=campaign.id,
            name=offers_stream["name"],
            type=offers_stream["type"],
            schema=offers_stream["schema"],
            action_type=offers_stream["action_type"],
            action_payload=offers_stream.get("action_payload"),
            is_active=True,
        )

        db.add(offers_stream_record)
        db.flush()

        keitaro_offers = await client.get("/offers")
        offer_names = {
            offer["id"]: offer["name"]
            for offer in keitaro_offers
        }

        for offer_data in offers:
            db.add(
                StreamOffer(
                    stream_id=offers_stream_record.id,
                    offer_id=offer_data["offer_id"],
                    offer_name=offer_names.get(
                        offer_data["offer_id"],
                        f"Offer {offer_data['offer_id']}",
                    ),
                    share=offer_data["share"],
                    is_active=True,
                )
            )

        db.commit()
        db.refresh(campaign)

        return {"campaign": campaign}

    except httpx.HTTPStatusError as error:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"Keitaro API returned status {error.response.status_code}",
        )
    except httpx.RequestError:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Keitaro API"
        )


@router.get("/local/campaigns", response_model=list[CampaignResponse])
def get_local_campaigns(db: Session = Depends(get_db)):
    campaigns = db.scalars(
        select(Campaign).options(
            selectinload(Campaign.streams).selectinload(Stream.offers)
        )
    ).all()

    return campaigns