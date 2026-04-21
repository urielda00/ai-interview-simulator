from sqlalchemy.orm import Session

from app.repositories.report_repository import get_reports_by_session_ids
from app.repositories.score_repository import get_scores_by_session_ids, get_scores_by_session_id
from app.repositories.session_repository import get_session_by_id_and_user_id, get_sessions_by_user_id


def _get_category_averages(scores):
    grouped = {}
    for item in scores:
        grouped.setdefault(item.category, []).append(item.score)

    return {
        category: round(sum(values) / len(values), 2)
        for category, values in grouped.items()
    }


def _get_top_category(scores):
    averages = _get_category_averages(scores)
    if not averages:
        return None

    return max(averages.items(), key=lambda item: item[1])[0]


def _get_bottom_category(scores):
    averages = _get_category_averages(scores)
    if not averages:
        return None

    return min(averages.items(), key=lambda item: item[1])[0]


def get_user_history(db: Session, current_user_id: int):
    sessions = get_sessions_by_user_id(db, current_user_id)
    session_ids = [session.id for session in sessions]

    reports = get_reports_by_session_ids(db, session_ids)
    scores = get_scores_by_session_ids(db, session_ids)

    report_map = {report.session_id: report for report in reports}

    scores_by_session = {}
    for score in scores:
        scores_by_session.setdefault(score.session_id, []).append(score)

    completed_scores = []
    result = []

    for session in sessions:
        session_scores = scores_by_session.get(session.id, [])
        avg_score = None
        if session_scores:
            avg_score = round(sum(item.score for item in session_scores) / len(session_scores), 2)

        report = report_map.get(session.id)

        previous_average_score = completed_scores[-1] if completed_scores else None
        recent_trend = None
        if avg_score is not None and previous_average_score is not None:
            diff = round(avg_score - previous_average_score, 2)
            if diff >= 0.4:
                recent_trend = "improving"
            elif diff <= -0.4:
                recent_trend = "declining"
            else:
                recent_trend = "stable"

        if avg_score is not None:
            completed_scores.append(avg_score)

        result.append(
            {
                "id": session.id,
                "track": session.track,
                "level": session.level,
                "mode": session.mode,
                "status": session.status,
                "current_question_index": session.current_question_index,
                "created_at": session.created_at,
                "report_id": report.id if report else None,
                "report_summary": report.summary if report else None,
                "average_score": avg_score,
                "top_category": _get_top_category(session_scores),
                "bottom_category": _get_bottom_category(session_scores),
                "recent_trend": recent_trend,
            }
        )

    return result


def get_session_score_summary(db: Session, session_id: int, current_user_id: int):
    session = get_session_by_id_and_user_id(db, session_id, current_user_id)
    if not session:
        return None

    scores = get_scores_by_session_id(db, session_id)
    if not scores:
        return {
            "session_id": session_id,
            "average_score": None,
            "breakdown": [],
            "total_scores": 0,
            "top_category": None,
            "bottom_category": None,
        }

    grouped = {}
    confidence_grouped = {}

    for item in scores:
        grouped.setdefault(item.category, []).append(item.score)
        if item.confidence is not None:
            confidence_grouped.setdefault(item.category, []).append(item.confidence)

    breakdown = []
    for category, values in grouped.items():
        avg_confidence = None
        confidence_values = confidence_grouped.get(category, [])
        if confidence_values:
            avg_confidence = round(sum(confidence_values) / len(confidence_values), 2)

        breakdown.append(
            {
                "category": category,
                "score": round(sum(values) / len(values), 2),
                "confidence": avg_confidence,
            }
        )

    breakdown.sort(key=lambda item: item["score"], reverse=True)
    average_score = round(sum(item.score for item in scores) / len(scores), 2)

    return {
        "session_id": session_id,
        "average_score": average_score,
        "breakdown": breakdown,
        "total_scores": len(scores),
        "top_category": breakdown[0]["category"] if breakdown else None,
        "bottom_category": breakdown[-1]["category"] if breakdown else None,
    }