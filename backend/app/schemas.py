from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "CHILDCARE", "PARK", "MEDICAL", "SAFETY", "AIR", "SCHOOL", "CULTURE"
]


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[ChatHistoryItem] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    extracted_profile: dict | None = None
    ready_to_recommend: bool = False

class NearbyChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=500,
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=5,
    )


class NearbyFacilityItem(BaseModel):
    id: str | None = None
    name: str
    type: str
    district: str
    address: str
    phone: str
    category: str
    latitude: float
    longitude: float
    distance_km: float


class NearbyLocation(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float


class NearbyChatResponse(BaseModel):
    reply: str
    location: NearbyLocation | None = None
    facility_type: str | None = None
    items: list[NearbyFacilityItem] = Field(
        default_factory=list
    )

class PriorityInput(BaseModel):
    category: Category
    weight: int = Field(ge=0, le=10)


class RecommendationRequest(BaseModel):
    child_age: int = Field(ge=0, le=7)
    priorities: list[PriorityInput]
    recommendation_count: int = Field(default=3, ge=2, le=3)


class CommunityCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=2000)
    district_name: str = Field(default="전체", max_length=20)
    password: str = Field(min_length=4, max_length=20)


class CommunityUpdateRequest(CommunityCreateRequest):
    pass


class CommunityDeleteRequest(BaseModel):
    password: str = Field(min_length=4, max_length=20)


class CommunityPost(BaseModel):
    id: int
    title: str
    content: str
    district_name: str
    author: str
    created_at: datetime
    view_count: int
