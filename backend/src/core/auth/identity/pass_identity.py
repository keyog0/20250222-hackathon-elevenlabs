from typing import Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import aiohttp
from loguru import logger

from config import settings
from core.errors.exceptions import PASSIdentityError


class PASSIdentity:
    def __init__(self):
        self.client_id = settings.PASS_CLIENT_ID
        self.client_secret = settings.PASS_CLIENT_SECRET
        self.redirect_uri = settings.PASS_REDIRECT_URI
        self.token_version_id = settings.PASS_TOKEN_VERSION_ID
        self.base_url = "https://svc.niceapi.co.kr:22001"

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise PASSIdentityError("PASS 인증 설정이 올바르지 않습니다.")

        # 암호화 키 생성
        salt = settings.ENCRYPTION_SALT.encode()
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(self.client_secret.encode()))
        self.cipher_suite = Fernet(key)

    async def get_auth_url(self) -> str:
        """인증 URL 생성"""
        response = await self.request_certification(self.token_version_id)
        return response["dataBody"]["token_url"]

    async def request_certification(self) -> dict[str, Any]:
        """인증 요청"""
        url = f"{self.base_url}/digital/niceid/api/v1.0/common/request/token"
        data = {
            "dataHeader": {"CNTY_CD": "ko"},
            "dataBody": {"token_version_id": self.token_version_id, "enc_mode": "1", "redirect_uri": self.redirect_uri},
        }
        return await self._make_request(url, data)

    async def get_token(self, code: str) -> dict[str, Any]:
        """인증 결과 조회"""
        url = f"{self.base_url}/digital/niceid/api/v1.0/common/result/token"
        data = {"dataHeader": {"CNTY_CD": "ko"}, "dataBody": {"token": code}}
        return await self._make_request(url, data)

    async def get_user_info(self, code: str) -> dict[str, Any]:
        """사용자 정보 조회"""
        result = await self.get_token(code)
        # PASS 인증 결과에서 필요한 사용자 정보 추출
        user_info = {
            "id": result["dataBody"].get("di"),  # 고유식별자
            "name": result["dataBody"].get("name"),
            "birthdate": result["dataBody"].get("birthdate"),
            "gender": result["dataBody"].get("gender"),
            "mobile": result["dataBody"].get("mobile_no"),
        }
        return user_info

    async def _make_request(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        """API 요청 수행"""
        headers = {"Content-Type": "application/json", "client_id": self.client_id, "client_secret": self.client_secret}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API 요청 실패: {str(e)}")
            raise PASSIdentityError(f"API 요청 실패: {str(e)}")

    def encrypt_data(self, data: str) -> str:
        """데이터 암호화"""
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"데이터 암호화 실패: {str(e)}")
            raise PASSIdentityError("데이터 암호화 실패")

    def decrypt_data(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"데이터 복호화 실패: {str(e)}")
            raise PASSIdentityError("데이터 복호화 실패")


class FakePASSIdentity:
    async def get_auth_url(self) -> str:
        return "https://svc.niceapi.co.kr:22001/digital/niceid/api/v1.0/common/request/token"

    async def get_user_info(self, code: str) -> dict[str, Any]:
        return {
            "id": "1234567890",
            "name": "홍길동",
            "birthdate": "1990-01-01",
            "gender": "male",
            "mobile": "01012345678",
        }
