from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi import status

from src.config import settings
from src.core.errors.exceptions import CustomException


# 전역으로 익셉션 캐치하는 부분
async def general_error_handler(_: Request, e: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "internal server error: 서버 에러가 발생했습니다"},
    )


async def http_exception_handler(_: Request, e: HTTPException):
    return JSONResponse(
        status_code=e.status_code,
        content={"detail": f"{e.title}: {e.description}"},
    )


async def custom_exception_handler(_: Request, e: CustomException):
    if settings.ENV == "prod":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "internal server error: 서버 에러가 발생했습니다"},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"{e.title}: {e.description}"},
    )
