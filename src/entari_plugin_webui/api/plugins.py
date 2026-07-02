from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..api.deps import require_auth
from ..services.plugin_service import (
    PluginNotFound,
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
    try:
        return {"success": True, "data": get_plugin(plugin_id)}
    except PluginNotFound:
        return {"success": False, "code": "plugin_not_found"}, 404


@router.post("/{plugin_id}/toggle")
async def toggle(plugin_id: str, body: ToggleBody):
    try:
        success = await toggle_plugin(plugin_id, enable=body.enable)
        return {"success": success, "enabled": body.enable}
    except PluginNotFound:
        return {"success": False, "code": "plugin_not_found"}, 404


@router.post("/{plugin_id}/reload")
async def reload(plugin_id: str):
    try:
        ok = await reload_plugin(plugin_id)
        return {"success": ok}
    except PluginNotFound:
        return {"success": False, "code": "plugin_not_found"}, 404


@router.put("/{plugin_id}/config")
async def put_config(plugin_id: str, body: ConfigBody):
    try:
        update_plugin_config(plugin_id, body.config)
        return {"success": True}
    except PluginNotFound:
        return {"success": False, "code": "plugin_not_found"}, 404
