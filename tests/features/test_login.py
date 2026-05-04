from httpx import AsyncClient
import pytest

from tests.features.helpers import login_user, register_user


class TestLogin:
    
    @pytest.mark.anyio
    async def test_login_without_existing_user(self, client: AsyncClient):
        response = await login_user(client, password="testpass")
        
        assert response.status_code == 400
        assert response.json() == {"detail": "Incorrect username or password"}

    @pytest.mark.anyio
    async def test_login_with_existing_user(self, client: AsyncClient):
        await register_user(client)

        response = await login_user(client)
        
        assert response.status_code == 200
        assert response.json()["access_token"] is not None
        assert response.json()["token_type"] == "bearer"
        assert response.cookies.get("refresh_token") is not None
        assert response.cookies.get("access_token") is None

    @pytest.mark.anyio
    async def test_login_failure(self, client: AsyncClient):
        await register_user(client)

        response = await login_user(client, password="wrongpassword")
        
        assert response.status_code == 400
        assert response.json() == {"detail": "Incorrect username or password"}