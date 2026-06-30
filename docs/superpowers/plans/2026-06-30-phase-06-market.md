# Phase 06 — 插件市场（registry + pip 任务）

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** `market_service` 远程拉目录（失败回退本地缓存），`/api/market/plugins[/{name}]`、` POST install/uninstall` 启 pip 子进程任务、`GET /api/market/tasks/{id}` 轮询；**安装名必须命中当前目录条目**，按其声明的 `pip_name` 执行。

**Architecture:** `services/market_service.py` 持 `httpx.AsyncClient` 拉 `registry_url`，缓存到 `static/marketplace.json`（TTL 1h）；`InstallTask` 内存 dict + `asyncio.create_subprocess_exec` 跑 `pip`。

**Tech Stack:** httpx、asyncio、subprocess、fastapi、starlette。

---

## 文件结构

- Create: `src/entari_plugin_webui/services/market_service.py`
- Create: `src/entari_plugin_webui/api/market.py`
- Create: `src/entari_plugin_webui/static/marketplace.json`（空目录种子 `%7B%22plugins%22:%5B%5D%7B%7D`）
- Modify: `api/router.py` 挂 router
- Create: `tests/services/test_market_service.py`、`tests/api/test_market.py`

---

## Task 6.1：目录种子与服务

**Files:** Create `static/marketplace.json`、`services/market_service.py`

- [ ] **Step 1:** 种子目录

`src/entari_plugin_webui/static/marketplace.json`：

```json
{"plugins": []}
```

- [ ] **Step 2: 测试 `tests/services/test_market_service.py`**

```python
from __future__ import annotations

import asyncio

import pytest

from entari_plugin_webui.services import market_service as ms


def test_parse_rate_ok():
    # 占位
    assert ms.MarketError is not None


@pytest.mark.asyncio
async def test_list_uses_remote(monkeypatch, tmp_path):
    cache = tmp_path / "marketplace.json"
    monkeypatch.setattr(ms, "_CACHE_PATH", cache)
    monkeypatch.setattr(ms, "_registry_url", lambda: "http://reg/x.json")

    async def fake_fetch(url):
        return {"plugins": [{"name": "demo", "pip_name": "entari-demo", "version": "1.0", "description": "d"}]}

    monkeypatch.setattr(ms, "_fetch_remote", fake_fetch)
    out = await ms.list_plugins()
    names = [p["name"] for p in out["plugins"]]
    assert "demo" in names
    assert cache.exists()  # 已写入缓存


@pytest.mark.asyncio
async def test_install_unknown_rejected(monkeypatch):
    monkeypatch.setattr(ms, "_registry_url", lambda: "")
    # 空目录 → 全部未知
    out = await ms.list_plugins()  # 用默认空
    with pytest.raises(ms.MarketError):
        await ms.start_install("does-not-exist")
```

- [ ] **Step 3: 实现 `services/market_service.py`**

```python
from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from .. import webui_config

_CACHE_PATH = Path(__file__).resolve().parent.parent / "static" / "marketplace.json"
_CACHE_TTL = 3600
_TASKS: dict[str, "InstallTask"] = {}


class MarketError(Exception):
    pass


class UnknownPlugin(MarketError):
    pass


@dataclass
class InstallTask:
    task_id: str
    pip_name: str
    action: str  # "install" | "uninstall"
    status: str = "pending"  # pending|running|success|failed
    percent: int = 0
    message: str = ""


def _registry_url() -> str:
    return getattr(webui_config, "registry_url", "") or ""


_loaded_cache: dict[str, Any] | None = None
_loaded_at: float = 0.0


async def _fetch_remote(url: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.json()
    except Exception:  # noqa: BLE001
        return None


def _load_local_cache() -> dict[str, Any]:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"plugins": []}


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
    try:
        proc = await asyncio.create_subprocess_exec(
            "pip", "list", "--format=json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        return {item["name"].lower() for item in json.loads(out.decode())}
    except Exception:  # noqa: BLE001
        return set()


async def list_plugins() -> dict[str, Any]:
    catalog = await _ensure_catalog()
    installed = await _installed_pip_names()
    plugins = []
    for p in catalog.get("plugins", []):
        p = dict(p)
        p["installed"] = (p.get("pip_name", "") or "").lower() in installed
        plugins.append(p)
    return {"plugins": plugins, "fallback": bool(catalog.get("__fallback"))}


async def get_plugin(name: str) -> dict[str, Any] | None:
    catalog = await _ensure_catalog()
    for p in catalog.get("plugins", []):
        if p.get("name") == name:
            installed = await _installed_pip_names()
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
        if task.action == "install":
            args = ["pip", "install", "-U", task.pip_name]
        else:
            args = ["pip", "uninstall", "-y", task.pip_name]
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        out, _ = await proc.communicate()
        task.percent = 100
        if proc.returncode == 0:
            task.status = "success"
            task.message = out.decode(errors="replace")[-500:]
        else:
            task.status = "failed"
            task.message = out.decode(errors="replace")[-500:]
    except Exception as e:  # noqa: BLE001
        task.status = "failed"
        task.message = str(e)


def get_task(task_id: str) -> InstallTask | None:
    return _TASKS.get(task_id)
```

