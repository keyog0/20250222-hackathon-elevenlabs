from fastapi import Request
from fastapi.security import APIKeyCookie
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any

from config import settings


class BaseTokenManager(APIKeyCookie):
    def __init__(self, name: str = "api-key"):
        super().__init__(name=name, auto_error=False)

        self.ACCESS_TOKEN_SECRET = settings.ACCESS_TOKEN_SECRET
        self.REFRESH_TOKEN_SECRET = settings.REFRESH_TOKEN_SECRET
        self.ALGORITHM = settings.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

    async def __call__(self, request: Request) -> str:
        return await super().__call__(request)

    def create_access_token(self, payload: dict[str, Any]) -> str:
        return self._create_token(
            payload, self.ACCESS_TOKEN_SECRET, timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    def create_refresh_token(self, payload: dict[str, Any]) -> str:
        return self._create_token(payload, self.REFRESH_TOKEN_SECRET, timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS))

    def _create_token(self, payload: dict[str, Any], secret: str, expires_delta: timedelta) -> str:
        to_encode = payload.copy()
        to_encode.update({"exp": datetime.now(timezone.utc) + expires_delta})
        encoded_jwt = jwt.encode(to_encode, secret, algorithm=self.ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str, is_access: bool = True) -> dict[str, Any]:
        try:
            secret = self.ACCESS_TOKEN_SECRET if is_access else self.REFRESH_TOKEN_SECRET
            payload = jwt.decode(token, secret, algorithms=[self.ALGORITHM], options={"require": ["exp"]})
            return payload
        except jwt.PyJWTError:
            return None

    def verify_token(self, token: str, is_access: bool = True) -> bool:
        payload = self.decode_token(token, is_access)
        if payload and payload["exp"] > datetime.now(timezone.utc).timestamp():
            return True
        return False


class AccessTokenManager(BaseTokenManager):
    def __init__(self, name: str = "access_token"):
        super().__init__(name=name)


class RefreshTokenManager(BaseTokenManager):
    def __init__(self, name: str = "refresh_token"):
        super().__init__(name=name)
