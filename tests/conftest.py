# flake8: noqa

import sys
from pathlib import Path

# 🔴 MUST BE FIRST
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.db import engine_test, AsyncSessionTest
from app.db.db import Base


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_database():
    # Create tables once for the test session
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine_test.dispose()


@pytest_asyncio.fixture
async def get_db_session() -> AsyncSession:
    async with AsyncSessionTest() as session:
        async with session.begin():
            yield session
            # transaction automatically rolled back