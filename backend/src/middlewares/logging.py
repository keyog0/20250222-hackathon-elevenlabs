import http
import logging
import time
import urllib.parse

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# ANSI 이스케이프 코드
RESET = "\033[0m"
COLORS = {
    "Grey": "\033[90m",  # Grey
    "Magenta": "\033[95m",  # Magenta
    "Blue": "\033[94m",  # Blue
    "Cyan": "\033[96m",  # Cyan
    "Green": "\033[92m",  # Green
    "Red": "\033[91m",  # Red
    "Yellow": "\033[93m",  # Yellow
    "White": "\033[97m",  # White
}

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/healthcheck", "/docs", "/openapi.json"]:
            return await call_next(request)
        if request.url.path.startswith("/videos") and request.url.path.endswith(".mp4"):
            return await call_next(request)
        if request.url.path.startswith("/dashboard"):
            return await call_next(request)

        log_time = f"[{COLORS['Grey']}{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{RESET}] "

        body = await request.body()
        if body:
            request._body = body  # type: ignore

        if request.headers.get("content-type") == "application/json":
            try:
                rbody = body.decode("utf-8").replace("\n", "").replace(" ", "")
            except UnicodeDecodeError:
                rbody = body
        else:
            rbody = "streaming body"

        query_params = (
            f"{COLORS['White']}params: {urllib.parse.unquote(str(request.query_params))}{RESET} | "
            if request.query_params
            else ""
        )
        request_id = f"{COLORS['White']}requestId: {request.headers.get('X-Amzn-Trace-Id') or request.headers.get('X-Request-Id')}"
        request_body = f"{COLORS['White']}body: {urllib.parse.unquote(rbody)}{RESET} | " if body else ""
        referer = f"{COLORS['White']}referer: {urllib.parse.unquote(request.headers.get('referer', '-'))}{RESET} | "
        client = f"{COLORS['Magenta']}client: {request.client.host}{RESET} "

        method_color = {
            "GET": COLORS["Blue"],
            "POST": COLORS["Green"],
            "PUT": COLORS["Yellow"],
            "PATCH": COLORS["Yellow"],
            "DELETE": COLORS["Red"],
        }.get(request.method, COLORS["White"])

        method = f"{method_color}{request.method}{RESET} "
        endpoint = f"{COLORS['White']}{urllib.parse.unquote(request.url.path)}{RESET} "

        detail_message = "".join([method, endpoint, query_params, request_body, referer, client, request_id])
        request_message = f"{log_time}{COLORS['Yellow']}[Req] <- {RESET}{detail_message}"
        logger.info(request_message)

        start_time = time.time()

        # 요청 본문을 읽기 위해 스트림을 다시 설정
        response = await call_next(request)
        end_time = time.time()
        elapsed_time = end_time - start_time

        # 로그 메시지 포맷
        log_time = f"[{COLORS['Grey']}{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{RESET}] "
        status_code_colours = {
            1: COLORS["White"],
            2: COLORS["Green"],
            3: COLORS["Yellow"],
            4: COLORS["Red"],
            5: COLORS["Red"],
        }
        status_color = status_code_colours.get(response.status_code // 100, COLORS["White"])
        status_phrase = http.HTTPStatus(response.status_code).phrase
        status = f"{status_color}{response.status_code} {status_phrase}{RESET} "

        elapsed = f" {COLORS['Cyan']}{elapsed_time:.2f}s{RESET} "

        log_message = f"{log_time}{COLORS['Cyan']}[Res] -> {RESET}{method}{endpoint}{status}{elapsed}{request_id}"
        # 로깅
        logger.info(log_message)
        return response
