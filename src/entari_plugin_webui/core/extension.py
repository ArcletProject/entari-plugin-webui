"""插件扩展机制 - 允许其他插件向 WebUI 注册路由和菜单"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class MenuItem:
    """菜单项"""
    label: str
    icon: str
    path: str
    order: int = 100
    badge: Optional[str] = None
    children: list["MenuItem"] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        result = {
            "label": self.label,
            "icon": self.icon,
            "path": self.path,
            "order": self.order,
        }
        if self.badge:
            result["badge"] = self.badge
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        return result


@dataclass
class RouteDefinition:
    """路由定义"""
    path: str
    methods: list[str]
    handler: Callable
    require_auth: bool = True


@dataclass
class WebSocketRouteDefinition:
    """WebSocket 路由定义"""
    path: str
    handler: Callable


class WebUIExtension:
    """
    WebUI 扩展
    
    允许其他插件注册:
    - HTTP 路由
    - WebSocket 路由
    - 菜单项
    """
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.routes: list[RouteDefinition] = []
        self.ws_routes: list[WebSocketRouteDefinition] = []
        self.menus: list[MenuItem] = []
    
    def add_route(
        self,
        path: str,
        methods: list[str],
        handler: Callable,
        require_auth: bool = True
    ):
        """
        注册 HTTP 路由
        
        Args:
            path: 路由路径，如 "/api/my-plugin/data"
            methods: HTTP 方法列表，如 ["GET", "POST"]
            handler: 处理函数
            require_auth: 是否需要认证，默认 True
        """
        self.routes.append(RouteDefinition(
            path=path,
            methods=methods,
            handler=handler,
            require_auth=require_auth
        ))
    
    def add_websocket_route(self, path: str, handler: Callable):
        """
        注册 WebSocket 路由
        
        Args:
            path: 路由路径，如 "/ws/my-plugin"
            handler: WebSocket 处理函数
        """
        self.ws_routes.append(WebSocketRouteDefinition(
            path=path,
            handler=handler
        ))
    
    def add_menu(
        self,
        label: str,
        icon: str,
        path: str,
        order: int = 100,
        badge: Optional[str] = None,
        children: Optional[list[MenuItem]] = None
    ):
        """
        注册菜单项
        
        Args:
            label: 菜单标签
            icon: 图标名称（如 "mdi:puzzle"）
            path: 路由路径
            order: 排序权重，数值越小越靠前
            badge: 徽章文本
            children: 子菜单项
        """
        self.menus.append(MenuItem(
            label=label,
            icon=icon,
            path=path,
            order=order,
            badge=badge,
            children=children or []
        ))


# 扩展注册表
_extensions: dict[str, WebUIExtension] = {}


def webui_extend(plugin_id: str) -> WebUIExtension:
    """
    获取或创建插件的 WebUI 扩展
    
    Usage:
        from entari_plugin_webui import webui_extend
        
        ext = webui_extend("my-plugin")
        ext.add_menu("我的功能", "mdi:star", "/my-plugin", order=50)
        ext.add_route("/api/my-plugin/data", ["GET"], my_handler)
    
    Args:
        plugin_id: 插件 ID
    
    Returns:
        WebUIExtension 实例
    """
    if plugin_id not in _extensions:
        _extensions[plugin_id] = WebUIExtension(plugin_id)
    return _extensions[plugin_id]


def get_all_menus() -> list[dict]:
    """
    获取所有插件注册的菜单项
    
    Returns:
        按 order 排序的菜单项列表
    """
    menus = []
    for ext in _extensions.values():
        menus.extend(ext.menus)
    
    menus.sort(key=lambda m: m.order)
    return [m.to_dict() for m in menus]


def get_all_extension_routes() -> tuple[list[RouteDefinition], list[WebSocketRouteDefinition]]:
    """
    获取所有插件注册的路由
    
    Returns:
        (HTTP 路由列表, WebSocket 路由列表)
    """
    routes = []
    ws_routes = []
    
    for ext in _extensions.values():
        routes.extend(ext.routes)
        ws_routes.extend(ext.ws_routes)
    
    return routes, ws_routes


def clear_extensions():
    """清除所有扩展（用于测试）"""
    _extensions.clear()
