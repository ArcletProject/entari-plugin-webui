from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.extension import get_all_menus
from .deps import require_auth

router = APIRouter(prefix="/api", tags=["menus"], dependencies=[Depends(require_auth)])

BUILTIN_MENUS = [
    {"label_key": "menu.dashboard", "icon": "mdi:view-dashboard", "path": "/", "order": 0},
    {"label_key": "menu.plugins", "icon": "mdi:puzzle", "path": "/plugins", "order": 10},
    {"label_key": "menu.market", "icon": "mdi:store", "path": "/market", "order": 20},
    {"label_key": "menu.config", "icon": "mdi:cog", "path": "/config", "order": 30},
    {"label_key": "menu.logs", "icon": "mdi:console", "path": "/logs", "order": 40},
]


@router.get("/menus")
async def menus():
    extension = get_all_menus()
    merged = sorted(BUILTIN_MENUS + extension, key=lambda m: m.get("order", 100))
    return {"success": True, "menus": merged}
