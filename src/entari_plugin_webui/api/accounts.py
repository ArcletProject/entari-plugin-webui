from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.accounts import account_registry
from .deps import require_auth

router = APIRouter(prefix="/api/accounts", tags=["accounts"], dependencies=[Depends(require_auth)])


@router.get("")
async def accounts():
    return {"success": True, **account_registry.snapshot()}
