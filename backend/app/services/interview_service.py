import logging
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.interview_session import InterviewSession
from app.repositories.message_repository import create_message, get_messages_by_session_id
from app.repositories.score_repository import create_score, get_scores_by_session_id
from app.repositories.session_repository import get_session_by_id_and_user_id
from app.repositories.upload_repository import get_files_by_session_id
from app.services.ai_service import generate_followup_with_openai
from app.services.report_service import build_session_report
from app.services.scoring_service import score_answer


logger = logging.getLogger(__name__)


QUESTION_BANK = {
    "en": {
        "backend": [
            "Explain the difference between authentication and authorization.",
            "How does JWT-based authentication work in a backend system?",
            "How would you protect sensitive API endpoints?",
            "What are common security mistakes in backend APIs?",
            "What is the difference between stateless and stateful authentication?",
        ],
        "default": [
            "Tell me about a technical project you built.",
            "What was the hardest engineering problem you faced there?",
            "How did you debug and solve it?",
            "What would you improve if you rebuilt it today?",
        ],
    },
    "he": {
        "backend": [
            "הסבר את ההבדל בין authentication לבין authorization.",
            "איך JWT-based authentication עובד במערכת backend?",
            "איך היית מגן על API endpoints רגישים?",
            "מהן טעויות אבטחה נפוצות ב-backend APIs?",
            "מה ההבדל בין stateless authentication לבין stateful authentication?",
        ],
        "default": [
            "ספר על פרויקט טכני שבנית.",
            "מה הייתה הבעיה ההנדסית הכי קשה שהתמודדת איתה שם?",
            "איך דיבגת ופתרת אותה?",
            "מה היית משפר אם היית בונה את המערכת מחדש היום?",
        ],
    },
}

LEETCODE_BANK = {
    "en": {
        "junior": [
            {
                "title": "Two Sum",
                "prompt": "LeetCode-style question: Two Sum. Given an array of integers and a target, return the indices of the two numbers such that they add up to the target. Explain your approach, time complexity, and optionally provide code.",
            },
            {
                "title": "Valid Parentheses",
                "prompt": "LeetCode-style question: Valid Parentheses. Given a string containing just the characters ()[]{} determine if the input string is valid. Explain your approach, time complexity, and optionally provide code.",
            },
            {
                "title": "Best Time to Buy and Sell Stock",
                "prompt": "LeetCode-style question: Best Time to Buy and Sell Stock. Given an array where the ith element is the price of a stock on day i, find the maximum profit from one transaction. Explain your approach, time complexity, and optionally provide code.",
            },
        ],
        "mid": [
            {
                "title": "Group Anagrams",
                "prompt": "LeetCode-style question: Group Anagrams. Given an array of strings, group the anagrams together. Explain your approach, time complexity, and optionally provide code.",
            },
            {
                "title": "Top K Frequent Elements",
                "prompt": "LeetCode-style question: Top K Frequent Elements. Given an integer array and an integer k, return the k most frequent elements. Explain your approach, time complexity, and optionally provide code.",
            },
        ],
        "senior": [
            {
                "title": "LRU Cache",
                "prompt": "LeetCode-style question: LRU Cache. Design a data structure that follows the constraints of an LRU cache. Explain your design, tradeoffs, complexity, and optionally provide code.",
            }
        ],
    },
    "he": {
        "junior": [
            {
                "title": "Two Sum",
                "prompt": "שאלת LeetCode: Two Sum. נתון מערך של מספרים שלמים ו-target. החזר את האינדקסים של שני המספרים שסכומם שווה ל-target. הסבר את הגישה שלך, time complexity, ואם תרצה גם קוד.",
            },
            {
                "title": "Valid Parentheses",
                "prompt": "שאלת LeetCode: Valid Parentheses. נתונה מחרוזת שמכילה רק את התווים ()[]{} וקבע אם היא תקינה. הסבר את הגישה שלך, time complexity, ואם תרצה גם קוד.",
            },
            {
                "title": "Best Time to Buy and Sell Stock",
                "prompt": "שאלת LeetCode: Best Time to Buy and Sell Stock. נתון מערך שבו כל איבר מייצג מחיר מניה ביום מסוים, ומטרתך למצוא את הרווח המקסימלי מעסקה אחת. הסבר את הגישה שלך, time complexity, ואם תרצה גם קוד.",
            },
        ],
        "mid": [
            {
                "title": "Group Anagrams",
                "prompt": "שאלת LeetCode: Group Anagrams. נתון מערך של מחרוזות, ויש לקבץ יחד את כל ה-anagrams. הסבר את הגישה שלך, time complexity, ואם תרצה גם קוד.",
            },
            {
                "title": "Top K Frequent Elements",
                "prompt": "שאלת LeetCode: Top K Frequent Elements. נתון מערך של מספרים שלמים ומספר k, ויש להחזיר את k האיברים השכיחים ביותר. הסבר את הגישה שלך, time complexity, ואם תרצה גם קוד.",
            },
        ],
        "senior": [
            {
                "title": "LRU Cache",
                "prompt": "שאלת LeetCode: LRU Cache. תכנן data structure שעומד בדרישות של LRU cache. הסבר את התכנון שלך, tradeoffs, complexity, ואם תרצה גם קוד.",
            }
        ],
    },
}


