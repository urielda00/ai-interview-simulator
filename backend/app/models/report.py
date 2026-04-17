from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, func
from app.core.database import Base

class Report(Base):
    __tablename__ = "session_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    study_plan = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())