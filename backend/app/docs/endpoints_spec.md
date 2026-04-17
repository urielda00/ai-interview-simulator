# Endpoints Spec

## Health
- GET /api/v1/health/
  - Purpose: server health check
  - Response: { "status": "ok" }

## Auth
- Placeholder for:
  - POST /register
  - POST /login
  - GET /me

## Sessions
- Placeholder for:
  - POST /
  - GET /{session_id}
  - GET /user/{user_id}

## Interviews
- Placeholder for:
  - POST /start
  - POST /answer
  - POST /next-question
  - POST /finish

## Reports
- Placeholder for:
  - GET /{session_id}
  - GET /user/{user_id}

## Uploads
- Placeholder for:
  - POST /project-files
  - GET /{file_id}