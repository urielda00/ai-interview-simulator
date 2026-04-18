import io
import sys
import traceback
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import Base, engine
from app.services.ai_service import has_openai, generate_followup_with_openai
from app.core.i18n import is_hebrew_text


class StepFailure(Exception):
    def __init__(self, step: str, message: str):
        super().__init__(f"[{step}] {message}")
        self.step = step
        self.message = message


def ok(step: str, message: str):
    print(f"[OK] {step} - {message}")


def fail(step: str, message: str):
    raise StepFailure(step, message)


def assert_true(condition: bool, step: str, message: str):
    if not condition:
        fail(step, message)


def assert_status(response, expected_status: int, step: str):
    if response.status_code != expected_status:
        body = ""
        try:
            body = response.text
        except Exception:
            body = "<no body>"
        fail(step, f"Expected status {expected_status}, got {response.status_code}. Body: {body}")


def main():
    step = "bootstrap"

    try:
        Base.metadata.create_all(bind=engine)
        client = TestClient(app)
        unique = datetime.now().strftime("%Y%m%d%H%M%S")
        email = f"e2e_{unique}@example.com"
        password = "123456"

        step = "env_openai"
        assert_true(bool(settings.OPENAI_API_KEY), step, "OPENAI_API_KEY is missing in .env")
        assert_true(bool(settings.OPENAI_MODEL), step, "OPENAI_MODEL is missing in .env")
        assert_true(has_openai(), step, "OpenAI client is not available")

        step = "ai_sanity"
        ai_question = generate_followup_with_openai(
            question="What is JWT?",
            answer="JWT is a signed token used for stateless authentication in many backend systems.",
            track="backend",
            level="junior",
            mode="standard",
            language="en",
        )
        assert_true(bool(ai_question and len(ai_question.strip()) > 10), step, f"AI sanity check failed. Returned: {ai_question}")
        ok(step, f"AI returned follow-up question: {ai_question}")

        step = "root"
        response = client.get("/")
        assert_status(response, 200, step)
        assert_true(response.json().get("message") == "AI Interview Simulator API is running", step, "Root response message mismatch")
        ok(step, "Root endpoint works")

        step = "health"
        response = client.get("/api/v1/health/")
        assert_status(response, 200, step)
        assert_true(response.json().get("status") == "ok", step, "Health status mismatch")
        ok(step, "Health endpoint works")

        step = "register"
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "E2E User",
            },
        )
        assert_status(response, 200, step)
        user = response.json()
        user_id = user["id"]
        assert_true(user["email"] == email, step, "Registered email mismatch")
        ok(step, f"Registered user id={user_id}")

        step = "login"
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        assert_status(response, 200, step)
        token_data = response.json()
        token = token_data["access_token"]
        assert_true(bool(token), step, "Missing access token")
        headers_en = {
            "Authorization": f"Bearer {token}",
            "Accept-Language": "en",
        }
        headers_he = {
            "Authorization": f"Bearer {token}",
            "Accept-Language": "he",
        }
        ok(step, "Login works")

        step = "me"
        response = client.get("/api/v1/auth/me", headers=headers_en)
        assert_status(response, 200, step)
        me = response.json()
        assert_true(me["id"] == user_id, step, "Authenticated user id mismatch")
        ok(step, "Auth me works")

        step = "create_standard_session"
        response = client.post(
            "/api/v1/sessions/",
            headers=headers_en,
            json={
                "track": "backend",
                "level": "junior",
                "mode": "standard",
                "language": "en",
            },
        )
        assert_status(response, 200, step)
        standard_session = response.json()
        standard_session_id = standard_session["id"]
        assert_true(standard_session["user_id"] == user_id, step, "Session owner mismatch")
        ok(step, f"Standard session created id={standard_session_id}")

        step = "list_my_sessions"
        response = client.get("/api/v1/sessions/", headers=headers_en)
        assert_status(response, 200, step)
        sessions_list = response.json()
        assert_true(len(sessions_list) >= 1, step, "Sessions list is empty")
        ok(step, f"My sessions count={len(sessions_list)}")

        step = "get_my_session"
        response = client.get(f"/api/v1/sessions/{standard_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        ok(step, "Owned session fetch works")

        step = "start_standard_interview"
        response = client.post(
            "/api/v1/interviews/start",
            headers=headers_en,
            json={"session_id": standard_session_id},
        )
        assert_status(response, 200, step)
        start_data = response.json()
        opening_question = start_data["question"]
        assert_true(start_data["status"] == "in_progress", step, "Interview did not enter in_progress")
        assert_true(len(opening_question) > 20, step, "Opening question too short")
        ok(step, f"Standard interview started: {opening_question}")

        step = "answer_standard_interview"
        standard_answer = (
            "Authentication verifies identity, while authorization decides permissions. "
            "In a backend system I would validate JWT tokens in middleware, hash passwords, "
            "enforce RBAC, validate inputs, and consider tradeoffs like stateless scaling versus revocation complexity."
        )
        response = client.post(
            "/api/v1/interviews/answer",
            headers=headers_en,
            json={
                "session_id": standard_session_id,
                "answer": standard_answer,
            },
        )
        assert_status(response, 200, step)
        answer_data = response.json()
        assert_true(answer_data["score"] > 0, step, "Score was not generated")
        assert_true(answer_data["next_question"] != opening_question, step, "Next question should not equal opening question")
        ok(step, f"Standard answer scored={answer_data['score']} next_question={answer_data['next_question']}")

        step = "standard_transcript"
        response = client.get(f"/api/v1/interviews/transcript/{standard_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        transcript = response.json()
        messages = transcript["messages"]
        assert_true(len(messages) >= 3, step, "Transcript should have at least 3 messages")
        assert_true(messages[0]["role"] == "interviewer", step, "Message 1 role mismatch")
        assert_true(messages[1]["role"] == "candidate", step, "Message 2 role mismatch")
        assert_true(messages[2]["role"] == "interviewer", step, "Message 3 role mismatch")
        ok(step, f"Standard transcript length={len(messages)}")

        step = "standard_score_summary"
        response = client.get(f"/api/v1/history/scores/{standard_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        score_summary = response.json()
        assert_true(score_summary["session_id"] == standard_session_id, step, "Score summary session mismatch")
        assert_true(score_summary["total_scores"] >= 1, step, "No score rows found")
        assert_true(len(score_summary["breakdown"]) >= 1, step, "Breakdown is empty")
        ok(step, f"Standard score breakdown categories={len(score_summary['breakdown'])}")

        step = "finish_standard"
        response = client.post(f"/api/v1/interviews/finish/{standard_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        finish_data = response.json()
        assert_true(finish_data["status"] == "completed", step, "Finish did not mark session completed")
        ok(step, f"Standard interview finished with report_id={finish_data['report_id']}")

        step = "standard_report"
        response = client.get(f"/api/v1/reports/{standard_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        report = response.json()
        assert_true(bool(report["summary"]), step, "Report summary is empty")
        assert_true(bool(report["strengths"]), step, "Report strengths are empty")
        assert_true(bool(report["weaknesses"]), step, "Report weaknesses are empty")
        assert_true(bool(report["study_plan"]), step, "Report study_plan is empty")
        ok(step, "Standard report exists")

        step = "history_sessions_after_standard"
        response = client.get("/api/v1/history/sessions", headers=headers_en)
        assert_status(response, 200, step)
        history_items = response.json()
        assert_true(len(history_items) >= 1, step, "History list is empty")
        assert_true(any(item["id"] == standard_session_id for item in history_items), step, "Standard session not found in history")
        ok(step, f"History sessions count={len(history_items)}")

        step = "create_hebrew_session"
        response = client.post(
            "/api/v1/sessions/",
            headers=headers_he,
            json={
                "track": "backend",
                "level": "junior",
                "mode": "standard",
                "language": "he",
            },
        )
        assert_status(response, 200, step)
        hebrew_session_id = response.json()["id"]
        ok(step, f"Hebrew session created id={hebrew_session_id}")

        step = "start_hebrew_interview"
        response = client.post(
            "/api/v1/interviews/start",
            headers=headers_he,
            json={"session_id": hebrew_session_id},
        )
        assert_status(response, 200, step)
        hebrew_start = response.json()
        assert_true(is_hebrew_text(hebrew_start["question"]), step, "Hebrew opening question was not detected as Hebrew")
        ok(step, f"Hebrew interview started: {hebrew_start['question']}")

        step = "answer_hebrew_interview"
        hebrew_answer = (
            "Authentication מאמת זהות, ו-authorization קובע הרשאות. "
            "במערכת backend הייתי בודק JWT ב-middleware, מוסיף validation, "
            "ושוקל tradeoffs כמו scalability מול revocation."
        )
        response = client.post(
            "/api/v1/interviews/answer",
            headers=headers_he,
            json={
                "session_id": hebrew_session_id,
                "answer": hebrew_answer,
            },
        )
        assert_status(response, 200, step)
        hebrew_answer_data = response.json()
        assert_true(hebrew_answer_data["score"] > 0, step, "Hebrew answer score missing")
        assert_true(is_hebrew_text(hebrew_answer_data["next_question"]), step, "Hebrew next question was not detected as Hebrew")
        ok(step, f"Hebrew answer scored={hebrew_answer_data['score']}")

        step = "finish_hebrew"
        response = client.post(f"/api/v1/interviews/finish/{hebrew_session_id}", headers=headers_he)
        assert_status(response, 200, step)
        ok(step, "Hebrew interview finished")

        step = "hebrew_report"
        response = client.get(f"/api/v1/reports/{hebrew_session_id}", headers=headers_he)
        assert_status(response, 200, step)
        hebrew_report = response.json()
        assert_true(bool(hebrew_report["summary"]), step, "Hebrew report summary missing")
        assert_true(is_hebrew_text(hebrew_report["summary"]), step, "Hebrew report summary was not detected as Hebrew")
        ok(step, "Hebrew report exists")

        step = "create_leetcode_session"
        response = client.post(
            "/api/v1/sessions/",
            headers=headers_en,
            json={
                "track": "backend",
                "level": "junior",
                "mode": "leetcode",
                "language": "en",
            },
        )
        assert_status(response, 200, step)
        leetcode_session_id = response.json()["id"]
        ok(step, f"LeetCode session created id={leetcode_session_id}")

        step = "start_leetcode"
        response = client.post(
            "/api/v1/interviews/start",
            headers=headers_en,
            json={"session_id": leetcode_session_id},
        )
        assert_status(response, 200, step)
        leetcode_start = response.json()
        assert_true("LeetCode" in leetcode_start["question"], step, "LeetCode opening question mismatch")
        ok(step, "LeetCode interview started")

        step = "answer_leetcode"
        leetcode_answer = (
            "I would use a hash map to store numbers I have already seen and their indices. "
            "For each value, I check whether target minus current value is already in the map. "
            "This gives O(n) time complexity and O(n) space complexity. "
            "In Python I would loop once and return indices as soon as I find a match."
        )
        response = client.post(
            "/api/v1/interviews/answer",
            headers=headers_en,
            json={
                "session_id": leetcode_session_id,
                "answer": leetcode_answer,
            },
        )
        assert_status(response, 200, step)
        leetcode_answer_data = response.json()
        assert_true(leetcode_answer_data["score"] > 0, step, "LeetCode score missing")
        ok(step, f"LeetCode answer scored={leetcode_answer_data['score']}")

        step = "leetcode_score_summary"
        response = client.get(f"/api/v1/history/scores/{leetcode_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        leetcode_scores = response.json()
        assert_true(leetcode_scores["total_scores"] >= 1, step, "LeetCode score rows missing")
        assert_true(len(leetcode_scores["breakdown"]) >= 1, step, "LeetCode breakdown empty")
        ok(step, f"LeetCode breakdown categories={len(leetcode_scores['breakdown'])}")

        step = "finish_leetcode"
        response = client.post(f"/api/v1/interviews/finish/{leetcode_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        ok(step, "LeetCode interview finished")

        step = "leetcode_report"
        response = client.get(f"/api/v1/reports/{leetcode_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        leetcode_report = response.json()
        assert_true(bool(leetcode_report["summary"]), step, "LeetCode report summary missing")
        ok(step, "LeetCode report exists")

        step = "create_project_aware_session"
        response = client.post(
            "/api/v1/sessions/",
            headers=headers_en,
            json={
                "track": "backend",
                "level": "junior",
                "mode": "project_aware",
                "language": "en",
            },
        )
        assert_status(response, 200, step)
        project_session_id = response.json()["id"]
        ok(step, f"Project-aware session created id={project_session_id}")

        step = "upload_project_file"
        sample_code = b"def login_user(email, password):\n    return {'ok': True}\n"
        response = client.post(
            f"/api/v1/uploads/project-files/{project_session_id}",
            headers=headers_en,
            files={"file": ("auth_service.py", io.BytesIO(sample_code), "text/x-python")},
        )
        assert_status(response, 200, step)
        uploaded = response.json()
        assert_true(uploaded["original_name"] == "auth_service.py", step, "Uploaded filename mismatch")
        ok(step, "Project file uploaded")

        step = "list_project_files"
        response = client.get(f"/api/v1/uploads/project-files/{project_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        files_list = response.json()
        assert_true(len(files_list) >= 1, step, "Uploaded files list is empty")
        ok(step, f"Project files count={len(files_list)}")

        step = "start_project_aware"
        response = client.post(
            "/api/v1/interviews/start",
            headers=headers_en,
            json={"session_id": project_session_id},
        )
        assert_status(response, 200, step)
        project_start = response.json()
        assert_true("auth_service.py" in project_start["question"], step, "Project-aware question did not reference uploaded file")
        ok(step, f"Project-aware interview started: {project_start['question']}")

        step = "answer_project_aware"
        project_answer = (
            "I separated this file to keep authentication responsibilities isolated. "
            "The tradeoff is another abstraction layer, but it improves maintainability, testing, and scaling. "
            "If the system grows, I would further separate token handling, password hashing, and validation."
        )
        response = client.post(
            "/api/v1/interviews/answer",
            headers=headers_en,
            json={
                "session_id": project_session_id,
                "answer": project_answer,
            },
        )
        assert_status(response, 200, step)
        project_answer_data = response.json()
        assert_true(project_answer_data["score"] > 0, step, "Project-aware score missing")
        ok(step, f"Project-aware answer scored={project_answer_data['score']}")

        step = "project_score_summary"
        response = client.get(f"/api/v1/history/scores/{project_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        project_scores = response.json()
        assert_true(project_scores["total_scores"] >= 1, step, "Project-aware score rows missing")
        assert_true(len(project_scores["breakdown"]) >= 1, step, "Project-aware breakdown empty")
        ok(step, f"Project-aware breakdown categories={len(project_scores['breakdown'])}")

        step = "finish_project_aware"
        response = client.post(f"/api/v1/interviews/finish/{project_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        ok(step, "Project-aware interview finished")

        step = "project_aware_report"
        response = client.get(f"/api/v1/reports/{project_session_id}", headers=headers_en)
        assert_status(response, 200, step)
        project_report = response.json()
        assert_true(bool(project_report["summary"]), step, "Project-aware report summary missing")
        ok(step, "Project-aware report exists")

        step = "final_history_sessions"
        response = client.get("/api/v1/history/sessions", headers=headers_en)
        assert_status(response, 200, step)
        final_history = response.json()
        assert_true(len(final_history) >= 4, step, "Final history should contain at least 4 sessions")
        ok(step, f"Final history sessions count={len(final_history)}")

        print("\nALL CHECKS PASSED")
        print(f"User id: {user_id}")
        print(f"Standard session id: {standard_session_id}")
        print(f"Hebrew session id: {hebrew_session_id}")
        print(f"LeetCode session id: {leetcode_session_id}")
        print(f"Project-aware session id: {project_session_id}")

    except StepFailure as exc:
        print("\nCHECK FAILED")
        print(f"STEP: {exc.step}")
        print(f"DETAIL: {exc.message}")
        sys.exit(1)
    except Exception as exc:
        print("\nUNEXPECTED ERROR")
        print(f"STEP: {step}")
        print(f"ERROR: {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()