from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from .auth import router as auth_router
from .config import router as config_router
from .health import router as health_router
from .menus import router as menu_router
from .plugins import router as plugins_router
from .stats import router as stats_router

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
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
    app.include_router(auth_router)
    app.include_router(config_router)
    app.include_router(health_router)
    app.include_router(menu_router)
    app.include_router(plugins_router)
    app.include_router(stats_router)
    return app
