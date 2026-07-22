from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp
from arclet.entari import Entari

from entari_plugin_webui import webui_config

from ..core.error import MarketError, UnknownPlugin
from . import package_manager as _pm

_CACHE_PATH = Path(__file__).resolve().parent.parent / "static" / "marketplace.json"
_CACHE_TTL = 3600
_TASKS: dict[str, InstallTask] = {}

_PM: _pm.PackageManager | None = None


@dataclass
class InstallTask:
    task_id: str
    pip_name: str
    action: str
    status: str = "pending"
    percent: int = 0
    message: str = ""


def _registry_url() -> str:
    return getattr(webui_config, "registry_url", "") or ""


def _get_package_manager() -> _pm.PackageManager:
    global _PM
    if _PM is not None:
        return _PM
    override = getattr(webui_config, "package_manager", "") or ""
    if override and override in _pm.PM_INSTALL_CMD:
        exe = __import__("shutil").which(override) or __import__("sys").executable
        _PM = _pm.PackageManager(name=override, executable=exe)
    else:
        _PM = _pm.detect_package_manager()
    return _PM


_loaded_cache: dict[str, Any] | None = None
_loaded_at: float = 0.0


async def _fetch_remote(url: str) -> dict[str, Any] | None:
    try:
        app = Entari.current()
        async with app.http.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status()
            return await response.json()
    except (LookupError, RuntimeError, ValueError):
        try:
            async with (
                aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session,
                session.get(url) as response,
            ):
                response.raise_for_status()
                return await response.json()
        except Exception:  # noqa: BLE001
            return None
    except Exception:  # noqa: BLE001
        return None


def _load_local_cache() -> dict[str, Any]:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"plugins": {}}


def _save_local_cache(data: dict[str, Any]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False), "utf-8")


async def _ensure_catalog() -> dict[str, Any]:
    global _loaded_cache, _loaded_at
    now = time.time()
    if _loaded_cache is not None and now - _loaded_at < _CACHE_TTL:
        return _loaded_cache
    url = _registry_url()
    data: dict[str, Any] | None = None
    if url:
        data = await _fetch_remote(url)
        if data is not None:
            _save_local_cache(data)
    if data is None:
        data = _load_local_cache()
        data["__fallback"] = True
    _loaded_cache = data
    _loaded_at = now
    return data


async def _installed_pip_names() -> set[str]:
    return await _pm.list_installed(_get_package_manager())


async def list_plugins() -> dict[str, Any]:
    catalog = await _ensure_catalog()
    installed = await _installed_pip_names()
    plugins = []
    for p in catalog.get("plugins", {}).values():
        p = dict(p)
        p["installed"] = (p.get("pip_name", "") or "").lower() in installed
        plugins.append(p)
    return {"plugins": plugins, "fallback": bool(catalog.get("__fallback"))}


async def get_plugin(name: str) -> dict[str, Any] | None:
    catalog = await _ensure_catalog()
    installed = await _installed_pip_names()
    for p in catalog.get("plugins", {}).values():
        if p.get("name") == name:
            out = dict(p)
            out["installed"] = (p.get("pip_name", "") or "").lower() in installed
            return out
    return None


async def _lookup(name: str) -> dict[str, Any]:
    p = await get_plugin(name)
    if p is None:
        raise UnknownPlugin(name)
    return p


async def start_install(name: str) -> str:
    p = await _lookup(name)
    return _spawn(p["pip_name"], "install")


async def start_uninstall(name: str) -> str:
    p = await _lookup(name)
    if not p.get("installed"):
        raise MarketError("not_installed")
    return _spawn(p["pip_name"], "uninstall")


def _spawn(pip_name: str, action: str) -> str:
    tid = uuid.uuid4().hex
    task = InstallTask(task_id=tid, pip_name=pip_name, action=action)
    _TASKS[tid] = task
    asyncio.create_task(_run(task))
    return tid


async def _run(task: InstallTask) -> None:
    task.status = "running"
    task.percent = 10
    try:
        pm_ = _get_package_manager()
        rc, out = await _pm.run_action(pm_, task.action, task.pip_name)
        task.percent = 100
        if rc == 0:
            task.status = "success"
        else:
            task.status = "failed"
        task.message = out[-500:]
    except Exception as e:  # noqa: BLE001
        task.status = "failed"
        task.message = str(e)


def get_task(task_id: str) -> InstallTask | None:
    return _TASKS.get(task_id)
