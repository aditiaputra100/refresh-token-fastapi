from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from database import Base, get_async_db
from main import app
import pytest

@pytest.fixture(scope="module")
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    if engine.dialect.name == "sqlite":
        @event.listens_for(engine.sync_engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

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

@pytest.fixture(scope="function")
async def client(async_session: AsyncSession):
    def override_get_async_db():
        yield async_session

    app.dependency_overrides[get_async_db] = override_get_async_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://tests") as ac:
        yield ac

    app.dependency_overrides.clear()