
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
import asyncio
import secrets
from datetime import datetime
from io import StringIO
from pathlib import Path

from arclet.entari.event.lifespan import Startup
from sqlalchemy import select, ForeignKey
from sqlalchemy import Integer, String, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import flag_modified
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from fastapi import Request
from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from ansi2html import Ansi2HTMLConverter

from entari_plugin_database import SqlalchemyService, Base, mapped_column, Mapped, get_session,Config
from entari_plugin_server import add_route, replace_fastapi, add_websocket_route,server
from arclet.entari.config import config_model_schema
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

# ================================================================================
# 全局配置
# ================================================================================
UPLOAD_DIR = "configs"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = "./entari_plugin_webui/backend/configs/entari.yml"

# 设置静态目录
server.mount("/assets", Path(os.path.join(BASE_DIR, 'entari_plugin_webui/frontend')))
server.mount("/frontend", Path(os.path.join(BASE_DIR, 'entari_plugin_webui/frontend/assets')))


@add_route("/")
async def vue_set(request: Request):
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'index.html')
    return FileResponse(html_path)

# -------------------------------- CORS --------------------------------
cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
replace_fastapi(middleware=[cors_middleware])

# ================================================================================
# 数据库模型
# ================================================================================
class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    password: Mapped[str] = mapped_column(String(30), nullable=False)
    token: Mapped[str] = mapped_column(String(512), default="")
    instances: Mapped[list["Instance"]] = relationship("Instance", back_populates="user", cascade="all, delete-orphan")

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
# ================================================================================
# 工具函数
# ================================================================================
def generate_token(length: int = 64) -> str:
    """生成随机 token"""
    return secrets.token_urlsafe(length)

# ================================================================================
# 初始化数据库
# ================================================================================
@plugin.listen(Startup)
@inject(SqlalchemyService)
async def init_db():
    """创建表结构，并插入默认管理员帐号"""

    async with get_session() as session:
        # 若数据库为空，则插入一条默认用户
        exists = (await session.scalars(select(User))).one_or_none()
        if not exists:
            token = generate_token()
            user = User(name="Entari", password="114514", token=token)
            instance = Instance(
                name="config",
                type="ws",
                host="127.0.0.1",
                port=5140,
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

# ================================================================================
# 登录路由
# ================================================================================
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
        return JSONResponse({"success": True, "token": token, "instances": [inst.as_dict() for inst in instances]})

# ================================================================================
# 退出登录路由
# ================================================================================
@add_route("/api/logout", methods=["POST"])
async def logout():
    """占位：前端可直接丢弃 token"""
    return True

# ================================================================================
# 实例路由：新增 / 修改
# ================================================================================
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

# ================================================================================
# 日志实时推送： WebSocket
# ================================================================================
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
# ---------------------------- WebSocket 路由 ----------------------------
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

    # ---------------- 异常处理 ----------------
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

# ================================================================================
# 配置管理路由
# ================================================================================
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
    with open("./entari_plugin_webui/backend/configs/entari.yml", "w", encoding="utf-8") as f:
        yaml.dump(body, f, allow_unicode=True, sort_keys=False)
    return JSONResponse({"success": True})
