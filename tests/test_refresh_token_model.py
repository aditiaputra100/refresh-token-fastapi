from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import RefreshToken, User
import uuid
import pytest


class TestRefreshTokenModel:
    def test_refresh_token_model(self):

        refresh_token = RefreshToken(
            token="test_token",
            user_id=1,
        )

        assert refresh_token.token == "test_token"
        assert refresh_token.user_id == 1

    @pytest.mark.anyio
    async def test_create_refresh_token(self, async_session: AsyncSession):
        expired_at = datetime.now() + timedelta(days=6)
        user_id = uuid.uuid4()


        refresh_token = RefreshToken(
            token="test_token",
            user_id=user_id,
        )

        async_session.add(refresh_token)
        await async_session.commit()
        await async_session.refresh(refresh_token)

        assert refresh_token.token == "test_token"
        assert refresh_token.user_id == user_id
        assert refresh_token.expired_at >= expired_at

    def test_user_and_refresh_token_relationship(self):
        user_id = uuid.uuid4()

        user = User(
            id=user_id,
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
    async def test_crete_user_and_refresh_token_relationship(self, async_session: AsyncSession):
        user_id = uuid.uuid4()
        expired_at = datetime.now() + timedelta(days=6)

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

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert user.refresh_token.user_id == refresh_token.user_id
        assert user.refresh_token.token == "test_token"
        assert user.refresh_token.expired_at >= expired_at
