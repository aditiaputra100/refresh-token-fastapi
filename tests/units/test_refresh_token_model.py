from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import RefreshToken, User
import uuid
import pytest


class TestRefreshTokenModel:
    async def _create_user(self, async_session: AsyncSession) -> User:
        user = User(
            id=uuid.uuid4(),
            username="johndoe",
            email="johndoe@example.com",
            hashed_password="hashed_password",
            full_name="John Doe",
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user

    def test_refresh_token_model(self):

        refresh_token = RefreshToken(
            token="test_token",
            user_id=uuid.uuid4(),
        )

        assert refresh_token.token == "test_token"
        assert isinstance(refresh_token.user_id, uuid.UUID)

    @pytest.mark.anyio
    async def test_create_refresh_token(self, async_session: AsyncSession):
        user = await self._create_user(async_session)
        refresh_token = RefreshToken(
            token="test_token",
            user_id=user.id,
        )

        async_session.add(refresh_token)
        await async_session.commit()
        await async_session.refresh(refresh_token)

        assert refresh_token.token == "test_token"
        assert refresh_token.user_id == user.id
        assert refresh_token.expires_at > datetime.now()

    def test_user_and_refresh_token_relationship(self):
        user_id = uuid.uuid4()

        user = User(
            id=user_id,
            username="johndoe",
            email="johndoe@example.com",
            hashed_password="hashed_password",
            full_name="John Doe",
        )

        refresh_token = RefreshToken(
            token="test_token",
            user_id=user_id,
        )

        user.refresh_token = refresh_token

        assert user.refresh_token.user_id == refresh_token.user_id
        assert user.refresh_token.token == "test_token"
    
    @pytest.mark.anyio
    async def test_create_user_and_refresh_token_relationship(self, async_session: AsyncSession):
        user = await self._create_user(async_session)

        refresh_token = RefreshToken(
            token="test_token",
            user_id=user.id,
        )

        user.refresh_token = refresh_token

        async_session.add(refresh_token)
        await async_session.commit()
        await async_session.refresh(refresh_token)

        assert refresh_token.user_id == user.id
        assert refresh_token.token == "test_token"
        assert refresh_token.expires_at > datetime.now()
