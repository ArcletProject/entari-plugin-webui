from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from ..core.error import AppError, TooManyRequests
from ..utils import logger
from .auth import router as auth_router
from .config import router as config_router
from .extensions import router as extensions_router
from .health import router as health_router
from .market import router as market_router
from .menus import router as menu_router
from .plugins import router as plugins_router
from .stats import router as stats_router

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "no-referrer",
    "X-XSS-Protection": "0",
}


async def _csrf_middleware(request: Request, call_next):
    if (
        request.method not in SAFE_METHODS
        and request.url.path.startswith("/api/")
        and not request.headers.get("x-requested-with")
        and not _same_origin(request)
    ):
        return JSONResponse({"code": "forbidden_csrf"}, status_code=403)
    return await call_next(request)


async def _security_headers_middleware(request: Request, call_next):
    resp = await call_next(request)
    for k, v in _SECURITY_HEADERS.items():
        resp.headers.setdefault(k, v)
    return resp


async def _error_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except TooManyRequests as e:
        return JSONResponse(
            {"success": False, "code": e.code, "message": e.message},
            status_code=e.status,
            headers={"Retry-After": str(e.retry_after) if e.retry_after else "60"},
        )
    except AppError as e:
        return JSONResponse({"success": False, "code": e.code, "message": e.message}, status_code=e.status)
    except HTTPException as e:
        return JSONResponse(
            {"success": False, "code": "http_error", "message": e.detail}, status_code=e.status_code, headers=e.headers
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("unhandled exception", exc_info=e)
        return JSONResponse({"success": False, "code": "internal_error", "message": str(e)}, status_code=500)


def _same_origin(request: Request) -> bool:
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        return False
    host = request.headers.get("host", "")
    try:
        from urllib.parse import urlparse

        return urlparse(origin).netloc == host
    except ValueError:
        return False


def create_app() -> FastAPI:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]
    app = FastAPI(title="Entari WebUI", middleware=middleware)
    app.middleware("http")(_csrf_middleware)
    app.middleware("http")(_security_headers_middleware)
    app.middleware("http")(_error_middleware)
    app.include_router(auth_router)
    app.include_router(config_router)
    app.include_router(extensions_router)
    app.include_router(health_router)
    app.include_router(market_router)
    app.include_router(menu_router)
    app.include_router(plugins_router)
    app.include_router(stats_router)
    return app
