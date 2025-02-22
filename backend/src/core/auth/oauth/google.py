from core.auth.oauth.base import BaseOAuth
from typing import Dict, Any
import aiohttp
from urllib.parse import urlencode


class GoogleOAuth(BaseOAuth):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(client_id, client_secret, redirect_uri)
        self.base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    async def get_auth_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
        }
        return f"{self.base_url}?{urlencode(params)}"

    async def get_token(self, code: str) -> Dict[str, Any]:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        return await self.request_token(data)

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        return await self.request_user_info(access_token)

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}") as response:
                return await response.json()
