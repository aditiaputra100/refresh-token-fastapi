from datetime import timedelta, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, UUID
from pwdlib import PasswordHash
from models.user import User, RefreshToken
from config import settings
import jwt
import secrets


password_hash = PasswordHash.recommended()

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
    stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
    result = await session.execute(stmt)
    existing_refresh_token = result.scalar_one_or_none()

    token = secrets.token_hex(32)
    
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=7)

    if existing_refresh_token:
        if existing_refresh_token.revoked_at is not None:
            raise PermissionError("Unauthorized")

        existing_refresh_token.token = token
        existing_refresh_token.expires_at = expire

        await session.commit()
        await session.refresh(existing_refresh_token)

        return existing_refresh_token.token

    refresh_token = RefreshToken(user_id=user_id, token=token, expires_at=expire)

    session.add(refresh_token)
    await session.commit()
    await session.refresh(refresh_token)

    return refresh_token.token

async def create(session: AsyncSession, user: User) -> User:
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user

async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    return user

async def get_refresh_token(session: AsyncSession, token: str) -> RefreshToken | None:
    result = await session.execute(select(RefreshToken).where(RefreshToken.token == token))
    refresh_token = result.scalar_one_or_none()

    return refresh_token

async def revoke_refresh_token(session: AsyncSession, token: str) -> bool:
    refresh_token = await get_refresh_token(session, token)

    if not refresh_token:
        return False

    refresh_token.revoked_at = datetime.now()

    await session.commit()

    return True