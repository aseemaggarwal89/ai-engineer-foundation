from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

# Load settings (reads from .env)
settings = get_settings()

# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# DATABASE_URL = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'app' / 'app.db'}"

DATABASE_URL = settings.database_url
# Create async engine (PostgreSQL via asyncpg)
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

# Declarative base
Base = declarative_base()


async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that provides a transactional async DB session.
    """
    async with AsyncSessionLocal() as session:
        yield session
