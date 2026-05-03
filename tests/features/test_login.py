from httpx import AsyncClient
from test_register import TestRegister
import pytest


class TestLogin:
    
    @pytest.mark.anyio
    async def test_login_without_existing_user(self, client: AsyncClient):
        response = await client.post(
            "/login", 
            data={"username": "testuser", "password": "testpass"})
        
        assert response.status_code == 400
        assert response.json() == {"detail": "Incorrect username or password"}

    @pytest.mark.anyio
    async def test_login_with_existing_user(self, client: AsyncClient):
        # First, register the user
        await TestRegister().test_register(client)

        # Then, attempt to log in with the registered user
        response = await client.post(
            "/login", 
            data={"username": "testuser", "password": "password123"})
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.cookies.get("refresh_token") is not None

    @pytest.mark.anyio
    async def test_login_failure(self, client: AsyncClient):
        # First, register the user
        await TestRegister().test_register(client)

        # Then, attempt to log in with the registered user
        response = await client.post(
            "/login", 
            data={"username": "testuser", "password": "wrongpassword"})
        
        assert response.status_code == 400
        assert response.json() == {"detail": "Incorrect username or password"}