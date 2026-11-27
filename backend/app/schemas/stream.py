from pydantic import BaseModel, ConfigDict, Field


class StreamOffersAdd(BaseModel):
    offer_ids: list[int] = Field(min_length=1)


class StreamOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int
    offer_name: str
    share: int
    is_active: bool
    is_pinned: bool


class StreamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keitaro_id: int | None
    campaign_id: int
    name: str
    type: str
    schema: str
    action_type: str
    action_payload: str | None
    is_active: bool
    is_dirty: bool
    offers: list[StreamOfferResponse]