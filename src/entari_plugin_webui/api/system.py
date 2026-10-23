from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.system_info import get_system_info
from .deps import require_auth

router = APIRouter(prefix="/api/system", tags=["system"], dependencies=[Depends(require_auth)])


@router.get("")
async def system():
    return {"success": True, **get_system_info()}
