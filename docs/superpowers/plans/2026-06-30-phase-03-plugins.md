# Phase 03 — 插件管理与菜单

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** 实现 `plugin_service` 封装 Entari 插件 API，提供 `/api/plugins/*`（list/detail/toggle/reload/config 写）与 `/api/menus`（内置 + 扩展合并）。

**Architecture:** `services/plugin_service.py` 调 `arclet.entari` 的 `get_plugins/find_plugin/enable/disable/unload/load_plugin/get_plugin_references/get_plugin_referents`；`api/plugins.py` 薄路由；`api/menus.py` 内置菜单常量。扩展菜单此 phase 仍空（phase 08 接入）。

**Tech Stack:** arclet.entari、fastapi、`EntariConfig`/`plugin_config`、`config_model_schema`。

---

## 文件结构

- Create: `src/entari_plugin_webui/services/plugin_service.py`
- Create: `src/entari_plugin_webui/api/plugins.py`
- Create: `src/entari_plugin_webui/api/menus.py`
- Modify: `src/entari_plugin_webui/api/router.py`（挂 routers）
- Create: `tests/services/test_plugin_service.py`、`tests/api/test_plugins.py`

---

## Task 3.1：plugin_service 序列化与动作

**Files:** Create `services/plugin_service.py`

- [ ] **Step 1: 测试 `tests/services/test_plugin_service.py`**（mock entari 插件对象）

```python
from __future__ import annotations

from unittest.mock import MagicMock

from entari_plugin_webui.services import plugin_service as ps


def _mk(pid="p1", available=True):
    plug = MagicMock()
    plug.id = pid
    plug.path = "mod.path"
    plug.uid = None
    plug.is_available = available
    plug.available = True
    plug.is_static = False
    plug.reusable = True
    plug.config = {"k": "v"}
    plug.subplugins = set()
    meta = MagicMock()
    meta.name = pid
    meta.version = "1.0"
    meta.description = "desc"
    meta.license = "MIT"
    meta.author = [{"name": "x"}]
    meta.urls = None
    meta.classifier = []
    meta.requirements = []
    meta.config = None
    meta.config = None
    plug.metadata = meta
    return plug


def test_serialize(monkeypatch):
    monkeypatch.setattr(ps, "get_plugin_references", lambda p: set())
    monkeypatch.setattr(ps, "get_plugin_referents", lambda p: set())
    s = ps.serialize_plugin(_mk())
    assert s["id"] == "p1"
    assert s["enabled"] is True
    assert s["configurable"] is False


def test_toggle(monkeypatch):
    p = _mk()
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    ps.toggle_plugin("p1", enable=True)
    p.enable.assert_called_once()


def test_reload(monkeypatch):
    p = _mk()
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(ps, "enable_plugin", lambda *a, **k: None)
    async def _unload(i): return True
    monkeypatch.setattr(ps, "unload_plugin_async", _unload)
    monkeypatch.setattr(ps, "load_plugin", lambda i: p)
    assert ps.reload_plugin("p1") is True


def test_update_config(monkeypatch):
    p = _mk()
    p._config_key = "p1"
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    cfg = MagicMock()
    cfg.plugin = {"p1": {}}
    cfg.save = MagicMock()
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    ps.update_plugin_config("p1", {"x": 1})
    assert cfg.plugin["p1"] == {"x": 1}
    cfg.save.assert_called_once()
```

- [ ] **Step 2: 实现 `services/plugin_service.py`**

```python
from __future__ import annotations

import asyncio
from typing import Any

from arclet.entari import (
    enable_plugin,
    find_plugin,
    get_plugin_references,
    get_plugin_referents,
    get_plugins,
    load_plugin,
    unload_plugin_async,
)
from arclet.entari.config import EntariConfig


class PluginNotFound(Exception):
    pass


def _authors(meta) -> list[str]:
    out = []
    for a in (meta.author or []):
        if isinstance(a, dict):
            out.append(a.get("name", str(a)))
        else:
            out.append(str(a))
    return out


def serialize_plugin(plug) -> dict[str, Any]:
    meta = plug.metadata
    configurable = bool(meta and getattr(meta, "config", None))
    return {
        "id": plug.id,
        "uid": plug.uid,
        "path": plug.path,
        "name": meta.name if meta else plug.id,
        "version": meta.version if meta else None,
        "description": meta.description if meta else None,
        "license": meta.license if meta else None,
        "authors": _authors(meta) if meta else [],
        "icon": meta.icon if meta else None,
        "urls": (meta.urls or {}) if meta else {},
        "classifier": (meta.classifier or []) if meta else [],
        "requirements": (meta.requirements or []) if meta else [],
        "enabled": plug.is_available,
        "available": plug.available,
        "is_static": plug.is_static,
        "reusable": plug.reusable,
        "subplugins": sorted(plug.subplugins or set()),
        "config": dict(plug.config or {}),
        "configurable": configurable,
        "references": sorted(get_plugin_references(plug)),
        "referents": sorted(get_plugin_referents(plug)),
    }


def list_plugins() -> list[dict[str, Any]]:
    return [serialize_plugin(p) for p in get_plugins()]


def get_plugin(plugin_id: str) -> dict[str, Any]:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    return serialize_plugin(plug)


def toggle_plugin(plugin_id: str, *, enable: bool) -> bool:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    plug.enable() if enable else plug.disable()
    return True


async def reload_plugin(plugin_id: str) -> bool:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    if hasattr(plug, "reload") and callable(plug.reload):
        result = plug.reload()
        if asyncio.iscoroutine(result):
            await result
        return True
    await unload_plugin_async(plugin_id)
    new = load_plugin(plugin_id)
    if new is not None:
        await enable_plugin(plugin_id)
        return True
    return False


def update_plugin_config(plugin_id: str, config: dict[str, Any]) -> None:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    key = getattr(plug, "_config_key", plugin_id)
    EntariConfig.instance.plugin[key] = config
    EntariConfig.instance.save()
```

