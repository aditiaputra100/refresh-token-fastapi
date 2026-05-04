from httpx import AsyncClient
import pytest

from tests.features.helpers import register_user

class TestRegister:

    @pytest.mark.anyio
    async def test_register(self, client: AsyncClient):
        response = await register_user(client)

        assert response.status_code == 201
        assert response.json()["access_token"] is not None
        assert response.json()["token_type"] == "bearer"
        assert response.cookies.get("refresh_token") is not None
        assert response.json()["user"]["email"] == "test@example.com"

    @pytest.mark.anyio
    async def test_register_validation_error(self, client: AsyncClient):
        response = await client.post("/register", data={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Test User"
        })

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_existing_user(self, client: AsyncClient):
        await register_user(client)

        response = await register_user(client)

        assert response.status_code == 400
        assert response.json()["detail"] == "User with this email or username already exists"