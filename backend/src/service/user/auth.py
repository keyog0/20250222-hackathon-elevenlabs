from uuid import UUID
from fastapi import Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from core.auth.identity.pass_identity import FakePASSIdentity, PASSIdentity
from core.auth.token.cookie_manager import AccessTokenManager
from core.models.user import SocialUserModel, UserModel
from core.errors.exceptions import ForbiddenException, UnAuthorizedException
from schemas.user.auth import LoginRequest, RegisterRequest, SocialRequest, UserProfile

from config import settings

jwt_token_manager = AccessTokenManager()
pass_identity = PASSIdentity() if settings.ENV == "prod" else FakePASSIdentity()


async def _create_token(user: UserModel, is_remember: bool):
    access_token = jwt_token_manager.create_access_token(payload={"user_id": user.id, "role": user.role})
    refresh_token = jwt_token_manager.create_refresh_token(
        payload={"user_id": user.id, "role": user.role, "is_remember": is_remember}
    )

    response = Response(status_code=status.HTTP_200_OK)
    secure_config = {"httponly": True}
    if settings.ENV == "prod":
        secure_config.update({"secure": True, "samesite": "Strict"})
    response.set_cookie(key="access_token", value=access_token, **secure_config)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        **secure_config,
    )
    return response


async def login(db_session: AsyncDBSession, request: LoginRequest):
    user = await UserModel.get_user_by_email(db_session, request.email)
    if not user:
        raise ForbiddenException("존재하지 않는 계정입니다.")

    if not user.verify_password(request.password):
        raise ForbiddenException("잘못된 비밀번호입니다.")

    if user.is_locked:
        raise ForbiddenException("비밀번호를 5회 이상 틀린 경우 300초 동안 로그인이 불가능합니다.")

    if not user.is_active:
        raise ForbiddenException("비활성화된 계정입니다.")

    user.record_login()
    return await _create_token(user, request.is_remember)


async def logout():
    response = Response(status_code=status.HTTP_200_OK)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response


async def refresh_token(db_session: AsyncDBSession, refresh_token: str):
    if not jwt_token_manager.verify_token(refresh_token, is_access=False):
        raise UnAuthorizedException("유효하지 않은 토큰입니다.")

    payload = jwt_token_manager.decode_token(refresh_token, is_access=False)
    user_id = payload["user_id"]
    user = await UserModel.get_user_by_id(db_session, user_id)
    if not user:
        raise UnAuthorizedException("유효하지 않은 토큰입니다.")

    access_token = jwt_token_manager.create_access_token(
        payload={"user_id": user.id, "role": user.role, "is_social_login": False}
    )
    response = Response(status_code=status.HTTP_200_OK)
    secure_config = {"httponly": True}
    if settings.ENV == "prod":
        secure_config.update({"secure": True, "samesite": "Strict", "domain": settings.DOMAIN})
    response.set_cookie(key="access_token", value=access_token, **secure_config)
    return response


async def get_current_user_model(db_session: AsyncDBSession, access_token: str) -> UserModel:
    if not access_token:
        raise UnAuthorizedException("유효하지 않은 토큰입니다.")

    if not jwt_token_manager.verify_token(access_token):
        raise UnAuthorizedException("유효하지 않은 토큰입니다.")

    payload = jwt_token_manager.decode_token(access_token)
    user_id = payload["user_id"]

    user = await UserModel.get_user_by_id(db_session, user_id)
    if not user:
        raise ForbiddenException("존재하지 않는 계정입니다.")
    return user


async def get_current_user(db_session: AsyncDBSession, access_token: str):
    user = await get_current_user_model(db_session, access_token)
    return UserProfile(**user.profile)


async def register(db_session: AsyncDBSession, register_request: RegisterRequest):
    user = UserModel(
        **register_request.user_profile.model_dump(),
        **register_request.security.model_dump(),
        **register_request.identity_pass.model_dump(),
    )
    db_session.add(user)
    await db_session.commit()
    return user


async def get_pass_auth_url(request: Request):
    return await pass_identity.get_auth_url()


async def get_pass_user_info(request: Request, code: str):
    return await pass_identity.get_user_info(code)


async def register_social_user(db_session: AsyncDBSession, access_token: str, register_social_request: SocialRequest):
    user = await get_current_user_model(access_token)
    social_user = SocialUserModel(
        social_id=register_social_request.social_id,
        social_platform=register_social_request.social_platform,
        user_id=user.id,
    )
    db_session.add(social_user)
    await db_session.commit()
    return social_user


async def login_social_user(db_session: AsyncDBSession, social_request: SocialRequest):
    social_user = await SocialUserModel.get_user_by_social_id(
        db_session=db_session,
        social_id=social_request.social_id,
        social_platform=social_request.social_platform,
    )
    if not social_user:
        raise ForbiddenException("존재하지 않는 소셜 계정입니다.")

    user = social_user.user
    return await _create_token(user, True)
