from copy import deepcopy
from fastapi import APIRouter, Request, Depends

from router.user.auth import auth_router
from config import settings


def truncate_json(json, max_len: int = 100):
    if isinstance(json, str) and max_len < len(json):
        return json[:max_len] + "(truncated)"
    if isinstance(json, dict):
        for k, v in json.items():
            json[k] = truncate_json(v, max_len)
    if isinstance(json, list):
        for i, v in enumerate(json):
            json[i] = truncate_json(v)
    return json


async def store_request_body(request: Request):
    if request.method in ("PATCH", "POST", "PUT"):
        content_type = request.headers.get("Content-Type")

        # 파일 업로드인 경우 본문을 소비하지 않게 변경
        if content_type and "multipart/form-data" in content_type:
            return

        try:
            _body = await request.json()
            body = truncate_json(deepcopy(_body))
        except:
            _body = await request.body()
            body = _body.decode()

        request.state.body = body


api_router = APIRouter(dependencies=[Depends(store_request_body)])
api_router.include_router(auth_router)


@api_router.get("/healthcheck", include_in_schema=settings.DEBUG_MODE)
def healthcheck():
    return {"status": "ok"}