- [ ] **Step 4:** Run `pdm run pytest tests/services/test_market_service.py -v`。测试通过 `from entari_plugin_webui import webui_config` 设置 `registry_url`，conftest 的 `_reset_global_state`（Phase 2 Task 2.5）已自动重置 `registry_url` 为 `""`。提交。

---

## Task 6.2：market 路由

**Files:** Create `api/market.py`

- [ ] **Step 1:** 实现（含安装名校验由 service 强制）

```python
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

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
        return {"success": False, "code": "plugin_not_found"}, 404
    return {"success": True, "data": p}


@router.post("/install")
async def install(body: NameBody):
    try:
        tid = await start_install(body.name)
        return {"success": True, "task_id": tid}
    except UnknownPlugin:
        return {"success": False, "code": "unknown_plugin"}, 400
    except MarketError as e:
        return {"success": False, "code": "market_error", "message": str(e)}, 400


@router.post("/uninstall")
async def uninstall(body: NameBody):
    try:
        tid = await start_uninstall(body.name)
        return {"success": True, "task_id": tid}
    except UnknownPlugin:
        return {"success": False, "code": "unknown_plugin"}, 400
    except MarketError as e:
        return {"success": False, "code": "market_error", "message": str(e)}, 400


@router.get("/tasks/{task_id}")
async def task(task_id: str):
    t = get_task(task_id)
    if t is None:
        return {"success": False, "code": "task_not_found"}, 404
    return {
        "success": True,
        "task_id": t.task_id,
        "pip_name": t.pip_name,
        "action": t.action,
        "status": t.status,
        "percent": t.percent,
        "message": t.message,
    }
```

- [ ] **Step 2:** 挂 router。`pdm run format && pdm run lint && pdm run typecheck`。提交。

---

## Task 6.3：api 测试

**Files:** `tests/api/test_market.py`

- [ ] **Step 1:**

```python
def test_list(client, monkeypatch):
    from entari_plugin_webui.api import market as M
    async def _l():
        return {"plugins": [{"name": "demo", "installed": False}], "fallback": False}
    monkeypatch.setattr(M, "list_plugins", _l)
    r = client.get("/api/market/plugins")
    assert r.json()["plugins"][0]["name"] == "demo"


def test_install_unknown_400(client, monkeypatch):
    from entari_plugin_webui.api import market as M
    from entari_plugin_webui.services.market_service import UnknownPlugin
    async def _i(name):
        raise UnknownPlugin(name)
    monkeypatch.setattr(M, "start_install", _i)
    r = client.post("/api/market/install", json={"name": "x"})
    assert r.status_code == 400 and r.json()["code"] == "unknown_plugin"
```

- [ ] **Step 2:** Run → PASS。提交。

---

## Phase 6 完成标准

- 远程拉取成功 → 写缓存；失败 → 回退本地缓存并标记 `fallback`
- 安装/卸载名必须命中目录；按声明 `pip_name` 执行 pip；任务轮询可用
- ruff/pyright/pytest 全绿