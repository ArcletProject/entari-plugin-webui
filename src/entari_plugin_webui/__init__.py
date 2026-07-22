"""Entari Plugin: WebUI 服务（重设计版）"""

from __future__ import annotations

from pathlib import Path

from arclet.entari import plugin, metadata
from arclet.entari.event.lifespan import Startup
from arclet.entari.event.send import SendResponse
from arclet.entari.plugin import PluginRole, plugin_config
from entari_plugin_server import add_route, add_websocket_route, replace_asgi, server
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, Response

from .config import Config
from .core.extension import MenuItem as MenuItem
from .core.extension import WebUIExtension as WebUIExtension
from .core.extension import get_all_extension_routes
from .core.extension import webui_extend as webui_extend
from .core.security import (
    LoginThrottle,
    generate_random_password,
    hash_password,
    is_hashed_password,
    is_local_deployment,
    parse_rate_limit,
    set_local_mode,
)
from .core.session import SessionStore
from .utils import logger

__version__ = "1.0.2"
_STATIC_DIR = Path(__file__).parent / "static"
_FRONTEND_DIR = _STATIC_DIR / "frontend"

webui_config = plugin_config(Config, bind=True)

from .adapter import WebUIAdapter
from .api import create_app as _create_app  # noqa: E402
from .api import logs  # noqa: F401
from .models.stats import MessageStat  # noqa: F401
from .services.stats_service import increment  # noqa: PLC0415

_session_store: SessionStore = SessionStore(ttl=webui_config.session_ttl)
_login_throttle = LoginThrottle(*parse_rate_limit(webui_config.login_rate_limit))

if not server.path:
    logger.warning("未检测到 Server 插件的 path 配置，WebUI 可能无法正常工作")
    logger.warning("已自动设置 Server 插件的 path 为 /satori")
    server.path = "/satori"

server.apply(WebUIAdapter())


metadata(
    "WebUI 服务",
    PluginRole.UTILITY,
    [{"name": "RF-Tar-Railt", "email": "rf_tar_railt@qq.com"}],
    __version__,
    description="基于 Vite + Vue 3 + Element Plus 的可视化管理面板",
    urls={"homepage": "https://github.com/ArcletProject/entari-plugin-webui"},
    config=Config,
)


# ---------- SPA fallback handlers ----------
async def _root(request: Request) -> Response:
    if not _FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'pdm run build-frontend'.",
            status_code=503,
        )
    path = request.url.path.lstrip("/")
    file = _FRONTEND_DIR / (path or "index.html")
    if file.exists():
        return FileResponse(file)
    return Response(status_code=404)


replace_asgi(app := _create_app())

if _FRONTEND_DIR.exists() and (_FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIR / "assets", html=True))

add_route("/", methods=["GET"], include_in_schema=False)(_root)
add_route("/favicon.ico", methods=["GET"], include_in_schema=False)(_root)
add_route("/favicon.svg", methods=["GET"], include_in_schema=False)(_root)


# ---------- SendResponse listener (message counting) ----------
@plugin.listen(SendResponse)
async def _on_message_sent(event: SendResponse) -> None:
    platform = event.account.platform
    try:
        await increment(platform)
    except Exception:  # noqa: BLE001
        logger.debug("消息计数失败")


# ---------- Startup listener ----------
@plugin.listen(Startup, priority=100)
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
        elif not is_hashed_password(webui_config.password):
            webui_config.password = hash_password(webui_config.password)
            logger.info("已将配置文件中的明文密码哈希处理")

    import arclet.entari.logger as entari_log
    from loguru import logger as loguru_logger

    from .core.log_stream import LogWriter, get_log_buffer

    log_buffer = get_log_buffer()
    loguru_logger.add(
        LogWriter(log_buffer), level=0, diagnose=True, backtrace=True, colorize=True, filter=entari_log.default_filter
    )  # type: ignore[call-overload]

    routes, ws_routes = get_all_extension_routes()
    for r in routes:
        add_route(r.path, methods=r.methods)(r.handler)
    for w in ws_routes:
        add_websocket_route(w.path)(w.handler)

    host = server.host or "127.0.0.1"
    logger.info(f"管理面板已启动: http://{host}:{server.port}/")
