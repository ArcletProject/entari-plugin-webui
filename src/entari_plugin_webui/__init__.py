"""
================================================================================
Entari 插件：WebUI 服务
--------------------------------------------------------------------------------
作者：RF-Tar-Railt <rf_tar_railt@qq.com>
版本：0.2.0
描述：基于 Nuxt 3 + Naive UI 的可视化管理面板
主页：https://github.com/ArcletProject/entari-plugin-webui
================================================================================
"""

from pathlib import Path
from datetime import datetime

from starlette.responses import FileResponse, Response
from starlette.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from arclet.entari import plugin
from arclet.entari.event.lifespan import Startup
from arclet.entari.event.send import SendResponse
from entari_plugin_server import add_route, replace_fastapi, server
from entari_plugin_database import SqlalchemyService, Base, get_session

from .config import Config, webui_config

__all__ = ["webui_extend", "MenuItem", "WebUIExtension"]

# ---------- 插件元数据 ----------
plugin.metadata(
    "WebUI 服务",
    [{"name": "RF-Tar-Railt", "email": "rf_tar_railt@qq.com"}],
    "0.2.0",
    description="基于 Nuxt 3 + Naive UI 的可视化管理面板",
    urls={
        "homepage": "https://github.com/ArcletProject/entari-plugin-webui",
    },
    config=Config
)

# ---------- 路径配置 ----------
FRONTEND_DIR = Path(__file__).parent / "frontend"
STATIC_DIR = Path(__file__).parent / "static"

# ---------- CORS 中间件 ----------
cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
replace_fastapi(middleware=[cors_middleware])


from .core import (
    is_local_deployment,
    require_auth,
    hash_password,
    generate_random_password,
    get_all_menus,
    get_all_extension_routes,
    webui_extend,
)
from .core.auth import set_local_mode
from .utils.log_stream import get_log_buffer, LogWriter
from .models.stats import MessageStat

# 导入 API 路由（通过装饰器自动注册）
from .api import auth, plugins, config, stats, ws

# 公开扩展接口
from .core.extension import MenuItem, WebUIExtension


# ---------- 静态文件服务 ----------
if FRONTEND_DIR.exists():
    # Nuxt 生成的静态资源
    if (FRONTEND_DIR / "_nuxt").exists():
        server.mount("/_nuxt", FRONTEND_DIR / "_nuxt")
    if (FRONTEND_DIR / "assets").exists():
        server.mount("/assets", FRONTEND_DIR / "assets")


# ---------- SPA Fallback（支持 history 模式）----------
@add_route("/{path:path}", methods=["GET"])
async def spa_fallback(path: str):
    """
    SPA 回退路由
    
    - API 路由不走这里（由具体路由处理）
    - 静态文件直接返回
    - 其他路由返回 index.html
    """
    # 跳过 API 和 WebSocket 路由
    if path.startswith("api/") or path.startswith("ws/"):
        return Response(status_code=404)
    
    if not FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'npm run generate' in frontend directory.",
            status_code=503
        )
    
    # 尝试直接返回静态文件
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # 返回 index.html（SPA 入口）
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    return Response(status_code=404)


# ---------- 根路由 ----------
@add_route("/", methods=["GET"])
async def root():
    """根路由返回 index.html"""
    if not FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'npm run generate' in frontend directory.",
            status_code=503
        )
    
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    return Response(status_code=404)


# ---------- 扩展菜单 API ----------
@add_route("/api/menus", methods=["GET"])
@require_auth
async def get_menus():
    """获取所有菜单项（含扩展插件注册的）"""
    from starlette.responses import JSONResponse
    
    # 内置菜单
    builtin_menus = [
        {"label": "仪表盘", "icon": "mdi:view-dashboard", "path": "/", "order": 0},
        {"label": "插件管理", "icon": "mdi:puzzle", "path": "/plugins", "order": 10},
        {"label": "插件市场", "icon": "mdi:store", "path": "/market", "order": 20},
        {"label": "配置管理", "icon": "mdi:cog", "path": "/config", "order": 30},
        {"label": "实时日志", "icon": "mdi:console", "path": "/logs", "order": 40},
    ]
    
    # 合并扩展菜单
    extension_menus = get_all_menus()
    all_menus = builtin_menus + extension_menus
    all_menus.sort(key=lambda m: m.get("order", 100))
    
    return JSONResponse({
        "success": True,
        "menus": all_menus
    })


# ---------- 初始化 ----------
@plugin.listen(Startup)
async def on_startup():
    """
    插件启动初始化
    
    1. 设置认证模式
    2. 初始化管理员密码（远程部署时）
    3. 配置日志输出
    4. 注册扩展路由
    """

    # 检测部署模式
    is_local = is_local_deployment(server.host)
    set_local_mode(is_local)
    
    if is_local:
        logger.info("[WebUI] 本地部署模式，无需认证")
    else:
        logger.info("[WebUI] 远程部署模式，需要认证")
        
        # 检查是否已初始化密码
        if not webui_config.password:
            # 生成随机密码
            raw_password = generate_random_password(16)
            hashed = hash_password(raw_password)
            
            # 写入配置文件
            webui_config.password = hashed
            
            logger.warning("=" * 60)
            logger.warning("[WebUI] 已生成管理员密码，请妥善保管：")
            logger.warning(f"[WebUI] 密码: {raw_password}")
            logger.warning("=" * 60)
    
    # 配置日志输出到环形缓冲区
    log_buffer = get_log_buffer()
    log_writer = LogWriter(log_buffer)
    
    import arclet.entari.logger as entari_log
    logger.add(
        log_writer,
        level=0,
        diagnose=True,
        backtrace=True,
        colorize=True,
        filter=entari_log.default_filter,
        format=entari_log._custom_format,
    )
    
    # 注册扩展路由
    routes, ws_routes = get_all_extension_routes()
    for route in routes:
        add_route(route.path, methods=route.methods)(route.handler)
    
    # 输出访问地址
    host = server.host or "127.0.0.1"
    port = server.port
    logger.info(f"[WebUI] 管理面板已启动: http://{host}:{port}/")


# ---------- 消息计数 ----------
@plugin.listen(SendResponse)
async def on_message_sent(event: SendResponse):
    """记录发送的消息数量"""
    platform = event.account.platform or "unknown"
    today = datetime.utcnow().date().isoformat()
    
    try:
        async with get_session() as session:
            from sqlalchemy import select
            
            stmt = select(MessageStat).where(
                MessageStat.platform == platform,
                MessageStat.date == today
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            
            if row:
                row.count += 1
            else:
                session.add(MessageStat(
                    platform=platform,
                    instance_id=0,
                    date=today,
                    count=1
                ))
            
            await session.commit()
    except Exception as e:
        logger.debug(f"[WebUI] 消息计数失败: {e}")
