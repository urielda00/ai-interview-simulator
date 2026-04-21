from datetime import datetime

from pydantic import BaseModel


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
    top_category: str | None = None
    bottom_category: str | None = None
    recent_trend: str | None = None

    class Config:
        from_attributes = True