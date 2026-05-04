from datetime import timedelta, datetime
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, UUID, desc
from pwdlib import PasswordHash
from typing import Annotated
from models.user import User, RefreshToken
from config import settings
from database import get_async_db
import jwt
import secrets


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now() + expires_delta
    
    else:
        expire = datetime.now() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

async def create_refresh_token(user_id: UUID, session: AsyncSession, expires_delta: timedelta | None = None) -> str:
    find_refresh_token = await get_refresh_tokens_by_user_id(session, user_id)

    token = secrets.token_hex(32)
    
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=7)

    if find_refresh_token:
        find_refresh_token.token = token
        find_refresh_token.expires_at = expire

        await session.commit()
        await session.refresh(find_refresh_token)

        return find_refresh_token.token

    refresh_token = RefreshToken(user_id=user_id, token=token, expires_at=expire)

    session.add(refresh_token)
    await session.commit()
    await session.refresh(refresh_token)

    return refresh_token.token

async def rotate_refresh_token(token: str, session: AsyncSession, expires_delta: timedelta | None = None) -> str:
    refresh_token = await get_refresh_token(session, token)

    if not refresh_token:
        raise PermissionError("Unauthorized")
    
    refresh_token.token = secrets.token_hex(32)

    if expires_delta:
        refresh_token.expires_at = datetime.now() + expires_delta
    else:
        refresh_token.expires_at = datetime.now() + timedelta(days=7)

    await session.commit()
    await session.refresh(refresh_token)

    return refresh_token.token

async def create(session: AsyncSession, user: User) -> User:
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user

async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    return user

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    return user

async def get_refresh_token(session: AsyncSession, token: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.token == token, RefreshToken.revoked_at.is_(None))
    result = await session.execute(stmt)
    refresh_token = result.scalar_one_or_none()

    return refresh_token

async def get_refresh_tokens_by_user_id(session: AsyncSession, user_id: UUID) -> RefreshToken | None:
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .order_by(desc(RefreshToken.updated_at), desc(RefreshToken.created_at), desc(RefreshToken.id))
        .limit(1)
    )
    result = await session.execute(stmt)
    refresh_token = result.scalars().first()

    return refresh_token

async def revoke_refresh_token(session: AsyncSession, token: str) -> bool:
    refresh_token = await get_refresh_token(session, token)

    if not refresh_token:
        return False

    refresh_token.revoked_at = datetime.now()

    await session.commit()

    return True

async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_async_db)],
) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub") # type: ignore

        if email is None:
            return None

    except jwt.PyJWTError:
        return None

    user = await get_user_by_email(session, email)

    if user is None:
        return None

    return user

async def get_current_active_user(current_user: Annotated[User | None, Depends(get_current_user)]) -> User | None:
    return current_user