from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

AsyncSessionTest = async_sessionmaker(
    bind=engine_test,
    expire_on_commit=False,
)