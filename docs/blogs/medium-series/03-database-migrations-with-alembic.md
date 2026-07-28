# 03 - Database Migrations with Alembic in a FastAPI Project

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)


After setting up the FastAPI project structure, the next important backend concept I wanted to understand was database migration.

At the beginning, it is tempting to think:

```text
I have SQLAlchemy models.
The app can create tables.
Why do I need migrations?
```

But real backend systems change over time.

You add users.

You add authentication.

You add audit logs.

You add roles.

You change columns.

You add indexes.

You fix schema mistakes.

If those database changes are not tracked properly, the application becomes difficult to run consistently across local, staging, and production environments.

That is where Alembic becomes important.



## What Problem Does Alembic Solve?

Alembic solves schema versioning.

Instead of manually changing the database, every schema change becomes a versioned migration file.

That means the database can move from one known state to another known state.

For example:

```text
initial schema
-> add audit table
-> add email and password hash to users
-> change audit id type
-> current schema
```

This is important because backend code and database schema must evolve together.

## Why Manual Database Changes Are Risky

Without migrations, database changes become manual.

That creates problems:

- one developer has a column locally but another does not
- production schema is different from local schema
- rollback is unclear
- deployment depends on memory
- schema history is not visible in Git
- debugging becomes harder

For example, imagine adding an `email` column to a users table.

If the code expects `email`, but the database does not have it, the app fails at runtime.

A migration makes that change explicit.

## Database Stack In This Project

This project uses:

- PostgreSQL
- SQLAlchemy
- async SQLAlchemy sessions
- Alembic

Database setup lives in:

```text
app/db/db.py
```

ORM models live in:

```text
app/db/models/
```

Alembic configuration lives in:

```text
app/alembic.ini
app/alembic/
```

Migration versions live in:

```text
app/alembic/versions/
```

This keeps database configuration, models, and migration history easy to find.

## SQLAlchemy Models

SQLAlchemy models define the database tables in Python.

This project has models such as:

```text
UserORM
AuditORM
HealthStatus
```

Their responsibilities are different:

- `UserORM` stores users, email, password hash, active status, and role.
- `AuditORM` stores operational events such as registration and login.
- `HealthStatus` supports health-check behavior.

These models describe the desired structure of the database.

Alembic then helps convert model changes into migration files.

## Alembic Migration Flow

The normal migration flow is:

```text
change SQLAlchemy model
-> generate Alembic revision
-> inspect generated migration
-> apply migration
-> commit migration file
```

In this project, commands use the Alembic config file inside the app folder:

```bash
alembic -c app/alembic.ini revision --autogenerate -m "describe change"
```

Then apply the migration:

```bash
alembic -c app/alembic.ini upgrade head
```

If needed, rollback one migration:

```bash
alembic -c app/alembic.ini downgrade -1
```

The migration file should be reviewed before applying it.

## Why Autogenerate Is Helpful

Alembic autogenerate compares:

```text
SQLAlchemy model metadata
vs
current database schema
```

Then it creates a migration script.

This is useful because it reduces manual migration writing.

But autogenerate is not magic.

It should be treated as a first draft.

## Always Inspect Generated Migrations

Before applying a migration, I should inspect:

- table names
- column names
- column types
- nullable settings
- default values
- indexes
- constraints
- enum changes
- downgrade logic

This is important because a wrong migration can damage production data.

For example, changing a column type may require a custom SQL expression.

Dropping a column may permanently remove data.

Autogenerate may not understand every intention.

The developer must still review the migration.

## How Alembic Finds Models

Alembic needs access to SQLAlchemy metadata.

In this project, that is configured in:

```text
app/alembic/env.py
```

The file imports the SQLAlchemy base:

```python
from app.db.db import Base
```

Then sets:

```python
target_metadata = Base.metadata
```

This tells Alembic what models exist.

The environment file also imports model classes so they are registered:

```python
from app.db.models.health import HealthStatus
from app.db.models.audit_orm import AuditORM
from app.db.models.user_orm import UserORM
```

This matters because if a model is not imported, Alembic may not see it during autogeneration.

## Async SQLAlchemy And Alembic

The application uses async SQLAlchemy at runtime.

Runtime database sessions are async because FastAPI endpoints and repositories use `async` database calls.

The database engine is created with:

```python
create_async_engine(...)
```

Alembic also needs to connect correctly to the database.

That is why `env.py` uses async migration support:

```python
async_engine_from_config(...)
```

and runs migrations through:

```python
await connection.run_sync(do_run_migrations)
```

This bridge allows Alembic to work with the async database engine while still running migration operations safely.

## `create_all()` vs Alembic

In this project, the app currently calls:

```python
Base.metadata.create_all
```

during local startup.

That is convenient while learning because it helps create missing tables quickly.

But production should not rely on `create_all()` for schema evolution.

The production approach should be:

```text
run Alembic migrations
-> start application
```

Why?

Because migrations are versioned, reviewable, and repeatable.

`create_all()` can create missing tables, but it does not manage schema changes with the same control.

It will not replace a careful migration strategy.

## Migration Files Are Part Of The Codebase

Migration files should be committed to Git.

They are not temporary files.

They explain how the database moved from one version to another.

This is important for:

- local setup
- staging deployments
- production deployments
- rollback planning
- onboarding new developers
- debugging schema issues

If the application code is versioned but the database schema is not, the backend is incomplete.

## Audit Table Learning

One useful table in this project is the audit table.

Audit logging teaches that backend systems often need to store operational events.

Examples:

- user registered
- user logged in
- admin action happened
- protected route accessed
- AI request submitted

For AI systems, audit tables can later become even more useful.

They can support:

- prompt audit
- model usage tracking
- user-level activity history
- compliance reports
- debugging workflows
- incident investigation

This connects database design with AI backend production readiness.

## How This Helps AI Backends

At first, database migrations may look unrelated to AI.

But AI applications often need persistence.

For example:

- users
- API keys
- audit logs
- prompt history
- cached metadata
- document records
- embeddings
- vector indexes
- feedback scores
- usage analytics

When I add RAG in the future, database design becomes even more important.

RAG may require tables for:

- documents
- document chunks
- embeddings
- source metadata
- retrieval logs
- answer feedback

That is why learning Alembic now is useful.

It prepares the backend for more advanced AI features later.

## Production Considerations

For production systems, I would follow these habits:

- run migrations before starting the new app version
- review generated migrations before applying them
- back up important databases before risky schema changes
- avoid destructive migrations without a rollback plan
- keep migrations small and focused
- test migrations against staging data
- document manual migration steps if needed
- monitor application errors after deployment

Database migration is part of deployment engineering.

It should not be treated as an afterthought.

## Common Debugging Scenario

Suppose the app fails with an error like:

```text
column users.email does not exist
```

That usually means:

```text
The application code expects a newer schema,
but the database has not been migrated.
```

The fix is not to change the route.

The first thing to check is:

```bash
alembic -c app/alembic.ini current
alembic -c app/alembic.ini history
```

Then apply pending migrations if needed:

```bash
alembic -c app/alembic.ini upgrade head
```

This debugging habit saves time.

## What I Learned

Alembic taught me that backend development is not only writing Python code.

It also means managing change safely.

Database schema is part of the application.

If schema changes are not versioned, deployments become fragile.

For an AI backend, this matters even more because future features like RAG, feedback, prompt audit, and usage tracking all need reliable persistence.

## Next

In the next post, I will explain async programming in FastAPI.

That topic is important because this project uses async database calls, Redis calls, Ollama HTTP requests, and OpenAI API calls.
