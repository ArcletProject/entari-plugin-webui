"""WebUI 核心模块"""

from .security import is_local_deployment
from .auth import require_auth, create_tokens, verify_token, hash_password, verify_password, generate_random_password
from .extension import WebUIExtension, MenuItem, webui_extend, get_all_menus, get_all_extension_routes

__all__ = [
    "is_local_deployment",
    "require_auth",
    "create_tokens",
    "verify_token",
    "hash_password",
    "verify_password",
    "generate_random_password",
    "WebUIExtension",
    "MenuItem",
    "webui_extend",
    "get_all_menus",
    "get_all_extension_routes",
]
