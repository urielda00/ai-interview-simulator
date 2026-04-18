# API Contract - AI Interview Simulator Backend

Base URL:
/api/v1

Content-Type:
application/json

Authentication:
Protected endpoints require:
Authorization: Bearer <token>

---

## 1. Health

### GET /api/v1/health/

Purpose:
Server health check.

Auth required:
No

Response 200:
{
  "status": "ok"
}

---

## 2. Auth

### POST /api/v1/auth/register

Purpose:
Create a new user.

Auth required:
No

Request body:
{
  "email": "demo@example.com",
  "password": "123456",
  "full_name": "Demo User"
}

Validation:
- email - required, valid email
- password - required, min 6 chars, max 72 chars
- full_name - optional

Response 200:
{
  "id": 1,
  "email": "demo@example.com",
  "full_name": "Demo User",
  "created_at": "2026-04-17T20:00:00.000000+03:00"
}

Possible errors:
- 400 - email already registered
- 422 - invalid request body

Example 400:
{
  "detail": "Email already registered"
}

---

### POST /api/v1/auth/login

Purpose:
Login and receive JWT token.

Auth required:
No

Request body:
{
  "email": "demo@example.com",
  "password": "123456"
}

Response 200:
{
  "access_token": "jwt_here",
  "token_type": "bearer"
}

Possible errors:
- 401 - invalid credentials
- 422 - invalid request body
- 500 - stored password hash is invalid / old seed problem

Example 401:
{
  "detail": "Invalid credentials"
}

---

### GET /api/v1/auth/me

Purpose:
Return currently authenticated user.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Response 200:
{
  "id": 1,
  "email": "demo@example.com",
  "full_name": "Demo User",
  "created_at": "2026-04-17T20:00:00.000000+03:00"
}

Possible errors:
- 401 - invalid token
- 401 - missing token
- 401 - user not found

Example 401:
{
  "detail": "Invalid token"
}

---

### GET /api/v1/auth/{user_id}

Purpose:
Return user by id.

Auth required:
No

Path params:
- user_id - integer

Response 200:
{
  "id": 1,
  "email": "demo@example.com",
  "full_name": "Demo User",
  "created_at": "2026-04-17T20:00:00.000000+03:00"
}

Possible errors:
- 404 - user not found

Example 404:
{
  "detail": "User not found"
}

---

## 3. Sessions

### POST /api/v1/sessions/

Purpose:
Create a new interview session for the currently authenticated user.

Auth required:
Yes

Headers:
Authorization: Bearer <token>
Accept-Language: he | en (optional)

Request body:
{
  "track": "backend",
  "level": "junior",
  "mode": "standard",
  "language": "he"
}

Field rules:
- track - required, string
- level - required, string
- mode - required, string
- language - optional, "he" or "en"

Supported mode values:
- standard
- leetcode
- project_aware

Supported language values:
- he
- en

Common level values:
- junior
- mid
- senior

Language resolution order:
1. request body field `language`
2. `Accept-Language` header
3. default `en`

Response 200:
{
  "id": 1,
  "user_id": 1,
  "track": "backend",
  "level": "junior",
  "mode": "standard",
  "status": "created",
  "current_question_index": 0,
  "created_at": "2026-04-17T20:05:00.000000+03:00"
}

Possible errors:
- 401 - missing/invalid token
- 422 - invalid request body

Notes:
- user_id is taken from the token, not from the request body
- session language is stored and used for the rest of the interview/report flow
- response schema is unchanged

---

### GET /api/v1/sessions/

Purpose:
Return all sessions belonging to the currently authenticated user.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Response 200:
[
  {
    "id": 3,
    "user_id": 1,
    "track": "backend",
    "level": "junior",
    "mode": "project_aware",
    "status": "completed",
    "current_question_index": 1,
    "created_at": "2026-04-17T20:25:00.000000+03:00"
  },
  {
    "id": 2,
    "user_id": 1,
    "track": "backend",
    "level": "junior",
    "mode": "leetcode",
    "status": "completed",
    "current_question_index": 1,
    "created_at": "2026-04-17T20:15:00.000000+03:00"
  },
  {
    "id": 1,
    "user_id": 1,
    "track": "backend",
    "level": "junior",
    "mode": "standard",
    "status": "completed",
    "current_question_index": 1,
    "created_at": "2026-04-17T20:05:00.000000+03:00"
  }
]

