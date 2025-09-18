"""
================================================================================
Entari 插件：WebUI 服务
--------------------------------------------------------------------------------
作者：Utopia <utopia@qq.com>
版本：0.1.1
描述：基于 Vue3 + entari_plugin_server + entari_plugin_database 的可视化面板
主页：https://github.com/ArcletProject/entari-plugin-webui
================================================================================
"""

import os
import yaml
import logging
import asyncio
import secrets
from datetime import datetime,timedelta
from io import StringIO
from pathlib import Path
import sys,uuid
import subprocess
import json
from dataclasses import dataclass, field

from arclet.entari.event.lifespan import Startup
from sqlalchemy import select, ForeignKey,Integer, String, JSON,func, and_
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import flag_modified
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from fastapi import Request
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from ansi2html import Ansi2HTMLConverter

from entari_plugin_database import SqlalchemyService, Base, mapped_column, Mapped, get_session
from entari_plugin_server import add_route, replace_fastapi, add_websocket_route,server
from arclet.entari.plugin import get_plugins,find_plugin
from arclet.entari.config import EntariConfig
from arclet.entari.event.send import SendResponse
from arclet.entari import plugin, inject
import arclet.entari.logger as entari_log
from loguru import logger

plugin.metadata(
    "WebUI 服务",
    [{"name": "Utopia", "email": "utopia@qq.com"}],
    "0.1.1",
    description="基于vue3和entari_plugin_server、entari_plugin_database 的可视化面板",
    urls={
        "homepage": "https://github.com/ArcletProject/entari-plugin-webui",
    },
)

# ---------- 全局配置 ----------
logging.getLogger("lagrange.utils.binary.protobuf").setLevel(logging.CRITICAL)
UPLOAD_DIR = "configs"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = EntariConfig.instance.path
RUNTIME_CONF = Path(__file__).with_name('frontend') / 'runtime.json'
START_TIME = datetime.utcnow()

# # ---------- 设置静态目录 ----------
server.mount("/assets", Path(os.path.join(BASE_DIR, 'entari_plugin_webui/frontend')))
server.mount("/frontend", Path(os.path.join(BASE_DIR, 'entari_plugin_webui/frontend/assets')))

@dataclass
class InstallTask:
    task_id: str
    plugin_id: str
    status: str = "pending"
    percent: int = 0
    log: str = field(default="")

task_map: dict[str, InstallTask] = {}

@dataclass
class UninstallTask:
    task_id: str
    plugin_id: str
    status: str = "pending"
    percent: int = 0
    log: str = ""

uninstall_task_map: dict[str, UninstallTask] = {}

# ---------- 前端入口 ----------
@add_route("/")
async def vue_set(request: Request):
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'index.html')
    return FileResponse(html_path)

# ---------- CORS ----------
cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
replace_fastapi(middleware=[cors_middleware])

# ---------- 数据库模型 ----------
class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    password: Mapped[str] = mapped_column(String(30), nullable=False)
    token: Mapped[str] = mapped_column(String(512), default="")
    instances: Mapped[list["Instance"]] = relationship("Instance", back_populates="user", cascade="all, delete-orphan")
    email: Mapped[str] = mapped_column(String(120), default="user@example.com")

class Instance(Base):
    """实例表"""
    __tablename__ = "instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="instances")
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    host: Mapped[str] = mapped_column(String(100), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(String(100), nullable=True)
    ignoreSelfMessage: Mapped[bool] = mapped_column(default=True)
    logLevel: Mapped[str] = mapped_column(String(20), default="INFO")
    prefix: Mapped[str] = mapped_column(String(20), default="/")
    created_at: Mapped[str] = mapped_column(String(30), default="")
    filename: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(20), default="已停止")
    plugins: Mapped[list] = mapped_column(JSON, default=[])

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class MessageStat(Base):
    """每日各平台消息计数"""
    __tablename__ = "message_stat"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("instances.id"), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    count: Mapped[int] = mapped_column(Integer, default=0)

# ---------- 工具 ----------
def generate_token(length: int = 64) -> str:
    """生成随机 token"""
    return secrets.token_urlsafe(length)
