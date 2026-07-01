from __future__ import annotations

from fastapi import APIRouter, Depends

from ..api.deps import require_auth
from ..core.extension import get_all_menus, get_all_pages
from ..core.i18n import I18nRegistry
from ..core.permissions import get_permissions

router = APIRouter(prefix="/api/extensions", tags=["extensions"], dependencies=[Depends(require_auth)])


@router.get("/manifest")
async def manifest():
    return {
        "success": True,
        "menus": get_all_menus(),
        "pages": get_all_pages(),
        "i18n": I18nRegistry.all(),
        "permissions": get_permissions(),
    }
