# AI-Based Event Management and Scheduling Assistant (CSEAIML2026-P37)

React + FastAPI + SQLite implementation of the project report.

## Run
```
# backend
cd backend && pip install -r requirements.txt
python -m app.seed                     # demo data + trains sentiment model
uvicorn app.main:app --port 8000
# frontend (new terminal)
cd frontend && npm install && npm run dev      # http://localhost:5173
# tests
cd backend && DISABLE_JOBS=1 pytest tests -q
# screenshots (app running): cd screenshots && node capture.cjs   (needs playwright)
```
Demo logins: admin@lpu.in / Admin@123, organizer@lpu.in / Organizer@123, student@lpu.in / Student@123.

Env vars: JWT_SECRET, EVENTS_DB, SMTP_HOST/SMTP_PORT (MailHog: localhost:1025), MAIL_FROM.

## Notes
- Report names Spring Boot + MySQL. Those could not be built here (Maven Central blocked), so the API is FastAPI and the DB is SQLite with the same 12-table schema (backend/app/schema.sql).
- Sentiment model is trained on synthetic template sentences; its metrics are not real-world accuracy.