async def get_week_message_sum() -> list[int]:
    """返回最近 7 天【各平台汇总】的每日消息量，顺序 Mon->Sun"""
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())   # 本周一
    week_days = [monday + timedelta(days=i) for i in range(7)]

    async with get_session() as session:
        # SELECT date, SUM(count) FROM message_stat
        # WHERE date BETWEEN :monday AND :sunday GROUP BY date;
        stmt = (
            select(MessageStat.date, func.sum(MessageStat.count).label("total"))
            .where(
                and_(
                    MessageStat.date >= monday.isoformat(),
                    MessageStat.date <= week_days[-1].isoformat()
                )
            )
            .group_by(MessageStat.date)
        )
        rows = (await session.execute(stmt)).all()

    day_map = {row.date: row.total for row in rows}
    return [day_map.get(d.isoformat(), 0) for d in week_days]

async def get_today_message() -> int:
    """今天 0 点至今的消息总量"""
    today_str = datetime.utcnow().date().isoformat()
    async with get_session() as session:
        stmt = select(func.sum(MessageStat.count)).where(MessageStat.date == today_str)
        total = (await session.execute(stmt)).scalar()
    return total or 0

# ---------- 初始化 ----------
@plugin.listen(Startup)
@inject(SqlalchemyService)
async def init_db():
    """创建表结构，并插入默认管理员帐号"""

    async with get_session() as session:
        await session.run_sync(
            lambda sync_sess: Base.metadata.create_all(
                bind=sync_sess.bind, tables=[MessageStat.__table__]
            )
        )
        # 若数据库为空，则插入一条默认用户
        exists = (await session.scalars(select(User))).one_or_none()
        if not exists:
            token = generate_token()
            user = User(name="Entari", password="114514", token=token)
            instance = Instance(
                name="config",
                type="ws",
                host=server.host,
                port=server.port,
                path="satori",
                ignoreSelfMessage=True,
                logLevel="INFO",
                prefix="/",
                created_at=datetime.now().isoformat(),
                filename="config.yml",
                state="已停止",
            )
            user.instances.append(instance)

            session.add(user)
        await session.commit()
    host = server.host or '127.0.0.1'
    port = server.port
    RUNTIME_CONF.write_text(
        json.dumps({'baseURL': f'http://{host}:{port}/api'}, ensure_ascii=False),
        encoding='utf-8'
    )

# ---------- 登录 ----------
@add_route("/api/login", methods=["POST"])
async def login(request: Request):
    """处理登录请求，返回新 token"""
    data     = await request.json()
    username = data.get("name")
    password = data.get("password")

    async with get_session() as session:
        result = await session.scalars(
            select(User).where(User.name == username, User.password == password)
        )
        user = result.one_or_none()
        if not user:
            return JSONResponse({"success": False, "message": "用户名或密码错误"})

        # 生成新 token 并保存
        token = generate_token()
        user.token = token
        await session.commit()
        await session.refresh(user)
        instances = (await session.scalars(select(Instance).where(Instance.user_id == user.id))).all()
        return JSONResponse({"success": True, "token": token, "instances": [inst.as_dict() for inst in instances],
                             "user": { "name": user.name, "email": user.email }})

# ---------- 登出 ----------
@add_route("/api/logout", methods=["POST"])
async def logout():
    """占位：前端可直接丢弃 token"""
    return True

# ---------- 信息修改 ----------
@add_route("/api/user/update", methods=["POST"])
async def user_update(request: Request):
    """修改当前登录用户的密码或邮箱 """
    body = await request.json()
    new_pwd = body.get("password")
    new_email = body.get("email")

    if not new_pwd and not new_email:
        return JSONResponse({"success": False, "message": "无修改内容"})

    token = request.headers.get("Authorization") or request.headers.get("token")

    if not token:
        return JSONResponse({"success": False, "message": "未登录"}, status_code=401)

    async with get_session() as session:
        user = (await session.execute(select(User).where(User.token == token))).scalar_one_or_none()
        if not user:
            return JSONResponse({"success": False, "message": "Token 无效"}, status_code=401)

        if new_pwd:
            user.password = new_pwd
        if new_email:
            user.email = new_email

        await session.commit()

    return JSONResponse({"success": True, "message": "更新成功"})

