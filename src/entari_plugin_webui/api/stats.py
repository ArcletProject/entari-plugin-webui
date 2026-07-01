from __future__ import annotations

from fastapi import APIRouter, Depends

from ..api.deps import require_auth
from ..services.stats_service import get_stats

router = APIRouter(prefix="/api/stats", tags=["stats"], dependencies=[Depends(require_auth)])


@router.get("")
async def stats():
    return {"success": True, **(await get_stats())}
