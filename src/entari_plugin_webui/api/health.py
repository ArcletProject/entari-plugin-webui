from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])

_START = datetime.now()


@router.get("/health")
async def health() -> dict:

    frontend_built = (Path(__file__).resolve().parent.parent / "static" / "frontend" / "index.html").exists()
    return {
        "status": "ok",
        "uptime_seconds": int((datetime.now() - _START).total_seconds()),
        "frontend_built": frontend_built,
    }
