# 03 - Database Migrations with Alembic in a FastAPI Project

📌 GitHub Repository: [AI Engineer Foundation](https://github.com/aseemaggarwal89/ai-engineer-foundation)

After setting up the FastAPI project structure, the next backend concept I wanted to understand was database migration.

At the beginning, it is tempting to think:

```text
I have SQLAlchemy models.
The app can create tables.
Why do I need migrations?
```

But real backend systems change over time.

You add users.

You add authentication fields.

You add audit logs.

You add roles.

You change columns.

You add indexes.

If those database changes are not tracked properly, the application becomes difficult to run consistently across local, staging, and production environments.

That is where Alembic becomes important.

## What Alembic Does

Alembic manages versioned database schema migrations.

In simple words, it helps move the database from one known schema version to another known schema version.

It also stores the currently applied migration revision in the database using an `alembic_version` table.

That means the backend can answer:

```text
Which schema version is this database currently using?
Which migrations are available?
Which migration is the current head?
```

This is important because application code and database schema must evolve together.

## Why Manual Database Changes Are Risky

Without migrations, database changes become manual.

That creates problems:

- one developer has a column locally but another does not
- production schema is different from local schema
- rollback is unclear
- deployment depends on memory
- schema history is not visible in Git
- debugging becomes harder

For example, if the code expects a `users.email` column but the database does not have it, the application fails at runtime.

A migration makes that schema change explicit.

## Database Stack In This Project

This project currently uses:

- PostgreSQL as the application database
- SQLAlchemy 2.x
- async SQLAlchemy engine
- async SQLAlchemy sessions
- Alembic migration files
- environment-based database configuration

The relevant paths are:

```text
app/db/db.py
app/db/models/
app/alembic.ini
app/alembic/env.py
app/alembic/versions/
```

The declarative base, async engine, and async session factory live in:

```text
app/db/db.py
```

The database URL comes from application settings:

```python
settings.database_url
```

The app loads that value through:

```text
app/core/config.py
```

So Alembic and the application use the same configuration source instead of maintaining two separate database URLs.

## Actual ORM Models

The mapped SQLAlchemy ORM models currently are:

```text
UserORM
AuditORM
HealthStatus
```

They live under:

```text
app/db/models/
```

There is also a Pydantic model named:

```text
HealthResponse
```

That one is not a database table. It is an API response schema.

This distinction matters because not every Python class in the database folder is a mapped table.

## `UserORM`

`UserORM` maps to:

```text
users
```

It currently stores:

- `id`, string primary key, indexed, generated in Python with `uuid.uuid4()`
- `is_active`, boolean, non-null, Python default `True`
- `role`, SQLAlchemy enum named `user_role`, non-null, Python default `USER`
- `email`, string, non-null, unique index
- `password_hash`, string, non-null

This supports registration, login, protected routes, and role-based access.

## `AuditORM`

`AuditORM` maps to:

```text
audits
```

It currently stores:

- `id`, string primary key with length 36, generated in Python with `uuid.uuid4()`
- `event_type`, string, non-null
- `user_id`, string, non-null
- `created_at`, timezone-aware `DateTime`, non-null, server default `now()`

The current audit table stores operational authentication events, not AI prompt or model response content.

## `HealthStatus`

`HealthStatus` maps to:

```text
health_status
```

It currently stores:

- `id`, primary key
- `status`, string with length 20

This supports health-check behavior in the learning project.

## Alembic Metadata Registration

Alembic needs SQLAlchemy metadata to compare the Python models with the database schema.

The Alembic environment file is:

```text
app/alembic/env.py
```

It imports:

```python
from app.db.db import Base
from app.db.models import AuditORM, HealthStatus, UserORM
```

Then it sets:

```python
target_metadata = Base.metadata
```

This ensures the mapped models are registered before Alembic evaluates metadata.

Without importing the model modules, Alembic autogenerate may not see all tables.

## Actual Migration Chain

The current Alembic chain is linear and has one head.

The real chain is:

```text
base
-> 257ac9345cd9 initial schema
-> 51c802d33f74 add email and password hash to user
-> 9c54bce0c2e0 change audits id to uuid string
-> 77ff9f8c925d change audits id to uuid
-> 06dea7f83838 change audits id to string
```

The current head is:

```text
06dea7f83838
```

Two audit-related revisions are currently no-op placeholder revisions:

```text
9c54bce0c2e0
77ff9f8c925d
```

The final audit migration changes the existing `audits.id` column to `String(36)`.

It does not create the audit table again because the initial migration already creates `audits`.

That distinction is important.

Creating the same table twice would make an upgrade from an empty database fail.

## Migration Commands

Useful Alembic commands for this repository are:

```bash
alembic -c app/alembic.ini heads
alembic -c app/alembic.ini history
alembic -c app/alembic.ini current
alembic -c app/alembic.ini upgrade head
```

Create a new migration:

```bash
alembic -c app/alembic.ini revision --autogenerate -m "describe change"
```

Rollback one revision:

```bash
alembic -c app/alembic.ini downgrade -1
```

But rollback should not be treated as automatically safe in production.

I will explain why later in this post.

## Autogenerate Is A First Draft

Alembic autogenerate compares:

```text
SQLAlchemy MetaData
vs
the configured database schema
```

Then it creates a migration script.

This is helpful, but it is not a final migration.

Autogenerate is a first draft.

For example, Alembic may not understand the intention behind:

- column renames
- table renames
- data backfills
- destructive changes
- complex type conversions
- enum changes

A rename may appear as:

```text
drop old column
add new column
```

That could lose data if applied blindly.

So every generated migration must be reviewed.

## Async SQLAlchemy And Alembic

The application uses async SQLAlchemy at runtime.

The async engine is created with:

```python
create_async_engine(settings.database_url)
```

The session factory is:

```python
AsyncSessionLocal
```

Alembic is also configured to use an async SQLAlchemy engine in:

```text
app/alembic/env.py
```

The important detail is this:

```text
The database connection is managed through an async SQLAlchemy engine,
while Alembic migration operations run through a synchronous migration
context using connection.run_sync(...).
```

In code, the project uses:

```python
async_engine_from_config(...)
await connection.run_sync(do_run_migrations)
```

So the migration connection is async-managed, but Alembic operations still execute through the normal synchronous migration context.

That is the correct mental model.

## `create_all()` vs Alembic

Earlier, the application startup called:

```python
Base.metadata.create_all
```

That is convenient while learning, but it can hide missing migrations.

`create_all()` can create missing tables, but it does not provide controlled, versioned schema evolution.

The project now restricts `create_all()` behind an explicit local-only opt-in setting:

```text
AUTO_CREATE_TABLES=true
ENVIRONMENT=local
```

By default, startup does not create tables automatically.

The preferred flow is:

```text
run Alembic migrations
-> start application
```

This makes migrations the source of schema creation and schema evolution.

## Current Audit Persistence

The project currently persists audit events for:

- user registration
- user login

These are scheduled as FastAPI background tasks from the authentication routes.

Audit writing uses:

```text
AuditService
AuditRepository
AuditORM
```

The audit implementation currently stores:

- user ID
- event type
- created timestamp

It does not currently audit:

- protected route access
- AI summarization requests
- prompts
- raw model responses
- provider latency
- token usage

Those could be future extensions, but they are not current behavior.

## Future AI Audit Design

For future AI features, audit metadata could include:

- request ID
- user ID
- operation type
- provider
- model
- execution status
- latency
- token usage
- prompt template version
- safety outcome

But raw prompts and raw model responses should be treated carefully.

They may contain:

- secrets
- personal data
- private business information
- regulated data

If raw prompts or responses are ever stored, the design should include:

- redaction
- retention policy
- encryption
- access control
- compliance review
- clear user expectations

For now, this project does not store raw prompts or model responses in the audit table.

## Production Migration Safety

Migrations are powerful, but not every migration is safe to run blindly.

Risky examples include:

- dropping populated columns
- changing incompatible column types
- adding non-null columns without defaults or backfills
- renaming columns as drop-and-add operations
- adding uniqueness when duplicate data may already exist
- changing enum values incorrectly

Also, a downgrade is not always the safest production rollback.

For destructive migrations, a forward-fix migration can be safer than trying to downgrade.

A safer production pattern is:

```text
expand
-> deploy compatible code
-> backfill data
-> switch reads and writes
-> contract in a later migration
```

This may be more than a small learning project needs, but it is an important production concept.

## Debugging Schema Problems

Suppose the app fails with:

```text
column users.email does not exist
```

That usually means:

```text
The application code expects a newer schema,
but the database has not been migrated.
```

Useful commands:

```bash
alembic -c app/alembic.ini current
alembic -c app/alembic.ini heads
alembic -c app/alembic.ini history
alembic -c app/alembic.ini upgrade head
```

The fix may be to apply pending migrations, not to change the route or repository code.

## How This Helps AI Backends

At first, database migrations may look unrelated to AI.

But AI applications often need persistence.

For example:

- users
- audit events
- API keys
- prompt templates
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

## What I Learned

Alembic taught me that backend development is not only writing Python code.

It also means managing database change safely.

Database schema is part of the application.

If schema changes are not versioned, deployments become fragile.

For an AI backend, this matters even more because future features like RAG, feedback, prompt audit, and usage tracking all need reliable persistence.

## Next

In the next post, I will explain async programming in FastAPI.

That topic is important because this project uses async database calls, Redis calls, Ollama HTTP requests, and OpenAI API calls.
