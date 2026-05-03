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

    async def _create_user(self, async_session: AsyncSession) -> User:
        user = User(
            id=uuid.uuid4(),
            username="john",
            email="john@example.com",
            hashed_password="hash",
            full_name="John Doe",
        )

        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user

    @pytest.mark.anyio
    async def test_create_user(self, async_session: AsyncSession):
        user = await self._create_user(async_session)

        assert user.username == "john"
        assert user.email == "john@example.com"
        assert user.hashed_password == "hash"
        assert user.full_name == "John Doe"
        assert user.id is not None
    
    @pytest.mark.anyio
    async def test_read_user(self, async_session: AsyncSession):
        created_user = await self._create_user(async_session)
        
        stmt = select(User).where(User.username == created_user.username)
        result = await async_session.execute(stmt)

        user = result.scalar_one()

        assert user.id == created_user.id
        assert user.username == created_user.username
        assert user.email == created_user.email
        assert user.hashed_password == created_user.hashed_password
    
    @pytest.mark.anyio
    async def test_read_user_not_found(self, async_session: AsyncSession): 
        stmt = select(User).where(User.username == "john")
        result = await async_session.execute(stmt)

        user = result.scalar_one_or_none()

        assert user is None
