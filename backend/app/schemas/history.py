from pydantic import BaseModel
from datetime import datetime


class SessionHistoryItem(BaseModel):
    id: int
    track: str
    level: str
    mode: str
    status: str
    current_question_index: int
    created_at: datetime
    report_id: int | None = None
    report_summary: str | None = None
    average_score: float | None = None

    class Config:
        from_attributes = True