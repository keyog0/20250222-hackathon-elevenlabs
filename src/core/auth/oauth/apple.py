from core.auth.oauth.base import BaseOAuth
from typing import Dict, Any
import jwt
import time
from urllib.parse import urlencode

from core.errors.exceptions import SocialLoginError


class AppleOAuth(BaseOAuth):
    def __init__(self, client_id: str, team_id: str, key_id: str, private_key: str, redirect_uri: str):
        super().__init__(client_id, "", redirect_uri)  # client_secret은 동적으로 생성됨
        self.team_id = team_id
        self.key_id = key_id
        self.private_key = private_key
        self.base_url = "https://appleid.apple.com/auth/authorize"
        self.token_url = "https://appleid.apple.com/auth/token"

    async def get_auth_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "name email",
            "response_mode": "form_post",
        }
        return f"{self.base_url}?{urlencode(params)}"

    async def get_token(self, code: str) -> Dict[str, Any]:
        client_secret = self._create_client_secret()
        data = {
            "client_id": self.client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        return await self.request_token(data)

    async def get_user_info(self, id_token: str) -> Dict[str, Any]:
        # 애플은 별도의 사용자 정보 엔드포인트를 제공하지 않습니다.
        # 대신 id_token을 디코딩하여 사용자 정보를 얻습니다.
        try:
            user_info = jwt.decode(id_token, options={"verify_signature": False})
            return user_info
        except jwt.DecodeError:
            raise SocialLoginError("Failed to decode Apple ID token")

    def _create_client_secret(self) -> str:
        now = int(time.time())
        payload = {
            "iss": self.team_id,
            "iat": now,
            "exp": now + 3600,  # 1시간 후 만료
            "aud": "https://appleid.apple.com",
            "sub": self.client_id,
        }
        headers = {"kid": self.key_id, "alg": "ES256"}
        return jwt.encode(payload, self.private_key, algorithm="ES256", headers=headers)
