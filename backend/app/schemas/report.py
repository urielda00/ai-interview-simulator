from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: int
    session_id: int
    summary: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    study_plan: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True