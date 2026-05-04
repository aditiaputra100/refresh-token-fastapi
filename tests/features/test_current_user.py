from datetime import timedelta

from httpx import AsyncClient
import pytest

from tests.features.helpers import build_access_token, login_user, register_user


class TestCurrentUser:

    @pytest.mark.anyio
    async def test_get_current_user_after_login(self, client: AsyncClient):
        register_response = await register_user(client)
        access_token = register_response.json()["access_token"]

        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"

    @pytest.mark.anyio
    async def test_get_current_user_without_authorization_header(self, client: AsyncClient):
        response = await client.get("/users/me")

        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    @pytest.mark.anyio
    async def test_get_current_user_with_invalid_header_format(self, client: AsyncClient):
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Token invalid"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    @pytest.mark.anyio
    async def test_get_current_user_with_invalid_access_token(self, client: AsyncClient):
        response = await client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    @pytest.mark.anyio
    async def test_get_current_user_with_expired_access_token(self, client: AsyncClient):
        await register_user(client)

        expired_token = build_access_token("test@example.com", expires_delta=timedelta(days=-1))

        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    @pytest.mark.anyio
    async def test_refresh_returns_new_access_token(self, client: AsyncClient):
        await register_user(client)
        login_response = await login_user(client)

        assert login_response.status_code == 200
        assert login_response.json()["access_token"]

        refresh_response = await client.post("/refresh")

        assert refresh_response.status_code == 200
        assert refresh_response.json()["access_token"]
        assert refresh_response.json()["token_type"] == "bearer"

        refreshed_access_token = refresh_response.json()["access_token"]
        me_response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {refreshed_access_token}"},
        )

        assert me_response.status_code == 200
        assert me_response.json()["email"] == "test@example.com"

    @pytest.mark.anyio
    async def test_logout_revokes_refresh_token(self, client: AsyncClient):
        await register_user(client)
        login_response = await login_user(client)

        assert login_response.status_code == 200

        logout_response = await client.post("/logout")

        assert logout_response.status_code == 204

        refresh_again = await client.post("/refresh")
        assert refresh_again.status_code == 401
        assert refresh_again.json() == {"detail": "Unauthorized"}