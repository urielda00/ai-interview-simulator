from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, func
from app.core.database import Base

class Score(Base):
    __tablename__ = "question_scores"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("session_messages.id"), nullable=True)
    category = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())