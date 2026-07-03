from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..api.deps import require_auth
from ..services.plugin_service import (
    get_plugin,
    list_plugins,
    reload_plugin,
    toggle_plugin,
    update_plugin_config,
)

router = APIRouter(prefix="/api/plugins", tags=["plugins"], dependencies=[Depends(require_auth)])


class ToggleBody(BaseModel):
    enable: bool


class ConfigBody(BaseModel):
    config: dict


@router.get("")
async def list_():
    return {"success": True, "data": list_plugins()}


@router.get("/{plugin_id}")
async def detail(plugin_id: str):
    return {"success": True, "data": get_plugin(plugin_id)}


@router.post("/{plugin_id}/toggle")
async def toggle(plugin_id: str, body: ToggleBody):
    success = await toggle_plugin(plugin_id, enable=body.enable)
    return {"success": success, "enabled": body.enable}


@router.post("/{plugin_id}/reload")
async def reload(plugin_id: str):
    ok = await reload_plugin(plugin_id)
    return {"success": ok}


@router.put("/{plugin_id}/config")
async def put_config(plugin_id: str, body: ConfigBody):
    update_plugin_config(plugin_id, body.config)
    return {"success": True}
