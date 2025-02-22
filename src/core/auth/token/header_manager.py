from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request
from fastapi.security import APIKeyHeader
import jwt

from config import settings


class BaseXApiKeyManager(APIKeyHeader):
    def __init__(self, name: str = "x-api-key"):
        super().__init__(name=name, auto_error=False)

        self.API_KEY_SECRET = settings.API_KEY_SECRET
        self.ALGORITHM = settings.ALGORITHM

    async def __call__(self, request: Request) -> str:
        return await super().__call__(request)

    def create_api_key(self, payload: dict[str, Any], expires_days: int = 30) -> str:
        to_encode = payload.copy()
        expires_delta = timedelta(days=expires_days)
        to_encode.update({"exp": datetime.now(timezone.utc) + expires_delta})
        encoded_jwt = jwt.encode(to_encode, self.API_KEY_SECRET, algorithm=self.ALGORITHM)
        return encoded_jwt

    def decode_api_key(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.API_KEY_SECRET, algorithms=[self.ALGORITHM])

    def verify_api_key(self, token: str) -> bool:
        payload = self.decode_api_key(token)
        if payload:
            if payload.get("exp") and payload["exp"] > datetime.now(timezone.utc).timestamp():
                return True
            elif payload.get("exp") is None:
                return True
            else:
                return False
        return False
