from pydantic import BaseModel
from datetime import datetime


class ScoreBreakdownItem(BaseModel):
    category: str
    score: float
    confidence: float | None = None


class ScoreResponse(BaseModel):
    id: int
    session_id: int
    message_id: int | None = None
    category: str
    score: float
    confidence: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionScoreSummaryResponse(BaseModel):
    session_id: int
    average_score: float | None = None
    breakdown: list[ScoreBreakdownItem]
    total_scores: int