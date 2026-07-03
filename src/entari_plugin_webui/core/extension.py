from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .i18n import I18nRegistry
from .permissions import PermissionsRegistry

_EXTENSIONS: dict[str, WebUIExtension] = {}


@dataclass
class MenuItem:
    label_key: str
    icon: str
    path: str
    order: int = 100
    badge_key: str | None = None
    children: list[MenuItem] = field(default_factory=list)

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

    def add_menu(
        self,
        label_key: str,
        icon: str,
        path: str,
        order: int = 100,
        badge_key: str | None = None,
        children: list[MenuItem] | None = None,
    ) -> None:
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
            out.append(
                {
                    "key": p.key,
                    "label_key": p.label_key,
                    "icon": p.icon,
                    "component_url": p.component_url,
                    "permission": p.permission,
                }
            )
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
