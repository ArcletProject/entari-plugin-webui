from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from ..api.deps import require_auth
from ..services.market_service import (
    MarketError,
    UnknownPlugin,
    get_plugin,
    get_task,
    list_plugins,
    start_install,
    start_uninstall,
)

router = APIRouter(prefix="/api/market", tags=["market"], dependencies=[Depends(require_auth)])


class NameBody(BaseModel):
    name: str


@router.get("/plugins")
async def list_():
    return {"success": True, **(await list_plugins())}


@router.get("/plugins/{name}")
async def detail(name: str):
    p = await get_plugin(name)
    if p is None:
        return JSONResponse({"success": False, "code": "plugin_not_found"}, status_code=HTTP_404_NOT_FOUND)
    return {"success": True, "data": p}


@router.post("/install")
async def install(body: NameBody):
    try:
        tid = await start_install(body.name)
        return {"success": True, "task_id": tid}
    except UnknownPlugin:
        return JSONResponse({"success": False, "code": "unknown_plugin"}, status_code=HTTP_400_BAD_REQUEST)
    except MarketError as e:
        return JSONResponse(
            {"success": False, "code": "market_error", "message": str(e)},
            status_code=HTTP_400_BAD_REQUEST,
        )


@router.post("/uninstall")
async def uninstall(body: NameBody):
    try:
        tid = await start_uninstall(body.name)
        return {"success": True, "task_id": tid}
    except UnknownPlugin:
        return JSONResponse({"success": False, "code": "unknown_plugin"}, status_code=HTTP_400_BAD_REQUEST)
    except MarketError as e:
        return JSONResponse(
            {"success": False, "code": "market_error", "message": str(e)},
            status_code=HTTP_400_BAD_REQUEST,
        )


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
