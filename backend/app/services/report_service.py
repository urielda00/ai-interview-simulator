import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.message_repository import get_messages_by_session_id
from app.repositories.score_repository import get_scores_by_session_id
from app.repositories.report_repository import create_report, get_report_by_session_id
from app.repositories.session_repository import get_session_by_id, get_session_by_id_and_user_id
from app.services.ai_service import build_report_with_openai


logger = logging.getLogger(__name__)


def _average_by_category(scores):
    categories = {}
    for item in scores:
        categories.setdefault(item.category, []).append(item.score)

    return {
        category: round(sum(values) / len(values), 2)
        for category, values in categories.items()
    }


def _top_and_bottom_categories(category_averages: dict[str, float]) -> tuple[list[str], list[str]]:
    ordered = sorted(category_averages.items(), key=lambda x: x[1], reverse=True)
    top = [name for name, _ in ordered[:2]]
    bottom = [name for name, _ in ordered[-2:]] if ordered else []
    return top, bottom


def _format_category_summary(category_averages: dict[str, float]) -> str:
    return ", ".join(f"{category}: {score}" for category, score in category_averages.items())


def _build_fallback_report(language: str, avg_score: float, category_averages: dict[str, float]) -> tuple[str, str, str, str]:
    category_summary = _format_category_summary(category_averages)
    top_categories, bottom_categories = _top_and_bottom_categories(category_averages)

    if language == "he":
        top_text = ", ".join(top_categories) if top_categories else "לא זוהו עדיין"
        bottom_text = ", ".join(bottom_categories) if bottom_categories else "לא זוהו עדיין"

        if avg_score >= 8:
            summary = f"ביצוע חזק באופן כללי. פירוט קטגוריות - {category_summary}."
            strengths = f"התחומים החזקים יותר כרגע: {top_text}. יש תקשורת טכנית טובה ובסיס משכנע לראיון."
            weaknesses = f"התחומים שפחות חזקים כרגע: {bottom_text}. עדיין כדאי להעמיק יותר ב-tradeoffs, edge cases וריאליזם של production."
            study_plan = "המשך לתרגל שאלות המשך, החלטות scaling, ודוגמאות מהעולם האמיתי כדי להפוך תשובות חזקות למצוינות."
        elif avg_score >= 6:
            summary = f"ביצוע סביר עם מקום לשיפור. פירוט קטגוריות - {category_summary}."
            strengths = f"התחומים היחסית חזקים: {top_text}. יש בסיס ויכולת להסביר רעיונות טכניים."
            weaknesses = f"התחומים שדורשים יותר עבודה: {bottom_text}. התשובות צריכות יותר עומק, דוגמאות ומבנה ברור."
            study_plan = "תרגל תשובות במבנה קבוע: רעיון, דוגמה, tradeoff, complexity. התמקד קודם בתחומים החלשים יותר."
        else:
            summary = f"ביצוע התחלתי יחסית. פירוט קטגוריות - {category_summary}."
            strengths = f"התחומים שפחות חלשים יחסית כרגע: {top_text}. עדיין יש בסיס שאפשר לבנות עליו."
            weaknesses = f"התחומים החלשים כרגע: {bottom_text}. התשובות קצרות או שטחיות מדי ביחס לרמה שנדרשת בראיונות."
            study_plan = "חזור ליסודות, תרגל תשובות מלאות בקול, ונסה להסביר כל מושג עם דוגמה פשוטה לפני מעבר לנושאים מתקדמים."

        return summary, strengths, weaknesses, study_plan

    top_text = ", ".join(top_categories) if top_categories else "not detected yet"
    bottom_text = ", ".join(bottom_categories) if bottom_categories else "not detected yet"

    if avg_score >= 8:
        summary = f"Strong overall performance. Category breakdown - {category_summary}."
        strengths = f"Stronger areas right now: {top_text}. Communication and interview signal look solid."
        weaknesses = f"Weaker areas right now: {bottom_text}. You can still push harder on tradeoffs, edge cases, and production realism."
        study_plan = "Keep practicing follow-up questions, scaling decisions, and realistic examples to turn solid answers into standout answers."
    elif avg_score >= 6:
        summary = f"Decent performance with room to improve. Category breakdown - {category_summary}."
        strengths = f"Relatively stronger areas: {top_text}. There is a usable baseline and some ability to explain technical ideas."
        weaknesses = f"Areas that need more work: {bottom_text}. Answers need more depth, examples, and clearer structure."
        study_plan = "Practice a fixed answer pattern: concept, example, tradeoff, complexity. Start with the weaker categories first."
    else:
        summary = f"Early-stage performance. Category breakdown - {category_summary}."
        strengths = f"Less weak areas for now: {top_text}. There is still a foundation to build on."
        weaknesses = f"Weaker areas right now: {bottom_text}. Answers are too short or too shallow for strong interview performance."
        study_plan = "Review fundamentals, practice answering out loud, and explain each concept with a simple example before moving to advanced topics."

    return summary, strengths, weaknesses, study_plan


def build_session_report(db: Session, session_id: int):
    existing = get_report_by_session_id(db, session_id)
    if existing:
        return existing

    session = get_session_by_id(db, session_id)
    scores = get_scores_by_session_id(db, session_id)
    messages = get_messages_by_session_id(db, session_id)

    language = getattr(session, "language", "en") if session else "en"

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
            language=language,
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
        if language == "he":
            return create_report(
                db=db,
                session_id=session_id,
                summary="הראיון הושלם ללא נתוני ניקוד.",
                strengths="עדיין לא זוהו נקודות חוזק.",
                weaknesses="עדיין לא זוהו נקודות חולשה.",
                study_plan="מומלץ להשלים ראיון נוסף עם תשובות מלאות ומפורטות יותר.",
            )
        return create_report(
            db=db,
            session_id=session_id,
            summary="Interview completed with no score data.",
            strengths="No strengths detected yet.",
            weaknesses="No weaknesses detected yet.",
            study_plan="Complete another interview session with fuller answers.",
        )

    avg_score = sum(item.score for item in scores) / len(scores)
    category_averages = _average_by_category(scores)
    summary, strengths, weaknesses, study_plan = _build_fallback_report(
        language=language,
        avg_score=avg_score,
        category_averages=category_averages,
    )

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
        raise HTTPException(
            status_code=404,
            detail="Report not found" if getattr(session, "language", "en") == "en" else "הדוח לא נמצא",
        )

    return report