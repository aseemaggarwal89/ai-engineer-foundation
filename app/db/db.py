from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'app' / 'app.db'}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
