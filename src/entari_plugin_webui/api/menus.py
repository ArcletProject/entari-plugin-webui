from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.extension import get_all_menus
from ..core.i18n import I18nRegistry
from .deps import require_auth

router = APIRouter(prefix="/api", tags=["menus"], dependencies=[Depends(require_auth)])

BUILTIN_MENUS = [
    {"label_key": "menu.dashboard", "icon": "mdi:view-dashboard", "path": "/", "order": 0},
    {"label_key": "menu.settings", "icon": "mdi:puzzle", "path": "/settings", "order": 10},
    {"label_key": "menu.market", "icon": "mdi:store", "path": "/market", "order": 20},
    {"label_key": "menu.logs", "icon": "mdi:console", "path": "/logs", "order": 30},
    {"label_key": "menu.chat", "icon": "mdi:chat", "path": "/chat", "order": 40},
]


@router.get("/menus")
async def menus():
    extension = get_all_menus()
    merged = sorted(BUILTIN_MENUS + extension, key=lambda m: m.get("order", 100))
    ext_i18n = I18nRegistry.get_locale("zh-CN")
    for m in merged:
        key = m.get("label_key", "")
        if key in ext_i18n:
            m["label"] = ext_i18n[key]
    return {"success": True, "menus": merged}
