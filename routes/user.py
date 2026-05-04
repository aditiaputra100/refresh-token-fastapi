from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from models.user import User
from database import get_async_db
from services.user import get_current_active_user
from schemas.user import UserResponse

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return current_user
