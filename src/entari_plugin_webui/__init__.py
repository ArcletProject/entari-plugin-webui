"""Entari Plugin: WebUI 服务（重设计版）"""

from __future__ import annotations

from pathlib import Path

from arclet.entari import plugin
from arclet.entari.event.lifespan import Startup
from arclet.entari.event.send import SendResponse
from arclet.entari.logger import log
from arclet.entari.plugin import PluginRole, plugin_config
from entari_plugin_server import add_route, add_websocket_route, replace_asgi, server
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse, JSONResponse, Response

from .config import Config
from .core.extension import MenuItem as MenuItem
from .core.extension import WebUIExtension as WebUIExtension
from .core.extension import get_all_extension_routes
from .core.extension import webui_extend as webui_extend
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
_STATIC_DIR = Path(__file__).parent / "static"
_FRONTEND_DIR = _STATIC_DIR / "frontend"

logger = log.wrapper("[webui]", color="green")
webui_config = plugin_config(Config, bind=True)

from .api import create_app as _create_app  # noqa: E402
from .api import logs  # noqa: F401
from .models.stats import MessageStat  # noqa: F401
from .services.stats_service import increment  # noqa: PLC0415
from .adapter import WebUIAdapter

_session_store: SessionStore = SessionStore(ttl=webui_config.session_ttl)
_login_throttle = LoginThrottle(*parse_rate_limit(webui_config.login_rate_limit))

if not server.path:
    logger.warning("未检测到 Server 插件的 path 配置，WebUI 可能无法正常工作")
    logger.warning("已自动设置 Server 插件的 path 为 /satori")
    server.path = "/satori"

server.apply(WebUIAdapter())


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


replace_asgi(app := _create_app())

if _FRONTEND_DIR.exists():
    if (_FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=_FRONTEND_DIR / "assets", html=True))

add_route("/", methods=["GET"], include_in_schema=False)(_root)


@app.exception_handler(StarletteHTTPException)
async def _spa_fallback(req, exc: StarletteHTTPException) -> Response:
    if exc.status_code != 404:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
    if req.url.path.startswith("api/") or req.url.path.startswith("ws/") or req.url.path.startswith(server.path):
        return JSONResponse({"detail": exc.detail}, status_code=404, headers=exc.headers)
    if not _FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'pdm run build-frontend'.", status_code=503, headers=exc.headers
        )
    file_path = _FRONTEND_DIR / req.url.path
    if file_path.is_file():
        return FileResponse(file_path)
    index = _FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"detail": exc.detail}, status_code=404, headers=exc.headers)


# ---------- SendResponse listener (message counting) ----------
@plugin.listen(SendResponse)
async def _on_message_sent(event: SendResponse) -> None:
    platform = event.account.platform
    try:
        await increment(platform)
    except Exception:  # noqa: BLE001
        logger.debug("消息计数失败")


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
