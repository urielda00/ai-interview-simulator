from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.interview import (
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewFinishResponse,
    InterviewTranscriptResponse,
)
from app.services.interview_service import (
    start_interview,
    answer_interview,
    finish_interview,
    get_session_transcript,
)

router = APIRouter()


@router.post("/start", response_model=InterviewStartResponse)
def start_interview_endpoint(
    request_data: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return start_interview(db, request_data.session_id, current_user.id)


@router.post("/answer", response_model=InterviewAnswerResponse)
def answer_interview_endpoint(
    request_data: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return answer_interview(db, request_data.session_id, request_data.answer, current_user.id)


@router.post("/finish/{session_id}", response_model=InterviewFinishResponse)
def finish_interview_endpoint(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return finish_interview(db, session_id, current_user.id)


@router.get("/transcript/{session_id}", response_model=InterviewTranscriptResponse)
def get_transcript_endpoint(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_session_transcript(db, session_id, current_user.id)