from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings
from database import get_async_db, Base, async_engine
from routes.auth import auth_router
from routes.user import user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    
    await async_engine.dispose()

app = FastAPI(
    debug=settings.MODE,
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(user_router)

@app.get('/')
def read_root():
    return {
        'message': 'Welcome to FastAPI!',
        'mode': app.debug,
        'docs': 'http://localhost:8000/docs'
    }

@app.get('/health')
async def health_check(db: Annotated[AsyncSession, Depends(get_async_db)]):
    try:
        stmt = select(1)  # Simple query to check database connection
        await db.execute(stmt)

        return {
            'status': 'healthy',
            'database': 'connected'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
