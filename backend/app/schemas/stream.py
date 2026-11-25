from pydantic import BaseModel, ConfigDict


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