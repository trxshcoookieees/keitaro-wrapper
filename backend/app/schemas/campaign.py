from pydantic import BaseModel, Field

class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo_codes: list[str] = Field(min_length=1)