Possible errors:
- 401 - missing/invalid token

---

### GET /api/v1/sessions/{session_id}

Purpose:
Return a specific session belonging to the currently authenticated user.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Path params:
- session_id - integer

Response 200:
{
  "id": 1,
  "user_id": 1,
  "track": "backend",
  "level": "junior",
  "mode": "standard",
  "status": "created",
  "current_question_index": 0,
  "created_at": "2026-04-17T20:05:00.000000+03:00"
}

Possible errors:
- 401 - missing/invalid token
- 404 - session not found

Example 404:
{
  "detail": "Session not found"
}

Session status values currently used:
- created
- in_progress
- completed

---

## 4. Interviews

### POST /api/v1/interviews/start

Purpose:
Start interview for an existing owned session and create the first interviewer message.

Auth required:
Yes

Headers:
Authorization: Bearer <token>
Accept-Language: he | en (optional)

Request body:
{
  "session_id": 1
}

Response 200:
{
  "session_id": 1,
  "question": "Let's start your backend interview for a junior level. First question: Explain the difference between authentication and authorization.",
  "status": "in_progress"
}

Behavior by mode:
- standard - starts normal technical Q&A
- leetcode - starts coding-style interview
- project_aware - starts project-based questioning using uploaded file names if available

Language behavior:
- user-facing text is returned in the saved session language
- `Accept-Language` may still be sent by frontend for consistency, but session language is the source of truth after session creation

Possible errors:
- 401 - missing/invalid token
- 404 - session not found

Example 404:
{
  "detail": "Session not found"
}

---

### POST /api/v1/interviews/answer

Purpose:
Save candidate answer, score it, and return next question or completion.

Auth required:
Yes

Headers:
Authorization: Bearer <token>
Accept-Language: he | en (optional)

Request body:
{
  "session_id": 1,
  "answer": "Authentication verifies identity, while authorization decides permissions."
}

Response 200:
{
  "session_id": 1,
  "user_answer": "Authentication verifies identity, while authorization decides permissions.",
  "next_question": "How does JWT-based authentication work in a backend system?",
  "status": "in_progress",
  "score": 8.0
}

When interview reaches the end:
{
  "session_id": 1,
  "user_answer": "Final answer text",
  "next_question": "Interview completed.",
  "status": "completed",
  "score": 7.5
}

Field meanings:
- session_id - current session id
- user_answer - exact answer text sent by the client
- next_question - next interviewer question or completion message
- status - in_progress or completed
- score - average score for the submitted answer

Scoring behavior:
- May use AI scoring if OpenAI is configured
- Falls back to local heuristic scoring otherwise
- Detailed category breakdown is available separately through history score endpoints

Language behavior:
- user-facing text is returned in the saved session language
- technical terms may remain in English even inside Hebrew responses when appropriate

Possible errors:
- 401 - missing/invalid token
- 404 - session not found
- 422 - invalid request body
- 422 - empty answer
- 400 - interview has not started yet
- 400 - interview already completed

Example 404:
{
  "detail": "Session not found"
}

---

### POST /api/v1/interviews/finish/{session_id}

Purpose:
Finish interview early and generate report immediately.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Path params:
- session_id - integer

Response 200:
{
  "session_id": 1,
  "status": "completed",
  "report_id": 3
}

Possible errors:
- 401 - missing/invalid token
- 404 - session not found

Example 404:
{
  "detail": "Session not found"
}

---

### GET /api/v1/interviews/transcript/{session_id}

Purpose:
Return full transcript for an owned session.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Path params:
- session_id - integer

