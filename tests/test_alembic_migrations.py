from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import Environment
from app.db.db import Base
from app.db.models import AuditORM, HealthStatus, UserORM


ALEMBIC_INI = Path("app/alembic.ini")
EXPECTED_HEAD = "06dea7f83838"
EXPECTED_TABLES = {"users", "audits", "health_status"}


def alembic_script() -> ScriptDirectory:
    return ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))


def test_alembic_revision_chain_has_single_expected_head():
    script = alembic_script()

    assert script.get_heads() == [EXPECTED_HEAD]

    revisions = list(script.walk_revisions())
    revision_ids = {revision.revision for revision in revisions}
    down_revisions = {
        revision.down_revision
        for revision in revisions
        if isinstance(revision.down_revision, str)
    }

    assert down_revisions <= revision_ids


def test_orm_models_are_registered_in_base_metadata():
    assert {UserORM.__tablename__, AuditORM.__tablename__, HealthStatus.__tablename__} == EXPECTED_TABLES
    assert EXPECTED_TABLES <= set(Base.metadata.tables)


def test_production_lifespan_does_not_run_create_all(monkeypatch):
    import app.main as app_main

    run_sync_calls = []

    class FakeConnection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def run_sync(self, fn):
            run_sync_calls.append(fn)

    class FakeEngine:
        def begin(self):
            return FakeConnection()

    class FakeContainer:
        def __init__(self, settings):
            self.settings = settings

        async def startup(self):
            return None

        async def shutdown(self):
            return None

    settings = SimpleNamespace(
        environment=Environment.PROD,
        auto_create_tables=False,
    )
    app = SimpleNamespace(state=SimpleNamespace())

    monkeypatch.setattr(app_main, "get_settings", lambda: settings)
    monkeypatch.setattr(app_main, "ServiceContainer", FakeContainer)
    monkeypatch.setattr(app_main, "engine", FakeEngine())

    async def run_lifespan():
        async with app_main.lifespan(app):
            pass

    import asyncio

    asyncio.run(run_lifespan())

    assert run_sync_calls == []
