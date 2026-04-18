from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.core.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track = Column(String, nullable=False)
    level = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    language = Column(String, nullable=False, default="en", server_default="en")
    status = Column(String, nullable=False, default="created")
    current_question_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())