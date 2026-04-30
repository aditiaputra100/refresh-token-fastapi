from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import URL
from typing import AsyncGenerator
from config import settings

connection = settings.DATABASE.DB_CONNECTION

connections = {
    'sqlite': {
        'driver': 'sqlite+aiosqlite',
        'host': None,
        'port': None,
        'database': settings.DATABASE.DB_DATABASE or 'database.sqlite',
        'username': None,
        'password': None,
    },
    'mysql': {
        'driver': 'mysql+aiomysql',
        'host': settings.DATABASE.DB_HOST or 'localhost',
        'port': settings.DATABASE.DB_PORT or 3306,
        'database': settings.DATABASE.DB_DATABASE or 'fastapi',
        'username': settings.DATABASE.DB_USER or 'root',
        'password': settings.DATABASE.DB_PASSWORD or '',
    },
    'mariadb': {
        'driver': 'mariadb+aiomysql',
        'host': settings.DATABASE.DB_HOST or 'localhost',
        'port': settings.DATABASE.DB_PORT or 3306,
        'database': settings.DATABASE.DB_DATABASE or 'fastapi',
        'username': settings.DATABASE.DB_USER or 'root',
        'password': settings.DATABASE.DB_PASSWORD or '',
    },
    'postgresql': {
        'driver': 'postgresql+asyncpg',
        'host': settings.DATABASE.DB_HOST or 'localhost',
        'port': settings.DATABASE.DB_PORT or 5432,
        'database': settings.DATABASE.DB_DATABASE or 'fastapi',
        'username': settings.DATABASE.DB_USER or 'postgres',
        'password': settings.DATABASE.DB_PASSWORD or '',
    },
}

url = URL.create(
    drivername=connections[connection]['driver'],
    username=connections[connection]['username'],
    password=connections[connection]['password'],
    host=connections[connection]['host'],
    port=connections[connection]['port'],
    database=connections[connection]['database']
)

async_engine = create_async_engine(url, echo=settings.MODE)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
