from fastapi import status, HTTPException


class InternalServerErrorException(HTTPException):
    def __init__(self, description="서버 에러가 발생했습니다"):
        self.title = "internal server error"
        self.description = description
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{title}: {description}")


class ConflictException(HTTPException):
    def __init__(self, description="예상치 못한 오류"):
        self.title = "conflict"
        self.description = description
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"{self.title}: {self.description}")


class BadRequestException(HTTPException):
    def __init__(self, description="잘못된 요청입니다."):
        self.title = "bad request"
        self.description = description
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{self.title}: {self.description}")


class NotFoundException(HTTPException):
    def __init__(self, description="해당 리소스가 없습니다."):
        self.title = "not found"
        self.description = description
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{self.title}: {self.description}")


class UnAuthorizedException(HTTPException):
    def __init__(self, description="인증되지 않은 사용자입니다."):
        self.title = "unauthorized"
        self.description = description
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"{self.title}: {self.description}")


class ForbiddenException(HTTPException):
    def __init__(self, description="권한이 없습니다."):
        self.title = "forbidden"
        self.description = description
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=f"{self.title}: {self.description}")


class ServiceUnavailableException(HTTPException):
    def __init__(self, title="service unavailable", description="서비스가 일시적으로 사용 불가한 상태입니다."):
        self.title = title
        self.description = description
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"{title}: {description}")


class CustomException(Exception):
    """커스텀 예외"""

    title: str = "custom exception"
    description: str = "예상치 못한 오류"


class PASSIdentityError(CustomException):
    """PASS 인증 관련 커스텀 예외"""

    title: str = "pass identity error"
    description: str = "PASS 인증 오류"


class SocialLoginError(CustomException):
    """소셜 로그인 관련 커스텀 예외"""

    title: str = "social login error"
    description: str = "소셜 로그인 오류"


class JWTTokenError(CustomException):
    """JWT 토큰 관련 커스텀 예외"""

    title: str = "jwt token error"
    description: str = "JWT 토큰 오류"


class CacheError(CustomException):
    """캐시 관련 커스텀 예외"""

    title: str = "cache error"
    description: str = "캐시 오류"


class DatabaseError(CustomException):
    """데이터베이스 관련 커스텀 예외"""

    title: str = "database error"
    description: str = "데이터베이스 오류"
