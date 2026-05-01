import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User

class TestUserModel:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        

        yield

    def test_create_model(self):
        id = uuid.uuid4()

        user = User(
            id=id, 
            username="john", 
            email="john@example.com", 
            hashed_password="hash", 
            full_name="John Doe")

        assert user.username == "john"
        assert user.email == "john@example.com"
        assert user.hashed_password == "hash"
        assert user.full_name == "John Doe"
        assert user.id == id

    @pytest.mark.anyio
    async def test_create_user(self, async_session: AsyncSession):
        user_id = uuid.uuid4()

        user = User(
            id=user_id, 
            username="john", 
            email="john@example.com", 
            hashed_password="hash", 
            full_name="John Doe")

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert user.username == "john"
        assert user.email == "john@example.com"
        assert user.hashed_password == "hash"
        assert user.full_name == "John Doe"
        assert user.id == user_id
    
    @pytest.mark.anyio
    async def test_read_user(self, async_session: AsyncSession):
        await self.test_create_user(async_session)
        
        stmt = select(User).where(User.username == "john")
        result = await async_session.execute(stmt)

        user = result.scalar_one()

        assert user.username == "john"
        assert user.email == "john@example.com"
        assert user.hashed_password == "hash"
    
    @pytest.mark.anyio
    async def test_read_user_not_found(self, async_session: AsyncSession): 
        stmt = select(User).where(User.username == "john")
        result = await async_session.execute(stmt)

        user = result.scalar_one_or_none()

        assert user is None
