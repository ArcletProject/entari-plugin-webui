# Phase 08 — 扩展 API（增强版）

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** `WebUIExtension` 注册中心（菜单/HTTP/WS/i18n/权限/页面），公开 `webui_extend(plugin_id)`；startup 真正挂载 WS 路由（修复原版漏挂）；`/api/extensions/manifest` 下发聚合；`I18nRegistry`/`PermissionsRegistry` 合并扩展词条与权限。

**Architecture:** `core/extension.py` 持按 plugin id 的 `WebUIExtension`；`core/i18n.py`、`core/permissions.py` 注册表；`api/extensions.py` 路由；`__init__.py` startup 挂 WS。

**Tech Stack:** fastapi、dataclasses、entari_plugin_server `add_route`/`add_websocket_route`。

---

## 文件结构

- Modify/Replace: `src/entari_plugin_webui/core/extension.py`
- Create: `src/entari_plugin_webui/core/i18n.py`
- Create: `src/entari_plugin_webui/core/permissions.py`
- Create: `src/entari_plugin_webui/api/extensions.py`
- Modify: `__init__.py`（startup 挂 WS、导出公开符号）
- Modify: `api/menus.py` 使用真实 `get_all_menus`
- Create: `tests/core/test_extension.py`、`tests/api/test_extensions.py`

---

## Task 8.1：WebUIExtension 注册中心

**Files:** Replace `core/extension.py`

- [ ] **Step 1: 测试 `tests/core/test_extension.py`**

```python
from entari_plugin_webui.core.extension import (
    WebUIExtension,
    clear_extensions,
    get_all_menus,
    get_all_extension_routes,
    webui_extend,
)


def setup_function(_):
    clear_extensions()


def test_webui_extend_idempotent():
    a = webui_extend("plug_a")
    b = webui_extend("plug_a")
    assert a is b


def test_add_menu_and_collect():
    ext = webui_extend("plug_a")
    ext.add_menu(label_key="menu.a", icon="mdi:x", path="/a", order=5)
    menus = get_all_menus()
    assert menus[0]["label_key"] == "menu.a"


def test_add_route_and_ws():
    ext = webui_extend("plug_a")
    ext.add_route("/ext/a/data", ["GET"], lambda: None)
    ext.add_websocket_route("/ws/ext/a", lambda ws: None)
    routes, ws_routes = get_all_extension_routes()
    assert len(routes) == 1 and len(ws_routes) == 1


def test_add_page_i18n_perm():
    ext = webui_extend("plug_a")
    ext.add_page("panel_a", label_key="page.a", icon="mdi:p", component_url="/ext/a.html")
    ext.add_i18n("zh-CN", "page.a", "面板A")
    ext.add_permission("perm.a", label_key="perm.a")
    from entari_plugin_webui.core.i18n import get_i18n
    from entari_plugin_webui.core.permissions import get_permissions
    assert get_i18n("zh-CN")["page.a"] == "面板A"
    assert any(p["key"] == "perm.a" for p in get_permissions())
```

- [ ] **Step 2: 实现 `core/extension.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .i18n import I18nRegistry
from .permissions import PermissionsRegistry

_EXTENSIONS: dict[str, "WebUIExtension"] = {}


@dataclass
class MenuItem:
    label_key: str
    icon: str
    path: str
    order: int = 100
    badge_key: str | None = None
    children: list["MenuItem"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label_key": self.label_key,
            "icon": self.icon,
            "path": self.path,
            "order": self.order,
            "badge_key": self.badge_key,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class RouteDefinition:
    path: str
    methods: list[str]
    handler: Callable
    permission: str | None = None


@dataclass
class WebSocketRouteDefinition:
    path: str
    handler: Callable
    permission: str | None = None


@dataclass
class PageDefinition:
    key: str
    label_key: str
    icon: str
    component_url: str
    permission: str | None = None


class WebUIExtension:
    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self.routes: list[RouteDefinition] = []
        self.ws_routes: list[WebSocketRouteDefinition] = []
        self.menus: list[MenuItem] = []
        self.pages: list[PageDefinition] = []

    def add_menu(self, label_key: str, icon: str, path: str, order: int = 100, badge_key: str | None = None, children: list[MenuItem] | None = None) -> None:
        self.menus.append(MenuItem(label_key, icon, path, order, badge_key, children or []))

    def add_route(self, path: str, methods: list[str], handler: Callable, permission: str | None = None) -> None:
        self.routes.append(RouteDefinition(path, methods, handler, permission))

    def add_websocket_route(self, path: str, handler: Callable, permission: str | None = None) -> None:
        self.ws_routes.append(WebSocketRouteDefinition(path, handler, permission))

    def add_page(self, key: str, label_key: str, icon: str, component_url: str, permission: str | None = None) -> None:
        self.pages.append(PageDefinition(key, label_key, icon, component_url, permission))

    def add_i18n(self, locale: str, key: str, value: str) -> None:
        I18nRegistry.add(locale, key, value)

    def add_permission(self, key: str, label_key: str) -> None:
        PermissionsRegistry.add(key, label_key)


def webui_extend(plugin_id: str) -> WebUIExtension:
    ext = _EXTENSIONS.get(plugin_id)
    if ext is None:
        ext = WebUIExtension(plugin_id)
        _EXTENSIONS[plugin_id] = ext
    return ext


def get_all_menus() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ext in _EXTENSIONS.values():
        out.extend(m.to_dict() for m in ext.menus)
    out.sort(key=lambda m: m.get("order", 100))
    return out


def get_all_pages() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ext in _EXTENSIONS.values():
        for p in ext.pages:
            out.append({
                "key": p.key,
                "label_key": p.label_key,
                "icon": p.icon,
                "component_url": p.component_url,
                "permission": p.permission,
            })
    return out


def get_all_extension_routes() -> tuple[list[RouteDefinition], list[WebSocketRouteDefinition]]:
    routes: list[RouteDefinition] = []
    ws: list[WebSocketRouteDefinition] = []
    for ext in _EXTENSIONS.values():
        routes.extend(ext.routes)
        ws.extend(ext.ws_routes)
    return routes, ws


def clear_extensions() -> None:
    _EXTENSIONS.clear()
```

