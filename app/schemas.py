
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserStats(BaseModel):
    id: UUID
    email: EmailStr
    total_requests: int
    successful_requests: int
    failed_requests: int
    last_request_at: datetime | None
    success_rate: float

class RequestBase(BaseModel):
    hit_value: int = Field(ge=0, le=6)

class RequestCreate(RequestBase):
    pass

class RequestOut(RequestBase):
    id: UUID
    user_id: UUID
    points: int
    is_successful: bool
    created_at: datetime

    class Config:
        from_attributes = True
