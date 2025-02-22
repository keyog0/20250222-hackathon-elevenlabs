from abc import ABC, abstractmethod
import aiohttp
from typing import Dict, Any

from core.errors.exceptions import SocialLoginError


class BaseOAuth(ABC):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = ""  # 각 서비스별로 오버라이드 필요
        self.token_url = ""  # 각 서비스별로 오버라이드 필요
        self.user_info_url = ""  # 각 서비스별로 오버라이드 필요

    @abstractmethod
    async def get_auth_url(self) -> str:
        """인증 URL을 생성하는 메서드"""
        pass

    @abstractmethod
    async def get_token(self, code: str) -> Dict[str, Any]:
        """인증 코드로 액세스 토큰을 얻는 메서드"""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """액세스 토큰으로 사용자 정보를 얻는 메서드"""
        pass

    async def request_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """토큰 요청을 보내는 공통 메서드"""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data) as response:
                return await response.json()

    async def request_user_info(self, access_token: str) -> Dict[str, Any]:
        """사용자 정보 요청을 보내는 공통 메서드"""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.user_info_url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise SocialLoginError("Failed to get user info")