> 注意：若 `plug._config_key` 不存在，按 `plugin_id` 兜底。`meta.config` 是配置模型类——`configurable` 用其判定。

- [ ] **Step 3:** Run `pdm run pytest tests/services/test_plugin_service.py -v` → PASS。提交 `git commit -m "feat(service): plugin_service serialization/actions"`。

---

## Task 3.2：plugins 路由

**Files:** Create `api/plugins.py`

- [ ] **Step 1: 实现**

```python
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..api.deps import require_auth
from ..services.plugin_service import PluginNotFound, get_plugin, list_plugins, reload_plugin, toggle_plugin, update_plugin_config

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
        toggle_plugin(plugin_id, enable=body.enable)
        return {"success": True, "enabled": body.enable}
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
```

> 错误结构统一：失败返回 `{"success": False, "code": ...}` + HTTP 状码。phase-11 引入中间件统一映射，本 phase 手写返回。

- [ ] **Step 2:** 挂 router（router.py 加 `app.include_router(plugins_router)`）。

- [ ] **Step 3:** Run `pdm run format && pdm run lint && pdm run typecheck`。提交 `git commit -m "feat(api): /api/plugins routes"`。

---

## Task 3.3：menus 路由

**Files:** Create `api/menus.py`

- [ ] **Step 1: 实现**

```python
from __future__ import annotations

from fastapi import APIRouter, Depends

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
    # 扩展菜单在 phase 08 注入：从 core.extension.get_all_menus() 合并
    from ..core.extension import get_all_menus  # 局部导入避免提前循环

    extension = get_all_menus()
    merged = sorted(BUILTIN_MENUS + extension, key=lambda m: m.get("order", 100))
    return {"success": True, "menus": merged}
```

> `core/extension.get_all_menus` 在 phase 08 实现；本 phase 先建 `core/extension.py` 占位返回 `[]`，phase 08 再充实。

- [ ] **Step 2: 占位 `core/extension.py`**

```python
def get_all_menus() -> list[dict]:
    return []


def get_all_extension_routes():
    return [], []
```

- [ ] **Step 3:** 挂 `menu_router`、`plugins_router` 到 `create_app`。

- [ ] **Step 4:** 提交 `git commit -m "feat(api): /api/menus (builtin + extension stubs)"`。

---

## Task 3.4：api 路由集成测试（mock service）

**Files:** Create `tests/api/test_plugins.py`

- [ ] **Step 1:** 用组件测试覆盖 list/menus（本地模式无需 cookie）

```python
def test_list_plugins(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P
    monkeypatch.setattr(P, "list_plugins", lambda: [{"id": "echo", "name": "Echo", "enabled": True}])
    r = client.get("/api/plugins")
    assert r.status_code == 200
    assert r.json()["data"][0]["id"] == "echo"


def test_toggle(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P
    called = {}
    monkeypatch.setattr(P, "toggle_plugin", lambda pid, *, enable: called.update(pid=pid, en=enable) or True)
    r = client.post("/api/plugins/echo/toggle", json={"enable": False})
    assert r.status_code == 200 and r.json()["enabled"] is False


def test_menus(client):
    r = client.get("/api/menus")
    labels = [m["label_key"] for m in r.json()["menus"]]
    assert labels == ["menu.dashboard", "menu.plugins", "menu.market", "menu.config", "menu.logs"]
```

- [ ] **Step 2:** Run → PASS。提交 `git commit -m "test(api): plugins and menus integration"`。

---

## Phase 3 完成标准

- `/api/plugins`、`/api/plugins/{id}`、`/.../toggle`、`/.../reload`、`/.../config`、`/api/menus` 可用（本地直通）
- service 层单测、api 集成测通过；ruff/pyright 全绿