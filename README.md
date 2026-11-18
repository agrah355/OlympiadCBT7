# OlympiadCBT

A runnable full-stack MVP for NSEP / NSEC / NSEA-style computer-based practice.

## Features

- Next.js + Tailwind student dashboard, subject filters, test catalog and attempt history.
- 120-minute configurable countdown, question palette, answer selection, clear response, mark-for-review, previous/next and auto-submit.
- KaTeX rendering for `$...$` inline and `$$...$$` display math.
- FastAPI API with SQLAlchemy persistence (SQLite by default; PostgreSQL URL supported).
- Admin paper creation, PDF text extraction, CSV/PDF answer-key import, question editing, answer verification and publish gate.
- Deterministic OCR-glyph normalization for common physics/chemistry/math symbols and conservative MCQ boundary parsing.
- Instant scoring (+3 / -1 defaults), accuracy, percentage and question-by-question review.

## Run locally

Requirements: Docker Desktop, or Python 3.12+ and Node.js 20+.

### Docker (easiest)

```bash
cp .env.example .env
# Edit ADMIN_KEY in .env before exposing the app.
docker compose up --build
```

Open http://localhost:3000. API docs: http://localhost:8000/docs.

### Run without Docker

Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

On Windows PowerShell set the environment variable with `$env:NEXT_PUBLIC_API_URL="http://localhost:8000"` before `npm run dev`.

## First use

A demo Physics paper is seeded automatically by the Docker image and by `python seed.py`. Start it from the dashboard. To ingest a real paper, open **Admin**, enter the API key (default local-only key: `change-me-admin-key`), create a paper, upload the question PDF and answer key CSV/PDF, then edit and verify each parsed question. Mark each question as reviewed, ensure its answer is set, and publish.

CSV answer key format (header optional):

```csv
question,answer
1,B
2,D
3,A
```

## API overview

- `GET /api/papers[?subject=Physics]`
- `GET /api/papers/{paper_id}` (student-safe; no answer key)
- `POST /api/admin/papers`
- `POST /api/admin/papers/{id}/upload-pdf`
- `POST /api/admin/papers/{id}/upload-key`
- `GET /api/admin/papers`
- `PUT /api/admin/questions/{question_id}`
- `POST /api/admin/papers/{id}/publish`
- `POST /api/attempts/{paper_id}/submit`
- `GET /api/attempts?student=Student`

Admin endpoints require `X-Admin-Key` matching `ADMIN_KEY`.

## Important production notes / limitations

This is a functional starter, not a production exam service. PDF parsing is heuristic and intentionally creates drafts: complex layouts, multi-column papers, diagrams, tables, handwritten scans, and unusual OCR substitutions need human verification. PyMuPDF extracts embedded text; scanned PDFs need an OCR stage (for example Tesseract) before this parser. The glyph map handles common symbols but does not infer arbitrary corrupted characters. No LLM auto-reconstruction is enabled: inventing a symbol or equation can change the scientific meaning, so the review screen is the correctness gate. A production LLM adapter should return proposed edits with confidence and preserve the source text for audit.

The demo student identity is a name field, not secure authentication. Before real deployment add student/admin authentication, per-user authorization, rate limiting, CSRF/security headers, audit logs, immutable published-paper versions, backups, server-side exam session deadlines, idempotent submission, and monitoring. Use PostgreSQL in production and configure `DATABASE_URL`; install the matching PostgreSQL driver (for example `psycopg[binary]`). Also configure a real secret `ADMIN_KEY`, HTTPS, and an explicit CORS allowlist.