Response 200:
{
  "session_id": 1,
  "status": "in_progress",
  "messages": [
    {
      "id": 1,
      "session_id": 1,
      "role": "interviewer",
      "content": "Let's start your backend interview for a junior level. First question: Explain the difference between authentication and authorization.",
      "created_at": "2026-04-17T20:10:00.000000+03:00"
    },
    {
      "id": 2,
      "session_id": 1,
      "role": "candidate",
      "content": "Authentication verifies identity, while authorization decides permissions.",
      "created_at": "2026-04-17T20:10:15.000000+03:00"
    },
    {
      "id": 3,
      "session_id": 1,
      "role": "interviewer",
      "content": "How does JWT-based authentication work in a backend system?",
      "created_at": "2026-04-17T20:10:15.500000+03:00"
    }
  ]
}

Message field meanings:
- id - message id
- session_id - parent session id
- role - interviewer or candidate
- content - message text
- created_at - timestamp

Possible errors:
- 401 - missing/invalid token
- 404 - session not found

Example 404:
{
  "detail": "Session not found"
}

---

## 5. Uploads

### POST /api/v1/uploads/project-files/{session_id}

Purpose:
Upload one file to an owned project-aware session.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Content-Type:
multipart/form-data

Path params:
- session_id - integer

Form fields:
- file - required file upload

Response 200:
{
  "id": 1,
  "session_id": 6,
  "original_name": "auth_service.py",
  "stored_path": "uploads/session_6/auth_service.py",
  "file_type": "text/x-python",
  "created_at": "2026-04-17T20:20:00.000000+03:00"
}

Field meanings:
- id - uploaded file record id
- session_id - linked session
- original_name - original client filename
- stored_path - saved local path on server
- file_type - MIME type if available
- created_at - upload timestamp

Possible errors:
- 401 - missing/invalid token
- 404 - session not found
- 422 - no file provided / invalid multipart request

Example 404:
{
  "detail": "Session not found"
}

---

### GET /api/v1/uploads/project-files/{session_id}

Purpose:
Return uploaded files for an owned session.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Path params:
- session_id - integer

Response 200:
[
  {
    "id": 1,
    "session_id": 6,
    "original_name": "auth_service.py",
    "stored_path": "uploads/session_6/auth_service.py",
    "file_type": "text/x-python",
    "created_at": "2026-04-17T20:20:00.000000+03:00"
  }
]

Possible errors:
- 401 - missing/invalid token
- 404 - session not found

Example 404:
{
  "detail": "Session not found"
}

---

## 6. Reports

### GET /api/v1/reports/{session_id}

Purpose:
Return final session report for an owned session.

Auth required:
Yes

Headers:
Authorization: Bearer <token>
Accept-Language: he | en (optional)

Path params:
- session_id - integer

Response 200:
{
  "id": 1,
  "session_id": 1,
  "summary": "Strong overall performance with clear backend understanding and good communication.",
  "strengths": "Good structure, solid terminology, and clear explanation of authentication concepts.",
  "weaknesses": "Could go deeper on edge cases, operational tradeoffs, and production-level concerns.",
  "study_plan": "Practice more advanced security flows, token lifecycle handling, and system design tradeoffs.",
  "created_at": "2026-04-17T20:30:00.000000+03:00"
}

Field meanings:
- id - report id
- session_id - linked session id
- summary - high-level result
- strengths - strengths paragraph
- weaknesses - weaknesses paragraph
- study_plan - suggested improvement plan
- created_at - report timestamp

Language behavior:
- report text is returned in the saved session language
- technical terms may remain in English when appropriate

Possible errors:
- 401 - missing/invalid token
- 404 - session not found
- 404 - report not found

Example 404:
{
  "detail": "Report not found"
}

---

## 7. History

### GET /api/v1/history/sessions

