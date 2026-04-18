# Server Overview

## Purpose
Backend for AI Interview Simulator.

## Main responsibilities
- User authentication
- Interview session creation and management
- Message/question/answer persistence
- Scoring and report generation
- File upload for project-aware interviews
- Bilingual interview/report flow in English and Hebrew
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
- History
- Localization / i18n

## Localization behavior
- Frontend may send Accept-Language: he | en
- Session creation accepts a language field
- Session language is stored and used as the source of truth for the rest of the interview flow
- User-facing interview questions, follow-up questions, completion text, and reports are localized
- Technical terms may remain in English when appropriate inside Hebrew text