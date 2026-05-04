from datetime import timedelta, datetime
from fastapi import APIRouter, Cookie, Depends, HTTPException, Form, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Annotated, Literal, cast
from config import settings
from database import get_async_db
from models.user import User
from schemas.user import UserRegisteration
from services.user import (
    create,
    get_password_hash, 
    verify_password,
    create_access_token, 
    create_refresh_token,
    get_user_by_username,
    get_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token)

auth_router = APIRouter(tags=["auth"])
COOKIE_SAMESITE = cast(Literal["lax", "strict", "none"], settings.COOKIE_SAMESITE.lower())


def set_refresh_cookie(response: Response, refresh_token: str, max_age: int) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=settings.COOKIE_PATH,
    )

@auth_router.post("/register", status_code=201)
async def register(user_data: Annotated[UserRegisteration, Form()], async_session: Annotated[AsyncSession, Depends(get_async_db)], response: Response):
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )

    try:
        user = await create(async_session, new_user)

    except IntegrityError:
        await async_session.rollback()

        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    try:
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = await create_refresh_token(user.id, async_session, expires_delta=refresh_token_expires)

    except Exception:
        await async_session.rollback()

        raise HTTPException(status_code=500, detail="Failed to create refresh token")
    
    set_refresh_cookie(response, refresh_token, int(refresh_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@auth_router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], async_session: Annotated[AsyncSession, Depends(get_async_db)], response: Response):
    user = await get_user_by_username(async_session, form_data.username)

    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    try:
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = await create_refresh_token(user.id, async_session, expires_delta=refresh_token_expires)

    except Exception:
        await async_session.rollback()

        raise HTTPException(status_code=500, detail="Failed to create refresh token")
    
    set_refresh_cookie(response, refresh_token, int(refresh_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@auth_router.post(
        "/refresh")
async def refresh_token(async_session: Annotated[AsyncSession, Depends(get_async_db)], response: Response, refresh_token: Annotated[str | None, Cookie()] = None):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    find_refresh_token = await get_refresh_token(async_session, refresh_token)

    if not find_refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if find_refresh_token.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": find_refresh_token.user.email}, expires_delta=access_token_expires)

    try:
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = await rotate_refresh_token(find_refresh_token.token, async_session, expires_delta=refresh_token_expires)

    except PermissionError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    except Exception:
        await async_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to create refresh token")

    set_refresh_cookie(response, new_refresh_token, int(refresh_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": find_refresh_token.user.username,
            "email": find_refresh_token.user.email,
            "full_name": find_refresh_token.user.full_name
        }
    }

@auth_router.post(
        "/logout",
        status_code=204)
async def logout(async_session: Annotated[AsyncSession, Depends(get_async_db)], response: Response, refresh_token: Annotated[str | None, Cookie()] = None) -> None:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    revoke = await revoke_refresh_token(async_session, refresh_token)

    if not revoke:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=settings.COOKIE_PATH,
    )