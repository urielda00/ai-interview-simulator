from pydantic import BaseModel
from datetime import datetime


class InterviewStartRequest(BaseModel):
    session_id: int


class InterviewStartResponse(BaseModel):
    session_id: int
    question: str
    status: str


class InterviewAnswerRequest(BaseModel):
    session_id: int
    answer: str


class InterviewAnswerResponse(BaseModel):
    session_id: int
    user_answer: str
    next_question: str
    status: str
    score: float


class InterviewFinishResponse(BaseModel):
    session_id: int
    status: str
    report_id: int


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewTranscriptResponse(BaseModel):
    session_id: int
    status: str
    messages: list[MessageResponse]