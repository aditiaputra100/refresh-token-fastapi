from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import RefreshToken
import pytest

from tests.features.helpers import get_cookie_header, login_user, register_user


class TestRefreshToken:
    
    @pytest.mark.anyio
    async def test_refresh_token_is_none(self, client: AsyncClient):
        response = await client.post("/refresh")
        
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}
    
    @pytest.mark.anyio
    async def test_refresh_token_is_invalid(self, client: AsyncClient):
        response = await client.post("/refresh", cookies={"refresh_token": "invalidtoken"})

        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    @pytest.mark.anyio
    async def test_refresh_token_is_valid(self, client: AsyncClient, async_session: AsyncSession):
        await register_user(client)
        login_response = await login_user(client)

        assert login_response.status_code == 200
        assert login_response.json()["access_token"] is not None

        response = await client.post("/refresh")

        assert response.status_code == 200
        assert response.json()["access_token"] is not None
        assert response.json()["token_type"] == "bearer"

        refresh_token = response.cookies.get("refresh_token")

        assert refresh_token is not None

        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await async_session.execute(stmt)

        refresh_token_in_db = result.scalar_one_or_none()

        assert refresh_token_in_db is not None

        # Count the number of refresh tokens for the user
        stmt = select(RefreshToken).where(RefreshToken.user_id == refresh_token_in_db.user_id)
        result = await async_session.execute(stmt)
        refresh_tokens_for_user = result.scalars().all()

        assert len(refresh_tokens_for_user) == 1
        
    @pytest.mark.anyio
    async def test_revoke_refresh_token(self, client: AsyncClient, async_session: AsyncSession):
        await register_user(client)
        await login_user(client)

        endpoint_refresh = await client.post("/refresh")
        assert endpoint_refresh.status_code == 200

        refresh_token = endpoint_refresh.cookies.get("refresh_token")
        assert refresh_token is not None

        response = await client.post("/logout")

        assert response.status_code == 204
        assert response.cookies.get("refresh_token") is None

        stmt = select(RefreshToken)
        result = await async_session.execute(stmt)
        refresh_tokens = result.scalars().all()

        assert len(refresh_tokens) == 1
        assert refresh_tokens[0].revoked_at is not None

        new_response = await client.post("/refresh", cookies={"refresh_token": refresh_token})

        assert new_response.status_code == 401
        assert new_response.json() == {"detail": "Unauthorized"}

    @pytest.mark.anyio
    async def test_refresh_cookie_attributes(self, client: AsyncClient):
        await register_user(client)
        login_response = await login_user(client)

        cookie_header = get_cookie_header(login_response, "refresh_token")

        assert cookie_header
        assert "httponly" in cookie_header.lower()
        assert "max-age=" in cookie_header.lower()
        assert "access_token=" not in cookie_header.lower()

        refresh_response = await client.post("/refresh")
        refresh_cookie_header = get_cookie_header(refresh_response, "refresh_token")

        assert refresh_cookie_header
        assert "httponly" in refresh_cookie_header.lower()
        assert "access_token=" not in refresh_cookie_header.lower()