- [ ] **Step 3: 实现 `core/i18n.py`**

```python
from __future__ import annotations

_I18N: dict[str, dict[str, str]] = {}


class I18nRegistry:
    @staticmethod
    def add(locale: str, key: str, value: str) -> None:
        _I18N.setdefault(locale, {})[key] = value

    @staticmethod
    def get_locale(locale: str) -> dict[str, str]:
        return dict(_I18N.get(locale, {}))

    @staticmethod
    def all() -> dict[str, dict[str, str]]:
        return {loc: dict(d) for loc, d in _I18N.items()}


def get_i18n(locale: str) -> dict[str, str]:
    return I18nRegistry.get_locale(locale)
```

- [ ] **Step 4: 实现 `core/permissions.py`**

```python
from __future__ import annotations

_PERMS: dict[str, dict[str, str]] = {}


class PermissionsRegistry:
    @staticmethod
    def add(key: str, label_key: str) -> None:
        _PERMS[key] = {"key": key, "label_key": label_key}

    @staticmethod
    def all() -> list[dict[str, str]]:
        return list(_PERMS.values())


def get_permissions() -> list[dict[str, str]]:
    return PermissionsRegistry.all()
```

- [ ] **Step 5:** Run tests → PASS。提交 `git commit -m "feat(extension): WebUIExtension registry + i18n/permissions"`。

---

## Task 8.2：manifest 路由

**Files:** Create `api/extensions.py`

- [ ] **Step 1:**

```python
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
```

- [ ] **Step 2:** 挂 router。提交 `git commit -m "feat(api): /api/extensions/manifest"`。

---

## Task 8.3：startup 挂 WS 路由（修复漏挂）

**Files:** Modify `__init__.py`

- [ ] **Step 1:** startup 中：

```python
from entari_plugin_server import add_route, add_websocket_route
from .core.extension import get_all_extension_routes

@plugin.listen(Startup)
async def _on_startup() -> None:
    ...  # 既有的认证、日志、建表
    routes, ws_routes = get_all_extension_routes()
    for r in routes:
        add_route(r.path, methods=r.methods)(r.handler)
    for w in ws_routes:
        add_websocket_route(w.path)(w.handler)
```

- [ ] **Step 2:** `pdm run format && pdm run lint && pdm run typecheck`。提交 `git commit -m "fix(startup): mount extension WS routes"`。

---

## Task 8.4：menus 接真实扩展

`api/menus.py` 的 `get_all_menus` 局部导入已指向真实实现，无需改动。补测试。

- [ ] **Step 1:** `tests/api/test_extensions.py`

```python
def test_manifest(client, monkeypatch):
    from entari_plugin_webui.api import extensions as E
    monkeypatch.setattr(E, "get_all_menus", lambda: [{"label_key": "x", "path": "/x", "order": 1}])
    monkeypatch.setattr(E, "get_all_pages", lambda: [])
    monkeypatch.setattr(E, "I18nRegistry")
    monkeypatch.setattr(E, "get_permissions", lambda: [])
    r = client.get("/api/extensions/manifest")
    assert r.json()["menus"][0]["label_key"] == "x"
```

- [ ] **Step 2:** Run → PASS。提交。

---

## Task 8.5：公开符号导出

`__init__.py` `__all__` 与导出：

```python
from .core.extension import MenuItem, WebUIExtension, webui_extend
__all__ = ["webui_extend", "MenuItem", "WebUIExtension"]
```

`pdm run pyright`。提交 `git commit -m "feat: export webui_extend public API"`。

---

## Phase 8 完成标准

- 其他插件可 `from entari_plugin_webui import webui_extend`
- 注册的菜单进入 `/api/menus`、页面/权限进入 `/api/extensions/manifest`、i18n 与扩展词条合并
- startup 挂载 HTTP 与 WS 扩展路由
- ruff/pyright/pytest 全绿