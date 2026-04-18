from pydantic import BaseModel
from datetime import datetime


class SessionCreate(BaseModel):
    track: str
    level: str
    mode: str
    language: str | None = None


class SessionResponse(BaseModel):
    id: int
    user_id: int
    track: str
    level: str
    mode: str
    status: str
    current_question_index: int
    created_at: datetime

    class Config:
        from_attributes = True