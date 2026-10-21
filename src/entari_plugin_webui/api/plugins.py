from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from ..api.deps import require_auth
from ..services import market_service
from ..services.config_service import get_etag, get_section, report_to_dict
from ..services.plugin_service import (
    get_plugin,
    list_plugins,
    list_unloaded_plugins,
    load_unloaded,
    reload_plugin,
    toggle_plugin,
    uninstall_plugin,
    unload_plugin,
    update_plugin_config,
)

router = APIRouter(prefix="/api/plugins", tags=["plugins"], dependencies=[Depends(require_auth)])


class ToggleBody(BaseModel):
    enable: bool


class ConfigBody(BaseModel):
    config: dict


class LoadBody(BaseModel):
    key: str


@router.get("")
async def list_():
    return {"success": True, "data": list_plugins()}


@router.get("/unloaded")
async def unloaded_():
    return {"success": True, "plugins": list_unloaded_plugins()}


@router.post("/load")
async def load(body: LoadBody):
    return {"success": True, "data": await load_unloaded(body.key)}


@router.get("/{plugin_id}")
async def detail(plugin_id: str):
    data = get_plugin(plugin_id)
    data["market"] = await market_service.find_market_entry(data["id"], data["path"])
    return {"success": True, "data": data}


@router.post("/{plugin_id}/toggle")
async def toggle(plugin_id: str, body: ToggleBody):
    data = await toggle_plugin(plugin_id, enable=body.enable)
    return {"success": True, "data": data}


@router.post("/{plugin_id}/reload")
async def reload(plugin_id: str):
    ok = await reload_plugin(plugin_id)
    return {"success": ok, "data": get_plugin(plugin_id)}


@router.post("/{plugin_id}/unload")
async def unload(plugin_id: str):
    return {"success": True, "data": await unload_plugin(plugin_id)}


@router.post("/{plugin_id}/uninstall")
async def uninstall(plugin_id: str):
    task_id = await uninstall_plugin(plugin_id)
    return {"success": True, "task_id": task_id}


@router.put("/{plugin_id}/config")
async def put_config(
    plugin_id: str,
    body: ConfigBody,
    if_match: str | None = Header(default=None, alias="If-Match"),
):
    report = await update_plugin_config(plugin_id, body.config, if_match=if_match)
    section = f"plugins:{plugin_id}"
    return {
        "success": report.ok,
        "message": "已保存" if report.ok else "部分配置未生效",
        "apply": report_to_dict(report),
        "data": get_section(section),
        "etag": get_etag(),
    }
