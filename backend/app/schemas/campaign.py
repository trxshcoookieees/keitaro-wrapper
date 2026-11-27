from pydantic import BaseModel, Field, ConfigDict
from app.schemas.stream import StreamResponse


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo_codes: list[str] = Field(min_length=1)
    offer_ids: list[int] = Field(min_length=1)
    domain_id: int
    group_id: int
    traffic_source_id: int


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keitaro_id: int | None
    name: str
    domain_id: int | None
    group_id: int | None
    traffic_source_id: int | None
    is_active: bool
    is_dirty: bool
    streams: list[StreamResponse]


class CampaignCreateResponse(BaseModel):
    campaign: CampaignResponse
