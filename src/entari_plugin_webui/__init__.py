"""Entari Plugin: WebUI 服务（重设计版）"""

from __future__ import annotations

from pathlib import Path

from arclet.entari import plugin
from arclet.entari.event.lifespan import Startup
from arclet.entari.logger import log
from arclet.entari.plugin import PluginRole, plugin_config
from entari_plugin_server import add_route, replace_asgi, server
from starlette.responses import FileResponse, Response

from .config import Config
from .core.security import (
    LoginThrottle,
    generate_random_password,
    hash_password,
    is_local_deployment,
    parse_rate_limit,
    set_local_mode,
)
from .core.session import SessionStore

__version__ = "0.1.0"
__all__ = []
_STATIC_DIR = Path(__file__).parent / "static"
_FRONTEND_DIR = _STATIC_DIR / "frontend"

logger = log.wrapper("[webui]", color="green")
webui_config = plugin_config(Config)

from .api import create_app as _create_app  # noqa: E402

_session_store: SessionStore = SessionStore(ttl=webui_config.session_ttl)
_login_throttle = LoginThrottle(*parse_rate_limit(webui_config.login_rate_limit))


plugin.metadata(
    "WebUI 服务",
    PluginRole.NORMAL,
    [{"name": "RF-Tar-Railt", "email": "rf_tar_railt@qq.com"}],
    __version__,
    description="基于 Vite + Vue 3 + Element Plus 的可视化管理面板",
    urls={"homepage": "https://github.com/ArcletProject/entari-plugin-webui"},
    config=Config,
)


# ---------- SPA fallback handlers ----------
async def _spa_fallback(path: str) -> Response:
    if path.startswith("api/") or path.startswith("ws/"):
        return Response(status_code=404)
    if not _FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'pdm run build-frontend'.",
            status_code=503,
        )
    file_path = _FRONTEND_DIR / path
    if file_path.is_file():
        return FileResponse(file_path)
    index = _FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return Response(status_code=404)


async def _root() -> Response:
    if not _FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'pdm run build-frontend'.",
            status_code=503,
        )
    index = _FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return Response(status_code=404)


replace_asgi(_create_app())

if _FRONTEND_DIR.exists():
    if (_FRONTEND_DIR / "assets").exists():
        server.mount("/assets", _FRONTEND_DIR / "assets")
    if (_FRONTEND_DIR / "_nuxt").exists():
        server.mount("/_nuxt", _FRONTEND_DIR / "_nuxt")

add_route("/{path:path}", methods=["GET"])(_spa_fallback)
add_route("/", methods=["GET"])(_root)


# ---------- Startup listener ----------
@plugin.listen(Startup)
async def _on_startup() -> None:
    is_local = is_local_deployment(server.host)
    set_local_mode(is_local)
    if is_local:
        logger.info("本地部署模式，无需认证")
    else:
        logger.info("远程部署模式，需要认证")
        if not webui_config.password:
            raw = generate_random_password(16)
            webui_config.password = hash_password(raw)
            logger.warning("已生成管理员密码：" + raw)
    host = server.host or "127.0.0.1"
    logger.info(f"管理面板已启动: http://{host}:{server.port}/")
