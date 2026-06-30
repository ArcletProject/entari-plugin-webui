from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from entari_plugin_webui import __version__

router = APIRouter(prefix="/api", tags=["health"])

_START = datetime.utcnow()


@router.get("/health")
async def health() -> dict:
    from pathlib import Path

    frontend_built = (Path(__file__).resolve().parent.parent / "static" / "frontend" / "index.html").exists()
    return {
        "status": "ok",
        "uptime_seconds": int((datetime.utcnow() - _START).total_seconds()),
        "frontend_built": frontend_built,
    }
