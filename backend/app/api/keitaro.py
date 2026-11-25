from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

import httpx

from app.database import get_db
from app.services.keitaro_sync import sync_campaigns
from app.services.keitaro import KeitaroClient

router = APIRouter(
    prefix="/keitaro",
    tags=["Keitaro"],
)

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