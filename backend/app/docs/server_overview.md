# Server Overview

## Purpose
Backend for AI Interview Simulator.

## Main responsibilities
- User authentication
- Interview session creation and management
- Message/question/answer persistence
- Scoring and report generation
- File upload for project-aware interviews
- Future AI workflow orchestration

## Architecture
- FastAPI for API layer
- PostgreSQL for primary database
- SQLAlchemy for ORM
- Alembic for migrations
- Services layer for business logic
- Repositories layer for database access
- Workflows layer for AI interview flow

## Main domains
- Auth
- Sessions
- Interviews
- Reports
- Uploads