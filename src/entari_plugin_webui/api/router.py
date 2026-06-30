from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

from .health import router as health_router


def create_app() -> FastAPI:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
    app = FastAPI(title="Entari WebUI", middleware=middleware)
    app.include_router(health_router)
    return app