Purpose:
Return history overview for all sessions belonging to the currently authenticated user.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Response 200:
[
  {
    "id": 3,
    "track": "backend",
    "level": "junior",
    "mode": "project_aware",
    "status": "completed",
    "current_question_index": 1,
    "created_at": "2026-04-17T20:25:00.000000+03:00",
    "report_id": 7,
    "report_summary": "Strong overall performance with clear architectural reasoning.",
    "average_score": 8.25
  },
  {
    "id": 2,
    "track": "backend",
    "level": "junior",
    "mode": "leetcode",
    "status": "completed",
    "current_question_index": 1,
    "created_at": "2026-04-17T20:15:00.000000+03:00",
    "report_id": 6,
    "report_summary": "Decent performance with room to improve complexity explanations.",
    "average_score": 7.8
  }
]

Field meanings:
- id - session id
- track - interview track
- level - interview level
- mode - interview mode
- status - current session status
- current_question_index - latest question index reached
- created_at - session creation timestamp
- report_id - linked report id if exists
- report_summary - short summary from report if exists
- average_score - average across all stored score rows for that session

Possible errors:
- 401 - missing/invalid token

---

### GET /api/v1/history/scores/{session_id}

Purpose:
Return score summary and rubric/category breakdown for one owned session.

Auth required:
Yes

Headers:
Authorization: Bearer <token>

Path params:
- session_id - integer

Response 200:
{
  "session_id": 1,
  "average_score": 7.95,
  "breakdown": [
    {
      "category": "clarity",
      "score": 8.2,
      "confidence": 0.78
    },
    {
      "category": "technical_accuracy",
      "score": 8.6,
      "confidence": 0.78
    },
    {
      "category": "depth",
      "score": 7.4,
      "confidence": 0.78
    },
    {
      "category": "tradeoff_reasoning",
      "score": 7.6,
      "confidence": 0.78
    }
  ],
  "total_scores": 4
}

Possible errors:
- 401 - missing/invalid token
- 404 - session not found

Example 404:
{
  "detail": "Session not found"
}

Notes:
- breakdown is aggregated by category name
- total_scores is the number of stored score rows for that session
- categories vary by interview mode:
  - standard commonly uses:
    - clarity
    - technical_accuracy
    - depth
    - tradeoff_reasoning
  - leetcode commonly uses:
    - correctness
    - complexity_analysis
    - data_structures
    - communication
  - project_aware commonly uses:
    - architecture_reasoning
    - maintainability
    - tradeoff_reasoning
    - communication
- if AI scoring is used, the backend may currently store a simpler breakdown depending on implementation version

---

## 8. Frontend Flow Recommendation

Recommended frontend order:
1. Register user
2. Login user
3. Save JWT token
4. Call /api/v1/auth/me
5. Create session with chosen track, level, mode, language
6. Send Accept-Language header on requests for consistency
7. Optionally fetch /api/v1/sessions/ for dashboard/history
8. If mode is project_aware, upload one or more files first
9. Call /api/v1/interviews/start
10. Repeatedly call /api/v1/interviews/answer
11. Use /api/v1/interviews/transcript/{session_id} to render full chat history
12. Use /api/v1/history/scores/{session_id} to render score breakdown
13. When status becomes completed, or when user clicks finish, call /api/v1/interviews/finish/{session_id} if needed
14. Fetch final report using /api/v1/reports/{session_id}
15. Use /api/v1/history/sessions for progress/history dashboard

Notes:
- session language should be chosen at session creation time
- after session creation, the saved session language is the source of truth for interview and report text

---

## 9. Notes for Frontend

- All session-owned resources are protected and require JWT auth
- The backend currently returns plain JSON and does not use pagination
- score from /interviews/answer is the answer-level average score
- detailed score breakdown comes from /history/scores/{session_id}
- report is separate and must be fetched from /reports/{session_id}
- project_aware depends on uploaded files, but if none were uploaded, backend still starts with fallback project questions
- standard mode may return AI-generated follow-up questions if OpenAI is configured
- leetcode mode returns coding-style prompts and uses a different scoring style
- history/sessions is the recommended endpoint for dashboard cards / previous attempts / progress view
- frontend should send Accept-Language: he or en
- POST /api/v1/sessions/ should include language: "he" | "en"
- response field names do not change by language
- only string values are localized
- transcript stores the text as originally generated in the session language


