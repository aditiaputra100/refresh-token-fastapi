from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID, DateTime, ForeignKey
from datetime import datetime, timedelta
from database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, unique=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str] = mapped_column(nullable=False)

    refresh_token = relationship(
        'RefreshToken', 
        backref='user', 
        cascade="all, delete-orphan", 
        uselist=False,
        lazy='joined'
    )


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True, index=True)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(nullable=False)
    expired_at: Mapped[datetime] = mapped_column(DateTime,nullable=False, default=lambda: datetime.now() + timedelta(days=7))