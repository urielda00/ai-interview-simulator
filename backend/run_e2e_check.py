import io
import sys
import traceback
from datetime import datetime

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import Base, engine
from app.main import app
from app.services.ai_service import generate_followup_with_openai, has_openai


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


def contains_any(text: str, candidates: list[str]) -> bool:
    text_lower = text.lower()
    return any(candidate.lower() in text_lower for candidate in candidates)


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
        headers = {"Authorization": f"Bearer {token}"}
        ok(step, "Login works")

        step = "me"
        response = client.get("/api/v1/auth/me", headers=headers)
        assert_status(response, 200, step)
        me = response.json()
        assert_true(me["id"] == user_id, step, "Authenticated user id mismatch")
        ok(step, "Auth me works")

        step = "create_standard_session"
        response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            json={
                "track": "backend",
                "level": "junior",
                "mode": "standard",
            },
        )
        assert_status(response, 200, step)
        standard_session = response.json()
        standard_session_id = standard_session["id"]
        assert_true(standard_session["user_id"] == user_id, step, "Session owner mismatch")
        ok(step, f"Standard session created id={standard_session_id}")

        step = "list_my_sessions"
        response = client.get("/api/v1/sessions/", headers=headers)
        assert_status(response, 200, step)
        sessions_list = response.json()
        assert_true(len(sessions_list) >= 1, step, "Sessions list is empty")
        ok(step, f"My sessions count={len(sessions_list)}")

        step = "get_my_session"
        response = client.get(f"/api/v1/sessions/{standard_session_id}", headers=headers)
        assert_status(response, 200, step)
        ok(step, "Owned session fetch works")

        step = "start_standard_interview"
        response = client.post(
            "/api/v1/interviews/start",
            headers=headers,
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
            headers=headers,
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
        response = client.get(f"/api/v1/interviews/transcript/{standard_session_id}", headers=headers)
        assert_status(response, 200, step)
        transcript = response.json()
        messages = transcript["messages"]
        assert_true(len(messages) >= 3, step, "Transcript should have at least 3 messages")
        assert_true(messages[0]["role"] == "interviewer", step, "Message 1 role mismatch")
        assert_true(messages[1]["role"] == "candidate", step, "Message 2 role mismatch")
        assert_true(messages[2]["role"] == "interviewer", step, "Message 3 role mismatch")
        ok(step, f"Standard transcript length={len(messages)}")

        step = "standard_score_summary"
        response = client.get(f"/api/v1/history/scores/{standard_session_id}", headers=headers)
        assert_status(response, 200, step)
        score_summary = response.json()
        assert_true(score_summary["session_id"] == standard_session_id, step, "Score summary session mismatch")
        assert_true(score_summary["total_scores"] >= 1, step, "No score rows found")
        assert_true(len(score_summary["breakdown"]) >= 1, step, "Breakdown is empty")
        ok(step, f"Standard score breakdown categories={len(score_summary['breakdown'])}")

        step = "finish_standard"
        response = client.post(f"/api/v1/interviews/finish/{standard_session_id}", headers=headers)
        assert_status(response, 200, step)
        finish_data = response.json()
        assert_true(finish_data["status"] == "completed", step, "Finish did not mark session completed")
        ok(step, f"Standard interview finished with report_id={finish_data['report_id']}")

        step = "standard_report"
        response = client.get(f"/api/v1/reports/{standard_session_id}", headers=headers)
        assert_status(response, 200, step)
        report = response.json()
        assert_true(bool(report["summary"]), step, "Report summary is empty")
        assert_true(bool(report["strengths"]), step, "Report strengths are empty")
        assert_true(bool(report["weaknesses"]), step, "Report weaknesses are empty")
        assert_true(bool(report["study_plan"]), step, "Report study_plan is empty")
        ok(step, "Standard report exists")

        step = "history_sessions_after_standard"
        response = client.get("/api/v1/history/sessions", headers=headers)
        assert_status(response, 200, step)
        history_items = response.json()
        assert_true(len(history_items) >= 1, step, "History list is empty")
        assert_true(any(item["id"] == standard_session_id for item in history_items), step, "Standard session not found in history")
        ok(step, f"History sessions count={len(history_items)}")

        step = "create_leetcode_session"
        response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            json={
                "track": "backend",
                "level": "junior",
                "mode": "leetcode",
            },
        )
        assert_status(response, 200, step)
        leetcode_session_id = response.json()["id"]
        ok(step, f"LeetCode session created id={leetcode_session_id}")

        step = "start_leetcode"
        response = client.post(
            "/api/v1/interviews/start",
            headers=headers,
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
            headers=headers,
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
        response = client.get(f"/api/v1/history/scores/{leetcode_session_id}", headers=headers)
        assert_status(response, 200, step)
        leetcode_scores = response.json()
        assert_true(leetcode_scores["total_scores"] >= 1, step, "LeetCode score rows missing")
        assert_true(len(leetcode_scores["breakdown"]) >= 1, step, "LeetCode breakdown empty")
        ok(step, f"LeetCode breakdown categories={len(leetcode_scores['breakdown'])}")

        step = "finish_leetcode"
        response = client.post(f"/api/v1/interviews/finish/{leetcode_session_id}", headers=headers)
        assert_status(response, 200, step)
        ok(step, "LeetCode interview finished")

        step = "leetcode_report"
        response = client.get(f"/api/v1/reports/{leetcode_session_id}", headers=headers)
        assert_status(response, 200, step)
        leetcode_report = response.json()
        assert_true(bool(leetcode_report["summary"]), step, "LeetCode report summary missing")
        ok(step, "LeetCode report exists")

        step = "create_project_aware_session"
        response = client.post(
            "/api/v1/sessions/",
            headers=headers,
            json={
                "track": "backend",
                "level": "junior",
                "mode": "project_aware",
            },
        )
        assert_status(response, 200, step)
        project_session_id = response.json()["id"]
        ok(step, f"Project-aware session created id={project_session_id}")

        step = "upload_project_file"
        sample_code = b'''import jwt\nfrom passlib.context import CryptContext\n\npwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")\n\ndef validate_credentials(email: str, password: str) -> bool:\n    return bool(email and password)\n\ndef login_user(email: str, password: str):\n    if not validate_credentials(email, password):\n        raise ValueError("invalid credentials")\n    token = jwt.encode({"sub": email}, "secret", algorithm="HS256")\n    password_hash = pwd_context.hash(password)\n    return {"token": token, "password_hash": password_hash}\n'''
        response = client.post(
            f"/api/v1/uploads/project-files/{project_session_id}",
            headers=headers,
            files={"file": ("auth_service.py", io.BytesIO(sample_code), "text/x-python")},
        )
        assert_status(response, 200, step)
        uploaded = response.json()
        assert_true(uploaded["original_name"] == "auth_service.py", step, "Uploaded filename mismatch")
        ok(step, "Project file uploaded")

        step = "list_project_files"
        response = client.get(f"/api/v1/uploads/project-files/{project_session_id}", headers=headers)
        assert_status(response, 200, step)
        files_list = response.json()
        assert_true(len(files_list) >= 1, step, "Uploaded files list is empty")
        ok(step, f"Project files count={len(files_list)}")

        step = "start_project_aware"
        response = client.post(
            "/api/v1/interviews/start",
            headers=headers,
            json={"session_id": project_session_id},
        )
        assert_status(response, 200, step)
        project_start = response.json()
        project_opening_question = project_start["question"]

        assert_true(
            contains_any(
                project_opening_question,
                [
                    "login_user",
                    "validate_credentials",
                    "jwt",
                    "passlib",
                    "auth",
                    "password",
                    "token",
                ],
            ),
            step,
            f"Project-aware opening question did not reference real code content. Got: {project_opening_question}",
        )
        ok(step, f"Project-aware interview started: {project_opening_question}")

        step = "answer_project_aware"
        project_answer = (
            "I kept login_user as the main entry point because it makes the auth flow easy to follow. "
            "The tradeoff is that token creation, password hashing, and validation can become too coupled in one place. "
            "If the system grows, I would split credential validation, token handling, and hashing into narrower units."
        )
        response = client.post(
            "/api/v1/interviews/answer",
            headers=headers,
            json={
                "session_id": project_session_id,
                "answer": project_answer,
            },
        )
        assert_status(response, 200, step)
        project_answer_data = response.json()
        next_project_question = project_answer_data["next_question"]

        assert_true(project_answer_data["score"] > 0, step, "Project-aware score missing")
        assert_true(
            contains_any(
                next_project_question,
                [
                    "jwt",
                    "passlib",
                    "validation",
                    "auth",
                    "imports",
                    "dependencies",
                    "token",
                    "hash",
                ],
            ),
            step,
            f"Project-aware next question did not stay grounded in code content. Got: {next_project_question}",
        )
        ok(step, f"Project-aware answer scored={project_answer_data['score']} next_question={next_project_question}")

        step = "project_score_summary"
        response = client.get(f"/api/v1/history/scores/{project_session_id}", headers=headers)
        assert_status(response, 200, step)
        project_scores = response.json()
        assert_true(project_scores["total_scores"] >= 1, step, "Project-aware score rows missing")
        assert_true(len(project_scores["breakdown"]) >= 1, step, "Project-aware breakdown empty")
        ok(step, f"Project-aware breakdown categories={len(project_scores['breakdown'])}")

        step = "finish_project_aware"
        response = client.post(f"/api/v1/interviews/finish/{project_session_id}", headers=headers)
        assert_status(response, 200, step)
        ok(step, "Project-aware interview finished")

        step = "project_aware_report"
        response = client.get(f"/api/v1/reports/{project_session_id}", headers=headers)
        assert_status(response, 200, step)
        project_report = response.json()
        assert_true(bool(project_report["summary"]), step, "Project-aware report summary missing")
        ok(step, "Project-aware report exists")

        step = "final_history_sessions"
        response = client.get("/api/v1/history/sessions", headers=headers)
        assert_status(response, 200, step)
        final_history = response.json()
        assert_true(len(final_history) >= 3, step, "Final history should contain at least 3 sessions")
        ok(step, f"Final history sessions count={len(final_history)}")

        print("\nALL CHECKS PASSED")
        print(f"User id: {user_id}")
        print(f"Standard session id: {standard_session_id}")
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