def _get_owned_session(db: Session, session_id: int, current_user_id: int):
    session = get_session_by_id_and_user_id(db, session_id, current_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _lang(session: InterviewSession) -> str:
    return session.language if getattr(session, "language", None) in {"en", "he"} else "en"


def _category_label(category: str, language: str) -> str:
    if language == "he":
        mapping = {
            "clarity": "בהירות",
            "technical_accuracy": "דיוק טכני",
            "depth": "עומק",
            "tradeoff_reasoning": "חשיבת tradeoffs",
            "correctness": "נכונות",
            "complexity_analysis": "ניתוח סיבוכיות",
            "data_structures": "מבני נתונים",
            "communication": "תקשורת",
            "architecture_reasoning": "חשיבה ארכיטקטונית",
            "maintainability": "תחזוקתיות",
        }
        return mapping.get(category, category)

    mapping = {
        "clarity": "clarity",
        "technical_accuracy": "technical accuracy",
        "depth": "depth",
        "tradeoff_reasoning": "tradeoff reasoning",
        "correctness": "correctness",
        "complexity_analysis": "complexity analysis",
        "data_structures": "data structures",
        "communication": "communication",
        "architecture_reasoning": "architecture reasoning",
        "maintainability": "maintainability",
    }
    return mapping.get(category, category)


def _split_feedback_text(text: str) -> list[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    raw_parts = []
    for chunk in cleaned.replace("•", ".").replace("\n", ".").split("."):
        part = chunk.strip(" -\t")
        if part:
            raw_parts.append(part)

    return raw_parts[:3]


def _friendly_summary(score: float, language: str) -> tuple[str, str]:
    if language == "he":
        if score >= 8.5:
            return "excellent", "יש פה תשובה שבאמת נשמעת חזקה ובטוחה."
        if score >= 7:
            return "strong", "יש פה כיוון טוב, וזה כבר מרגיש די משכנע."
        if score >= 5.5:
            return "developing", "יש בסיס טוב, אבל עדיין חסר קצת עומק או חדות."
        return "needs-work", "יש כאן התחלה, אבל כרגע זה עוד לא נשמע מספיק חזק לראיון."

    if score >= 8.5:
        return "excellent", "This already sounds strong, clear, and interview-ready."
    if score >= 7:
        return "strong", "There is a solid direction here, and it already feels fairly convincing."
    if score >= 5.5:
        return "developing", "There is a good base here, but it still needs more depth or sharpness."
    return "needs-work", "There is a starting point here, but it does not sound strong enough yet for an interview."


def _default_worked_points(top_categories: list[str], language: str) -> list[str]:
    if language == "he":
        if not top_categories:
            return ["יש פה בכל זאת בסיס שאפשר לבנות עליו."]
        return [f"יחסית היה לך צד חזק יותר ב-{label}." for label in top_categories[:2]]

    if not top_categories:
        return ["There is still a baseline here that you can build on."]
    return [f"You came across relatively stronger on {label}." for label in top_categories[:2]]


def _default_improve_points(bottom_categories: list[str], language: str) -> list[str]:
    if language == "he":
        if not bottom_categories:
            return ["הייתי מחזק עוד קצת את הדיוק והעומק."]
        return [f"כדאי לחזק עוד את {label} בתשובה הבאה." for label in bottom_categories[:2]]

    if not bottom_categories:
        return ["I would tighten the depth and precision a bit more."]
    return [f"I would strengthen {label} a bit more in the next answer." for label in bottom_categories[:2]]


def _build_answer_review(
    message_id: int,
    breakdown: list[dict],
    language: str,
    strengths_text: str = "",
    weaknesses_text: str = "",
    reason_text: str = "",
) -> dict:
    ordered = sorted(breakdown, key=lambda item: item["score"], reverse=True)
    average_score = round(sum(item["score"] for item in breakdown) / len(breakdown), 2) if breakdown else 0.0
    tone, base_summary = _friendly_summary(average_score, language)

    top_categories = [_category_label(item["category"], language) for item in ordered[:2]]
    bottom_categories = [_category_label(item["category"], language) for item in ordered[-2:]]

    worked_points = _split_feedback_text(strengths_text) or _default_worked_points(top_categories, language)
    improve_points = _split_feedback_text(weaknesses_text) or _default_improve_points(bottom_categories, language)

    if language == "he":
        if reason_text.strip():
            summary = f"{base_summary} {reason_text.strip()}"
        else:
            summary = base_summary

        encouragement_map = {
            "excellent": "תמשיך בדיוק בכיוון הזה - זה כבר נשמע בשל מאוד.",
            "strong": "עוד קצת עומק ודוגמאות, וזה יכול להישמע ממש חזק.",
            "developing": "יש על מה לבנות, ועכשיו צריך להפוך את זה ליותר חד ומשכנע.",
            "needs-work": "זה בסדר - עדיף לזהות את הפער עכשיו ולחדד אותו בסשנים הבאים.",
        }
    else:
        if reason_text.strip():
            summary = f"{base_summary} {reason_text.strip()}"
        else:
            summary = base_summary

        encouragement_map = {
            "excellent": "Keep going in this direction - it already sounds mature and convincing.",
            "strong": "A bit more depth and a sharper example could make this genuinely strong.",
            "developing": "There is something to build on here, and the next step is making it tighter and more convincing.",
            "needs-work": "That is okay - better to catch the gap here and sharpen it in the next rounds.",
        }

    return {
        "message_id": message_id,
        "overall_score": average_score,
        "tone": tone,
        "summary": summary.strip(),
        "what_worked": worked_points[:3],
        "improve_next": improve_points[:3],
        "encouragement": encouragement_map[tone],
    }


def get_question_list(session: InterviewSession) -> list[str]:
    language = _lang(session)
    bank = QUESTION_BANK.get(language, QUESTION_BANK["en"])
    return bank.get(session.track.lower(), bank["default"])


def get_leetcode_list(session: InterviewSession) -> list[dict]:
    language = _lang(session)
    bank = LEETCODE_BANK.get(language, LEETCODE_BANK["en"])
    return bank.get(session.level.lower(), bank["junior"])


def get_project_questions(session: InterviewSession, db: Session) -> list[str]:
    language = _lang(session)
    files = get_files_by_session_id(db, session.id)

    if not files:
        if language == "he":
            return [
                "בחרת במצב project-aware, אבל עדיין לא הועלו קבצים. תאר את הארכיטקטורה של הפרויקט ואת החלטות התכנון המרכזיות שלך.",
                "אילו tradeoffs עשית בפרויקט הזה?",
                "מה היית refactor ראשון אם המערכת הזו הייתה צריכה לגדול משמעותית?",
            ]
        return [
            "You selected project-aware mode, but no files were uploaded yet. Describe the architecture of your project and your main design decisions.",
            "What tradeoffs did you make in this project?",
            "What would you refactor first if this system had to scale?",
        ]

    questions = []
    for uploaded_file in files[:5]:
        file_name = Path(uploaded_file.original_name).name
        if language == "he":
            questions.append(f"בקובץ '{file_name}', מה הייתה הכוונה שלך מאחורי המבנה והאחריות שלו?")
            questions.append(f"אילו tradeoffs או maintainability concerns קיימים סביב '{file_name}'?")
        else:
            questions.append(f"In file '{file_name}', what was your intent behind its structure and responsibilities?")
            questions.append(f"What tradeoffs or maintainability concerns exist around '{file_name}'?")
    return questions[:5]


def build_start_question(session: InterviewSession, db: Session) -> str:
    mode = session.mode.lower()
    language = _lang(session)

    if mode == "leetcode":
        item = get_leetcode_list(session)[0]
        if language == "he":
            return f"נתחיל ראיון LeetCode ברמת {session.level}. {item['prompt']}"
        return f"Let's start your LeetCode interview for a {session.level} level. {item['prompt']}"

    if mode == "project_aware":
        return get_project_questions(session, db)[0]

    questions = get_question_list(session)
    if language == "he":
        return f"נתחיל את ראיון ה-{session.track} שלך ברמת {session.level}. שאלה ראשונה: {questions[0]}"
    return f"Let's start your {session.track} interview for a {session.level} level. First question: {questions[0]}"


def _get_last_interviewer_question(db: Session, session_id: int) -> str:
    messages = get_messages_by_session_id(db, session_id)
    for message in reversed(messages):
        if message.role == "interviewer":
            return message.content
    return ""


def _get_first_interviewer_question(db: Session, session_id: int) -> str | None:
    messages = get_messages_by_session_id(db, session_id)
    for message in messages:
        if message.role == "interviewer":
            return message.content
    return None


def build_next_question(session: InterviewSession, next_index: int, db: Session, previous_answer: str) -> str:
    mode = session.mode.lower()

    if mode == "leetcode":
        return get_leetcode_list(session)[next_index]["prompt"]

    if mode == "project_aware":
        questions = get_project_questions(session, db)
        return questions[next_index]

    last_interviewer_question = _get_last_interviewer_question(db, session.id)

    ai_followup = generate_followup_with_openai(
        question=last_interviewer_question,
        answer=previous_answer,
        track=session.track,
        level=session.level,
        mode=session.mode,
        language=_lang(session),
    )
    if ai_followup:
        return ai_followup

    return get_question_list(session)[next_index]


def get_question_count(session: InterviewSession, db: Session) -> int:
    mode = session.mode.lower()
    if mode == "leetcode":
        return len(get_leetcode_list(session))
    if mode == "project_aware":
        return len(get_project_questions(session, db))
    return len(get_question_list(session))


def start_interview(db: Session, session_id: int, current_user_id: int):
    session = _get_owned_session(db, session_id, current_user_id)

    existing_opening_question = _get_first_interviewer_question(db, session.id)
    if existing_opening_question:
        if session.status == "created":
            session.status = "in_progress"
            db.commit()
            db.refresh(session)

        logger.info("Interview already started. Returning existing opening question. session_id=%s", session.id)
        return {
            "session_id": session.id,
            "question": existing_opening_question,
            "status": session.status,
        }

    opening_question = build_start_question(session, db)

    create_message(
        db=db,
        session_id=session.id,
        role="interviewer",
        content=opening_question,
    )

    session.status = "in_progress"
    session.current_question_index = 0
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "question": opening_question,
        "status": session.status,
    }


def answer_interview(db: Session, session_id: int, answer: str, current_user_id: int):
    session = _get_owned_session(db, session_id, current_user_id)
    language = _lang(session)

    if session.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Interview already completed" if language == "en" else "הראיון כבר הושלם",
        )

    cleaned_answer = answer.strip()
    if not cleaned_answer:
        raise HTTPException(
            status_code=422,
            detail="Answer cannot be empty" if language == "en" else "התשובה לא יכולה להיות ריקה",
        )

    last_question = _get_last_interviewer_question(db, session.id)
    if not last_question:
        raise HTTPException(
            status_code=400,
            detail="Interview has not started yet" if language == "en" else "הראיון עדיין לא התחיל",
        )

    candidate_message = create_message(
        db,
        session_id=session.id,
        role="candidate",
        content=cleaned_answer,
    )

    scoring_result = score_answer(
        question=last_question,
        answer=cleaned_answer,
        track=session.track,
        level=session.level,
        mode=session.mode,
        language=language,
    )

    logger.info(
        "Answer scored. session_id=%s source=%s fallback_reason=%s score=%s",
        session.id,
        scoring_result.get("source"),
        scoring_result.get("fallback_reason"),
        scoring_result.get("score"),
    )

    for breakdown_item in scoring_result["breakdown"]:
        create_score(
            db=db,
            session_id=session.id,
            message_id=candidate_message.id,
            category=breakdown_item["category"],
            score=breakdown_item["score"],
            confidence=breakdown_item.get("confidence"),
        )

    review = _build_answer_review(
        message_id=candidate_message.id,
        breakdown=scoring_result["breakdown"],
        language=language,
        strengths_text=scoring_result.get("strengths", ""),
        weaknesses_text=scoring_result.get("weaknesses", ""),
        reason_text=scoring_result.get("reason", ""),
    )

    next_index = session.current_question_index + 1
    question_count = get_question_count(session, db)

    if next_index >= question_count:
        session.status = "completed"
        db.commit()
        db.refresh(session)
        build_session_report(db, session.id)

        return {
            "session_id": session.id,
            "user_answer": cleaned_answer,
            "next_question": "Interview completed." if language == "en" else "הראיון הושלם.",
            "status": session.status,
            "score": scoring_result["score"],
            "review": review,
        }

    next_question = build_next_question(session, next_index, db, cleaned_answer)

    create_message(db, session_id=session.id, role="interviewer", content=next_question)

    session.current_question_index = next_index
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "user_answer": cleaned_answer,
        "next_question": next_question,
        "status": session.status,
        "score": scoring_result["score"],
        "review": review,
    }


