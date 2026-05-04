from datetime import timedelta

from httpx import AsyncClient

from services.user import create_access_token


async def register_user(
    client: AsyncClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "password123",
    full_name: str = "Test User",
):
    return await client.post(
        "/register",
        data={
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
        },
    )


async def login_user(
    client: AsyncClient,
    username: str = "testuser",
    password: str = "password123",
):
    return await client.post(
        "/login",
        data={
            "username": username,
            "password": password,
        },
    )


def build_access_token(email: str, expires_delta: timedelta | None = None) -> str:
    return create_access_token(data={"sub": email}, expires_delta=expires_delta)


def get_cookie_header(response, cookie_name: str) -> str:
    for header in response.headers.get_list("set-cookie"):
        if header.lower().startswith(f"{cookie_name}="):
            return header

    return ""