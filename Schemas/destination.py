from pydantic import BaseModel, HttpUrl
from typing import Optional


class DestinationBase(BaseModel):
    name: str
    country: str
    countryCode: str
    category: str
    budget: str
    imageUrl: HttpUrl
    description: Optional[str] = None


class DestinationCreate(DestinationBase):
    user_id: Optional[int] = None   # allow guest entries too


class DestinationUpdate(DestinationBase):
    user_id: Optional[int] = None


class DestinationResponse(DestinationBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        orm_mode = True