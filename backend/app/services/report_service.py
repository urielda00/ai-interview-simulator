import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.message_repository import get_messages_by_session_id
from app.repositories.score_repository import get_scores_by_session_id
from app.repositories.report_repository import create_report, get_report_by_session_id
from app.repositories.session_repository import get_session_by_id, get_session_by_id_and_user_id
from app.services.ai_service import build_report_with_openai


logger = logging.getLogger(__name__)


def build_session_report(db: Session, session_id: int):
    existing = get_report_by_session_id(db, session_id)
    if existing:
        return existing

    session = get_session_by_id(db, session_id)
    scores = get_scores_by_session_id(db, session_id)
    messages = get_messages_by_session_id(db, session_id)

    transcript_payload = [
        {
            "role": message.role,
            "content": message.content,
            "created_at": str(message.created_at),
        }
        for message in messages
    ]

    scores_payload = [
        {
            "category": score.category,
            "score": score.score,
            "confidence": score.confidence,
        }
        for score in scores
    ]

    if session:
        ai_report = build_report_with_openai(
            transcript=transcript_payload,
            scores=scores_payload,
            track=session.track,
            level=session.level,
            mode=session.mode,
        )
        if ai_report:
            logger.info("Session report built via AI. session_id=%s", session_id)
            return create_report(
                db=db,
                session_id=session_id,
                summary=ai_report["summary"],
                strengths=ai_report["strengths"],
                weaknesses=ai_report["weaknesses"],
                study_plan=ai_report["study_plan"],
            )

        logger.warning("AI report generation failed. Falling back to local report. session_id=%s", session_id)

    if not scores:
        return create_report(
            db=db,
            session_id=session_id,
            summary="Interview completed with no score data.",
            strengths="No strengths detected yet.",
            weaknesses="No weaknesses detected yet.",
            study_plan="Complete another interview session with fuller answers.",
        )

    avg_score = sum(item.score for item in scores) / len(scores)

    categories = {}
    for item in scores:
        categories.setdefault(item.category, []).append(item.score)

    category_summary = ", ".join(
        f"{category}: {round(sum(values) / len(values), 2)}"
        for category, values in categories.items()
    )

    if avg_score >= 8:
        summary = f"Strong overall performance. Category breakdown - {category_summary}."
        strengths = "Good depth, strong structure, and solid technical communication."
        weaknesses = "Can still push harder on tradeoffs and production realism."
        study_plan = "Practice advanced system tradeoffs, scaling decisions, and edge cases."
    elif avg_score >= 6:
        summary = f"Decent performance with room to improve. Category breakdown - {category_summary}."
        strengths = "Shows baseline understanding and can communicate technical ideas."
        weaknesses = "Answers need more depth, better examples, and clearer structure."
        study_plan = "Practice structured answering: concept, example, tradeoff, complexity."
    else:
        summary = f"Early-stage performance. Category breakdown - {category_summary}."
        strengths = "Engaged with the flow and provided basic responses."
        weaknesses = "Answers are too short or too shallow for strong scoring."
        study_plan = "Review fundamentals and practice speaking through full reasoning step by step."

    return create_report(
        db=db,
        session_id=session_id,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        study_plan=study_plan,
    )


def get_session_report(db: Session, session_id: int, current_user_id: int):
    session = get_session_by_id_and_user_id(db, session_id, current_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    report = get_report_by_session_id(db, session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report