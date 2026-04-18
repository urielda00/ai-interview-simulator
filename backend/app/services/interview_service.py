import logging
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.interview_session import InterviewSession
from app.repositories.message_repository import create_message, get_messages_by_session_id
from app.repositories.session_repository import get_session_by_id_and_user_id
from app.repositories.score_repository import create_score
from app.repositories.upload_repository import get_files_by_session_id
from app.services.ai_service import generate_followup_with_openai
from app.services.scoring_service import score_answer
from app.services.report_service import build_session_report


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

    return {
        "session_id": session.id,
        "status": session.status,
        "messages": messages,
    }