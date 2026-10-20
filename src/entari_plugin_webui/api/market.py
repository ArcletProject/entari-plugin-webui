from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from ..api.deps import require_auth
from ..core.error import PluginNotFound
from ..services.builtin_service import list_builtins, load_builtin, set_builtin_enabled, set_builtin_unloaded
from ..services.market_service import (
    get_plugin,
    get_task,
    list_plugins,
    start_install,
    start_uninstall,
)
from ..services.plugin_service import unload_market_plugin

router = APIRouter(prefix="/api/market", tags=["market"], dependencies=[Depends(require_auth)])


class NameBody(BaseModel):
    name: str


class ToggleBuiltinBody(BaseModel):
    enable: bool


@router.get("/builtins")
async def builtins_():
    return {"success": True, "data": list_builtins()}


@router.post("/builtins/{name}/toggle")
async def toggle_builtin(name: str, body: ToggleBuiltinBody):
    await set_builtin_enabled(name, body.enable)
    return {"success": True, "enabled": body.enable}


@router.post("/builtins/{name}/unload")
async def unload_builtin(name: str):
    await set_builtin_unloaded(name)
    return {"success": True}


@router.post("/builtins/{name}/load")
async def load_builtin_(name: str):
    return {"success": await load_builtin(name)}


@router.get("/plugins")
async def list_():
    return {"success": True, **(await list_plugins())}


@router.get("/plugins/{name}")
async def detail(name: str):
    p = await get_plugin(name)
    if p is None:
        raise PluginNotFound(name)
    return {"success": True, "data": p}


@router.post("/install")
async def install(body: NameBody):
    tid = await start_install(body.name)
    return {"success": True, "task_id": tid}


@router.post("/uninstall")
async def uninstall(body: NameBody):
    await unload_market_plugin(body.name)
    tid = await start_uninstall(body.name)
    return {"success": True, "task_id": tid}


@router.get("/tasks/{task_id}")
async def task(task_id: str):
    t = get_task(task_id)
    if t is None:
        return JSONResponse({"success": False, "code": "task_not_found"}, status_code=HTTP_404_NOT_FOUND)
    return {
        "success": True,
        "task_id": t.task_id,
        "pip_name": t.pip_name,
        "action": t.action,
        "status": t.status,
        "percent": t.percent,
        "message": t.message,
    }
