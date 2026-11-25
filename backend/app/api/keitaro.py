from fastapi import APIRouter, Query, HTTPException

import httpx

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