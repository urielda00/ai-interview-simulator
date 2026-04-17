from pydantic import BaseModel
from datetime import datetime


class SessionCreate(BaseModel):
    user_id: int
    track: str
    level: str
    mode: str


class SessionResponse(BaseModel):
    id: int
    user_id: int
    track: str
    level: str
    mode: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True