import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.interview_session import InterviewSession
from app.repositories.message_repository import create_message, get_messages_by_session_id
from app.repositories.score_repository import create_score
from app.repositories.session_repository import get_session_by_id_and_user_id
from app.repositories.upload_repository import get_files_by_session_id
from app.services.ai_service import generate_followup_with_openai
from app.services.code_analysis_service import build_project_aware_questions
from app.services.report_service import build_session_report
from app.services.scoring_service import score_answer


logger = logging.getLogger(__name__)


QUESTION_BANK = {
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
}

LEETCODE_BANK = {
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
}


def _get_owned_session(db: Session, session_id: int, current_user_id: int):
    session = get_session_by_id_and_user_id(db, session_id, current_user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def get_question_list(session: InterviewSession) -> list[str]:
    return QUESTION_BANK.get(session.track.lower(), QUESTION_BANK["default"])


def get_leetcode_list(session: InterviewSession) -> list[dict]:
    return LEETCODE_BANK.get(session.level.lower(), LEETCODE_BANK["junior"])


def get_project_questions(session: InterviewSession, db: Session) -> list[str]:
    files = get_files_by_session_id(db, session.id)

    if not files:
        return [
            "You selected project-aware mode, but no files were uploaded yet. Describe the architecture of your project and your main design decisions.",
            "What tradeoffs did you make in this project?",
            "What would you refactor first if this system had to scale?",
        ]

    questions = build_project_aware_questions(files)

    if not questions:
        return [
            "I could not extract enough signal from the uploaded files. Describe the architecture of your project and your main design decisions.",
            "What tradeoffs did you make in this project?",
            "What would you refactor first if this system had to scale?",
        ]

    return questions[:5]


def build_start_question(session: InterviewSession, db: Session) -> str:
    mode = session.mode.lower()

    if mode == "leetcode":
        item = get_leetcode_list(session)[0]
        return f"Let's start your LeetCode interview for a {session.level} level. {item['prompt']}"

    if mode == "project_aware":
        return get_project_questions(session, db)[0]

    questions = get_question_list(session)
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

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    cleaned_answer = answer.strip()
    if not cleaned_answer:
        raise HTTPException(status_code=422, detail="Answer cannot be empty")

    last_question = _get_last_interviewer_question(db, session.id)
    if not last_question:
        raise HTTPException(status_code=400, detail="Interview has not started yet")

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
            "next_question": "Interview completed.",
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