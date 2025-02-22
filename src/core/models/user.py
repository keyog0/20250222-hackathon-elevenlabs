import uuid
from datetime import datetime, timezone

import bcrypt
from sqlalchemy import UUID, Boolean, DateTime, ForeignKey, String, Integer, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from core.models.mixin import TimeStampedMixin


class UserModel(Base, TimeStampedMixin):
    __tablename__ = "users"

    _id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid1)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    _password: Mapped[str] = mapped_column(String(60), nullable=True)
    nickname: Mapped[str] = mapped_column(String, nullable=False, index=True)
    profile_image_url: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False, index=True, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 본인인증
    name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True, index=True)
    birthdate: Mapped[str] = mapped_column(String, nullable=True)
    gender: Mapped[str] = mapped_column(String, nullable=True, index=True)
    # 관리용 필드
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_failed_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    password_changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[str] = mapped_column(String, nullable=True)
    email_verification_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    reset_password_token: Mapped[str] = mapped_column(String, nullable=True)
    reset_password_sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    # 소셜 로그인을 위한 일대다 관계
    social_accounts: Mapped[list["SocialUserModel"]] = relationship(
        "SocialUserModel", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def id(self) -> str:
        return str(self._id)

    @id.setter
    def id(self, value: str) -> None:
        self._id = uuid.UUID(value)

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self.password_changed_at = datetime.now(timezone.utc)

    def verify_password(self, value: str) -> bool:
        return bcrypt.checkpw(value.encode("utf-8"), self._password.encode("utf-8"))

    def update_password(self, value: str) -> None:
        self.password = value
        self.save()

    def record_login(self) -> None:
        self.last_login_at = datetime.now(timezone.utc)
        self.login_count += 1
        self.failed_login_attempts = 0

    def record_failed_login(self) -> None:
        self.failed_login_attempts += 1
        self.last_failed_login_at = datetime.now(timezone.utc)

    def reset_failed_login_attempts(self) -> None:
        self.failed_login_attempts = 0
        self.last_failed_login_at = None

    @property
    def is_locked(self) -> bool:
        """
        5회 이상 실패한 로그인 시도 후 300초 이내에 다시 실패한 경우 계정 잠금
        """
        if (
            self.failed_login_attempts >= 5
            and self.last_failed_login_at
            and (datetime.now(timezone.utc) - self.last_failed_login_at).total_seconds() < 300
        ):
            return True
        return False

    @property
    def profile(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "nickname": self.nickname,
            "profile_image_url": self.profile_image_url,
            "role": self.role,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
        }

    @classmethod
    async def get_user_by_email(cls, db_session, email: str) -> "UserModel":
        user = await db_session.execute(select(cls).where(cls.email == email))
        return user.scalar_one_or_none()

    @classmethod
    async def get_user_by_id(cls, db_session, user_id: str) -> "UserModel":
        user = await db_session.execute(select(cls).where(cls._id == uuid.UUID(user_id)))
        return user.scalar_one_or_none()


class SocialUserModel(Base, TimeStampedMixin):
    __tablename__ = "social_users"

    _id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid1)
    social_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    social_platform: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users._id", ondelete="CASCADE"), nullable=False, index=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user: Mapped[UserModel] = relationship("UserModel", back_populates="social_accounts")

    def record_usage(self) -> None:
        self.last_used_at = datetime.now(timezone.utc)

    @property
    def id(self) -> str:
        return str(self._id)

    @id.setter
    def id(self, value: str) -> None:
        self._id = uuid.UUID(value)

    @classmethod
    async def get_user_by_id(cls, db_session, user_id: str) -> "SocialUserModel":
        user = await db_session.execute(select(cls).where(cls._id == uuid.UUID(user_id)))
        return user.scalar_one_or_none()

    @classmethod
    async def get_user_by_social_id(cls, db_session, social_id: str, social_platform: str) -> "SocialUserModel":
        user = await db_session.execute(
            select(cls).where(cls.social_id == social_id, cls.social_platform == social_platform)
        )
        return user.scalar_one_or_none()
