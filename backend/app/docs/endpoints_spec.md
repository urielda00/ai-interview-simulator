# Endpoints Spec

## Health
- GET /api/v1/health/
  - Purpose: server health check
  - Response: { "status": "ok" }

## Auth

### POST /api/v1/auth/register
Creates a new user.

Request body:
{
  "email": "demo@example.com",
  "password": "123456",
  "full_name": "Demo User"
}

Response:
{
  "id": 1,
  "email": "demo@example.com",
  "full_name": "Demo User",
  "created_at": "..."
}

### GET /api/v1/auth/{user_id}
Returns a user by id.

Response:
{
  "id": 1,
  "email": "demo@example.com",
  "full_name": "Demo User",
  "created_at": "..."
}

## Sessions

### POST /api/v1/sessions/
Creates a new interview session.

Request body:
{
  "user_id": 1,
  "track": "backend",
  "level": "junior",
  "mode": "standard"
}

Response:
{
  "id": 1,
  "user_id": 1,
  "track": "backend",
  "level": "junior",
  "mode": "standard",
  "status": "created",
  "created_at": "..."
}

### GET /api/v1/sessions/{session_id}
Returns a session by id.

Response:
{
  "id": 1,
  "user_id": 1,
  "track": "backend",
  "level": "junior",
  "mode": "standard",
  "status": "created",
  "created_at": "..."
}