# ---------- 实例增改 ----------
@add_route("/api/menus", methods=["POST"])
async def create_instance(request: Request):
    """新增或更新实例配置"""
    data       = await request.json()
    instance_id = data.get("id")
    config_data = data.get("data")
    filename    = data.get("filename")

    # 参数校验
    if not instance_id or not config_data or not filename:
        return JSONResponse({
            "success": False,
            "token": data.get("token"),
            "message": "缺少必要参数: id, data 或 filename"
        })

    # 构造实例对象
    new_instance = Instance(
        id=instance_id,
        name=filename.replace(".yml", ""),
        type=data.get("type"),
        host=data.get("host"),
        port=data.get("port"),
        path=data.get("path"),
        ignoreSelfMessage=data.get("ignoreSelfMessage", True),
        logLevel=data.get("logLevel", "INFO"),
        prefix=data.get("prefix", "/"),
        created_at=datetime.now().isoformat(),
        filename=filename,
        state="已停止"
    )

    # 写入文件
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(config_data)
    except Exception as e:
        return JSONResponse({"success": False, "message": f"文件保存失败: {str(e)}"})

    # 更新数据库
    async with get_session() as session:
        result = await session.scalars(select(User))
        user = result.first()
        if not user:
            return JSONResponse({"success": False, "message": "用户不存在"})

        user.instances.append(new_instance)
        flag_modified(user, 'instances')
        await session.commit()

    return JSONResponse({
        "success": True,
        "message": "实例创建成功",
        "instances": [new_instance.as_dict()]
    })

# ---------- 插件 ----------
MARKET_PLUGINS = {
    "entari-plugin-browser",
    "entari-plugin-database",
    "entari-plugin-arkgacha",
    "entari-plugin-server",
    "entari-plugin-webui",
}

@add_route("/api/plugins", methods=["GET"])
async def list_plugins():
    def _serial(p):
        m = p.metadata
        key = p.id
        enabled = find_plugin(key).is_available

        cfg = getattr(p, 'config', None)
        if cfg and hasattr(cfg, 'dict'):
            cfg = cfg.dict()
        elif cfg and hasattr(cfg, 'copy'):
            cfg = dict(cfg)
        else:
            cfg = {}

        return {
            "name": getattr(m, 'name', None) or key,
            "id": key,
            "title": getattr(m, 'name', None) or key,
            "desc": getattr(m, 'description', None) or "暂无描述",
            "version": getattr(m, 'version', None) or "0.0.0",
            "author": (
                "; ".join(
                    i if isinstance(i, str) else i.get("name", "unknown")
                    for i in (getattr(m, 'author', None) or [])
                )
            ) or "unknown",
            "status": enabled,
            "builtin": True,
            "urls": getattr(m, 'urls', None) or {},
            "configurable": m and getattr(m, 'config', None) is not None,
            "config": cfg,
        }

    plugins = get_plugins()
    return JSONResponse([_serial(p) for p in plugins])

@add_route("/api/market/plugins", methods=["GET"])
async def market_plugins():
    pip_list = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=json"],
        stdout=subprocess.PIPE,
        text=True,
        check=True
    ).stdout

    installed_packages = json.loads(pip_list)
    installed_plugins = {
        pkg["name"]: True for pkg in installed_packages
        if pkg["name"].startswith("entari-plugin-") or pkg["name"].startswith("entari_plugin_")
    }

    market_plugins_list = []
    for plugin in MARKET_PLUGINS:
        installed = False
        if plugin in installed_plugins or f"entari_plugin_{plugin}" in installed_plugins:
            installed = True

        market_plugins_list.append({
            "name": plugin,
            "fullName": plugin,
            "desc": plugin,
            "author": "unknown",
            "stars": 0,
            "updated": "",
            "tags": [],
            "installed": installed
        })
    return JSONResponse(market_plugins_list)

@add_route("/api/plugins/toggle", methods=["POST"])
async def toggle_plugin(request: Request):
    body = await request.json()
    id = body["id"]
    enable = body["enable"]
    plugin = find_plugin(id)
    if enable:
        plugin.enable()
    else:
        plugin.disable()
    return JSONResponse({"success": True})

# ---------- 异步安装/卸载 ----------
async def pip_install(task: InstallTask):
    task.status = "running"
    cmd = [sys.executable, "-m", "pip", "install", "-U", task.plugin_id]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
    if proc.returncode == 0:
        task.status = "success"
        task.percent = 100
        plg = find_plugin(task.plugin_id)
        if plg:
            await plg.enable()
    else:
        task.status = "failed"
        task.percent = 0

