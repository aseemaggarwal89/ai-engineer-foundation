# Database Migrations with Alembic in a FastAPI Project

After setting up the FastAPI project structure, the next important backend concept was database migration.

In real applications, the database schema changes over time.

You may add:

- new tables
- new columns
- indexes
- constraints
- enum values
- audit tables

These changes should be tracked and applied safely.

That is where Alembic helps.

## Why Migrations Matter

Without migrations, database changes become manual and risky.

For example, imagine adding an `email` column to users.

If one developer has the column locally and another does not, the app behaves differently.

Migrations solve this by making schema changes versioned and repeatable.

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

Models live in:

```text
app/db/models/
```

Alembic files live in:

```text
app/alembic/
```

Migration versions live in:

```text
app/alembic/versions/
```

## SQLAlchemy Models

The project has models such as:

```text
UserORM
AuditORM
HealthStatus
```

These models define the shape of database tables in Python code.

Example responsibilities:

- `UserORM` stores users, email, password hash, active status, and role.
- `AuditORM` stores audit events such as user registration and login.
- `HealthStatus` supports health-check behavior.

## Alembic Migration Flow

The normal migration flow is:

```text
change SQLAlchemy model
-> generate Alembic revision
-> inspect generated migration
-> apply migration
```

Commands:

```bash
alembic -c app/alembic.ini revision --autogenerate -m "describe change"
alembic -c app/alembic.ini upgrade head
```

Rollback:

```bash
alembic -c app/alembic.ini downgrade -1
```

## Why Inspect Generated Migrations?

Autogenerate is helpful, but it should not be trusted blindly.

Before applying a migration, check:

- table names
- column types
- nullable settings
- indexes
- enum changes
- constraints
- downgrade logic

This is an important production habit.

## Async SQLAlchemy and Alembic

The application uses async SQLAlchemy at runtime.

Alembic migration code still needs to work with the database engine correctly.

This is why Alembic has its own environment file:

```text
app/alembic/env.py
```

That file controls how Alembic connects to the database and reads metadata.

## create_all vs Migrations

The app currently calls:

```python
Base.metadata.create_all
```

This is convenient for local learning.

But in production, migrations should own schema changes.

Recommended production approach:

```text
run Alembic migrations
-> start application
```

Do not rely on `create_all()` to evolve production schemas.

## Audit Table Learning

The audit table is useful because it teaches that backend systems often need to store operational events.

Examples:

- user registered
- user logged in
- admin action happened
- AI request was made

For AI systems, audit tables can later support:

- prompt audit
- model decision trace
- usage tracking
- compliance reports

## What I Learned

Alembic taught me that backend development is not only writing Python code.

It also means managing database change safely.

Schema evolution is part of production engineering.

## Next

After database migrations, the next concept was async programming in FastAPI.

