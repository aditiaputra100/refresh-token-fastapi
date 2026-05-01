from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database import Base
import pytest

@pytest.fixture(scope="module")
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    yield engine

    await engine.dispose()

@pytest.fixture(scope="function")
async def async_session(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)