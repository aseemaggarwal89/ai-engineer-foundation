# Backend Development – Useful Commands Cheat Sheet

This file is a **single source of truth** for running, developing, testing, and maintaining your FastAPI backend.
You should rarely need to ask again once this is in place.

---

## 🚀 Run the Application

### Development (auto-reload – nodemon equivalent)
```bash
uvicorn app.main:app --reload
```

### Development (limit reload to app directory – faster)
```bash
uvicorn app.main:app --reload --reload-dir app
```

### Production (no reload)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run tests with verbose output
```bash
pytest -v
```

### Run a single test file
```bash
pytest tests/test_auth.py
```

### Run tests with coverage
```bash
pytest --cov=app --cov-report=term-missing
```

---

## 🗄️ Database & Migrations (Alembic)

### Check current revision
```bash
alembic current
```

### Create a new migration (auto-generate)
```bash
alembic revision --autogenerate -m "migration message"
```

### Create an empty migration
```bash
alembic revision -m "manual migration"
```

### Apply all migrations (upgrade to latest)
```bash
alembic upgrade head
```

### Apply migrations up to a specific revision
```bash
alembic upgrade <revision_id>
```

### Downgrade last migration
```bash
alembic downgrade -1
```

### Downgrade to a specific revision
```bash
alembic downgrade <revision_id>
```

### Show migration history
```bash
alembic history
```

### Show verbose migration history
```bash
alembic history --verbose
```

### Stamp database with a revision (no migration run)
```bash
alembic stamp head
```

---

## 🗄️ SQL / Database Utilities

### Open database shell (PostgreSQL)
```bash
psql -h localhost -p 5432 -U <username> -d <database>
```

### Open database shell (SQLite)
```bash
sqlite3 app.db
```

### List tables (PostgreSQL)
```sql
\dt
```

### Describe table (PostgreSQL)
```sql
\d <table_name>
```

### Basic SQL checks
```sql
SELECT COUNT(*) FROM users;
SELECT * FROM users LIMIT 10;
```

### Check active connections (PostgreSQL)
```sql
SELECT pid, usename, state, query
FROM pg_stat_activity;
```

### Kill a stuck connection (PostgreSQL)
```sql
SELECT pg_terminate_backend(<pid>);
```

---

## 🧹 Code Quality

### Run flake8
```bash
flake8
```

### Run black formatter
```bash
black app tests
```

### Run isort (imports)
```bash
isort app tests
```

### Run all formatters (recommended order)
```bash
isort app tests && black app tests
```

---

## 🔍 Debugging & Inspection

### Open interactive API docs (Swagger)
```text
http://localhost:8000/docs
```

### Open ReDoc
```text
http://localhost:8000/redoc
```

### Health check endpoint
```bash
curl http://localhost:8000/health
```

---

## 🐳 Docker (If Used)

### Build image
```bash
docker build -t fastapi-app .
```

### Run container (dev)
```bash
docker run -p 8000:8000 fastapi-app
```

---

## 🤖 AI / RAG (Future – Placeholder)

### Run AI-related background workers
```bash
python -m app.workers.ai_worker
```

### Run ingestion pipeline (RAG phase)
```bash
python -m app.ingestion.run
```

---

## 🧠 Mental Mapping (Important)

| Purpose | Command |
|------|--------|
| nodemon equivalent | `uvicorn --reload` |
| start server | `uvicorn app.main:app` |
| run tests | `pytest` |
| DB migrations | `alembic upgrade head` |

---

## ✅ Recommendation

- Keep this file at project root
- Update it when adding new tools
- Treat it as **developer contract**, not notes

This file supports **Layer 1 → Layer 9**, including future **AI & RAG** work.

