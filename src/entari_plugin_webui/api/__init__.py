"""API 路由模块"""

from .auth import register_auth_routes
from .plugins import register_plugin_routes
from .config import register_config_routes
from .stats import register_stats_routes
from .ws import register_ws_routes

__all__ = [
    "register_auth_routes",
    "register_plugin_routes",
    "register_config_routes",
    "register_stats_routes",
    "register_ws_routes",
]


def register_all_routes():
    """注册所有 API 路由"""
    register_auth_routes()
    register_plugin_routes()
    register_config_routes()
    register_stats_routes()
    register_ws_routes()