def finish_interview(db: Session, session_id: int, current_user_id: int):
    session = _get_owned_session(db, session_id, current_user_id)

    if session.status != "completed":
        session.status = "completed"
        db.commit()
        db.refresh(session)

    report = build_session_report(db, session.id)

    return {
        "session_id": session.id,
        "status": session.status,
        "report_id": report.id,
    }


def get_session_transcript(db: Session, session_id: int, current_user_id: int):
    session = _get_owned_session(db, session_id, current_user_id)
    messages = get_messages_by_session_id(db, session_id)
    scores = get_scores_by_session_id(db, session_id)

    grouped_scores = {}
    for score in scores:
        if score.message_id is None:
            continue
        grouped_scores.setdefault(score.message_id, []).append(
            {
                "category": score.category,
                "score": score.score,
                "confidence": score.confidence,
            }
        )

    answer_reviews = []
    for message in messages:
        if message.role != "candidate":
            continue

        breakdown = grouped_scores.get(message.id, [])
        if not breakdown:
            continue

        answer_reviews.append(
            _build_answer_review(
                message_id=message.id,
                breakdown=breakdown,
                language=_lang(session),
            )
        )

    return {
        "session_id": session.id,
        "status": session.status,
        "messages": messages,
        "answer_reviews": answer_reviews,
    }