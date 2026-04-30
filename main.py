from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings
from database import get_async_db

app = FastAPI(
    debug=settings.MODE
)

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
