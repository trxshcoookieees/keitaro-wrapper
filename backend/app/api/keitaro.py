from fastapi import APIRouter, HTTPException

import httpx

from app.services.keitaro import KeitaroClient

router = APIRouter(
    prefix="/keitaro",
    tags=["Keitaro"],
)

@router.get("/offers")
async def get_offers():
    client = KeitaroClient()

    try:
        return await client.get("/offers")
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