async def pip_uninstall_task(task: UninstallTask):
    task.status = "running"
    cmd = [sys.executable, "-m", "pip", "uninstall", "-y", task.plugin_id]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
    if proc.returncode == 0:
        task.status = "success"
        task.percent = 100
    else:
        task.status = "failed"
        task.percent = 0

@add_route("/api/plugins/install", methods=["POST"])
async def plugin_install(request: Request):
    body = await request.json()
    plugin_id = body["name"]
    task_id = str(uuid.uuid4())
    task = InstallTask(task_id=task_id, plugin_id=plugin_id)
    task_map[task_id] = task
    asyncio.create_task(pip_install(task))
    return JSONResponse({"success": True, "task_id": task_id})

@add_route("/api/plugins/uninstall", methods=["POST"])
async def plugin_uninstall(request: Request):
    body = await request.json()
    plugin_id = body["name"]
    task_id = str(uuid.uuid4())
    task = UninstallTask(task_id=task_id, plugin_id=plugin_id)
    asyncio.create_task(pip_uninstall_task(task))
    return JSONResponse({"success": True, "task_id": task_id})

@add_route("/api/plugins/save", methods=["POST"])
async def plugin_save(request: Request):
    body = await request.json()
    plugin_id = body.get("id")
    plugin_config = body.get("config")
    plg = find_plugin(plugin_id)
    if plg is None:
        return JSONResponse({"success": False, "message": "插件未找到"}, status_code=404)
    plg.config.update(plugin_config)

    return JSONResponse({"success": True})

# ---------- 实时日志 WebSocket ----------
fake_io = StringIO()
logger.add(
    fake_io,
    level=0,
    diagnose=True,
    backtrace=True,
    colorize=True,
    filter=entari_log.default_filter,
    format=entari_log._custom_format,
)
conv = Ansi2HTMLConverter(inline=True, scheme="xterm")

@add_websocket_route("/ws/log")
async def websocket_log(websocket: WebSocket):
    """实时推送日志到前端"""
    await websocket.accept()

    try:
        # 读取日志内容并发送
        last_position = 0
        while True:
            await asyncio.sleep(1)
            fake_io.seek(last_position)
            new_content = fake_io.read()
            if new_content:
                html = conv.convert(new_content, full=False)
                await websocket.send_text(new_content)
                last_position = fake_io.tell()

    except (asyncio.CancelledError, ConnectionResetError):
        pass  # 正常取消或连接重置
    except FileNotFoundError:
        await websocket.send_text("日志文件不存在，等待生成...")
    except WebSocketDisconnect:
        pass  # 客户端断开
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        await websocket.send_text(f"服务端错误: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# ---------- 首页统计 ----------
@add_route("/api/init_data", methods=["GET"])
async def init_data():
    week = await get_week_message_sum()
    today = await get_today_message()

    async with get_session() as session:
        total_msg = await session.execute(select(func.sum(MessageStat.count)))
        message_count = total_msg.scalar() or 0

    plugins = get_plugins()
    enabled_cnt = sum(1 for p in plugins if p.is_available)
    runtime_min = int((datetime.utcnow() - START_TIME).total_seconds() // 60)

    return JSONResponse({
        "today_messages": today,
        "weekMessages": week,
        "message_count": message_count,
        "plugin_enabled": enabled_cnt,
        "plugin_total": len(plugins),
        "runtime": runtime_min
    })

@plugin.listen(SendResponse)
@inject(SqlalchemyService)
async def count_sent(event: SendResponse):   # 参数名 = 事件类型名（小写）
    platform = event.account.platform or 'unknown'
    today = datetime.utcnow().date().isoformat()

    async with get_session() as session:
        row = await session.execute(
            select(MessageStat).where(
                MessageStat.platform == platform,
                MessageStat.date == today
            )
        )
        row = row.scalar_one_or_none()
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

# ---------- 主配置读写 ----------
@add_route("/api/config", methods=["GET"])
async def get_config():
    filepath = Path(CONFIG_FILE)
    if not filepath.exists():
        return JSONResponse({})
    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # print(data)
    return JSONResponse(data)

@add_route("/api/config", methods=["POST"])
async def save_config(request: Request):
    body = await request.json()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(body, f, allow_unicode=True, sort_keys=False)
    return JSONResponse({"success": True})