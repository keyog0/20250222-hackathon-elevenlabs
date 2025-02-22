from core.auth.oauth.base import BaseOAuth
from typing import Dict, Any
from urllib.parse import urlencode
import json
import secrets

from core.errors.exceptions import SocialLoginError


class NaverOAuth(BaseOAuth):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(client_id, client_secret, redirect_uri)
        self.base_url = "https://nid.naver.com/oauth2.0/authorize"
        self.token_url = "https://nid.naver.com/oauth2.0/token"
        self.user_info_url = "https://openapi.naver.com/v1/nid/me"

    async def get_auth_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": self.generate_state(),  # 네이버는 state 파라미터를 요구합니다
        }
        return f"{self.base_url}?{urlencode(params)}"

    async def get_token(self, code: str, state: str) -> Dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "state": state,
        }
        return await self.request_token(data)

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with self.session.get(self.user_info_url, headers=headers) as response:
            response_data = await response.json()
            if response_data.get("resultcode") == "00":
                return response_data.get("response", {})
            else:
                raise SocialLoginError("Failed to get user info from Naver")

    def generate_state(self) -> str:
        return secrets.token_urlsafe(32)
