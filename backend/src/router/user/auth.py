from fastapi import APIRouter, Body, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from core.auth.token.cookie_manager import AccessTokenManager, RefreshTokenManager
from core.database import get_async_session
from service.user import auth as auth_service
from schemas.user.auth import LoginRequest, UserProfile

auth_router = APIRouter(prefix="/auth", tags=["계정 및 인증"])


@auth_router.post("/login", response_class=Response)
async def login(
    db_session: AsyncDBSession = Depends(get_async_session),
    login_request: LoginRequest = Body(..., description="로그인 요청"),
):
    return await auth_service.login(db_session, login_request)


@auth_router.post("/logout", response_class=Response)
async def logout(request: Request, access_token: str = Depends(AccessTokenManager())):
    return await auth_service.logout()


@auth_router.post("/refresh", response_class=Response)
async def refresh_token(
    refresh_token: str = Depends(RefreshTokenManager()),
    db_session: AsyncDBSession = Depends(get_async_session),
):
    return await auth_service.refresh_token(db_session, refresh_token)


@auth_router.get("/me", response_model=UserProfile)
async def get_user_info(
    access_token: str = Depends(AccessTokenManager()),
    db_session: AsyncDBSession = Depends(get_async_session),
):
    return await auth_service.get_current_user(db_session, access_token)
