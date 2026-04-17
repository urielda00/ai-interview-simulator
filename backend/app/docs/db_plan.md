# DB Plan

## Tables

### users
- id
- email
- password_hash
- full_name
- created_at

### interview_sessions
- id
- user_id
- track
- level
- mode
- status
- created_at

### session_messages
- id
- session_id
- role
- content
- created_at

### question_scores
- id
- session_id
- message_id
- category
- score
- confidence
- created_at

### session_reports
- id
- session_id
- summary
- strengths
- weaknesses
- study_plan
- created_at

### uploaded_files
- id
- session_id
- original_name
- stored_path
- file_type
- created_at

## Relationships
- one user -> many interview sessions
- one session -> many messages
- one session -> many scores
- one session -> one report
- one session -> many uploaded files