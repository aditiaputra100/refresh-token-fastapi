from datetime import timedelta, datetime
from fastapi import APIRouter, Cookie, Depends, HTTPException, Form, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Annotated
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
    revoke_refresh_token)

auth_router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", refreshUrl="refresh")


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
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        max_age=int((datetime.now() + refresh_token_expires).timestamp()))
    
    return {
        "access_token": access_token,
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
    
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token, 
        httponly=True, 
        max_age=int((datetime.now() + refresh_token_expires).timestamp()))
    
    return {
        "access_token": access_token,
        "user": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@auth_router.post("/refresh")
async def refresh_token(async_session: Annotated[AsyncSession, Depends(get_async_db)], response: Response, refresh_token: Annotated[str | None, Cookie()] = None):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    find_refresh_token = await get_refresh_token(async_session, refresh_token)

    if not find_refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if find_refresh_token.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    create_access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": find_refresh_token.user.email}, expires_delta=create_access_token_expires)

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = await create_refresh_token(find_refresh_token.user_id, async_session, expires_delta=refresh_token_expires)

    response.set_cookie(
        key="refresh_token", 
        value=new_refresh_token, 
        httponly=True, 
        max_age=int((datetime.now() + refresh_token_expires).timestamp()))

    return {
        'access_token': access_token,
        'user': {
            "username": find_refresh_token.user.username,
            "email": find_refresh_token.user.email,
            "full_name": find_refresh_token.user.full_name
        }
    }

@auth_router.post("/logout", status_code=204)
async def logout(async_session: Annotated[AsyncSession, Depends(get_async_db)], response: Response, refresh_token: Annotated[str | None, Cookie()] = None) -> None:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    revoke = await revoke_refresh_token(async_session, refresh_token)

    if not revoke:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    response.delete_cookie(key="refresh_token", secure=True, httponly=True)