from __future__ import annotations

import asyncio
from datetime import datetime
from secrets import token_hex

from launart import Launart, any_completed
from launart.status import Phase
from loguru import logger
from starlette.responses import JSONResponse, Response
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket
from yarl import URL

from satori import Api, Event, EventType, LoginStatus
from satori.exception import ActionFailed
from satori.model import Login, User, MessageObject, Channel, ChannelType
from satori.server import Request
from satori.server.route import MessageParam
from satori.server.adapter import Adapter as BaseAdapter
from satori.utils import decode, encode

from .core.security import is_local_mode


async def message_receive(raw: dict, conn: WebsocketConnection):
    user_id = raw["user_id"]
    message_id = raw["message_id"]
    message_content = raw["message_content"]
    return Event(
        EventType.MESSAGE_CREATED,
        datetime.now(),
        conn.adapter.logins[conn.session_id],
        channel=Channel("chat", ChannelType.DIRECT),
        user=User(user_id, user_id),
        message=MessageObject(id=message_id, content=message_content),
    )


class WebsocketConnection:
    connection: WebSocket

    def __init__(self, adapter: WebUIAdapter, connection: WebSocket, session_id: str = "entari"):
        self.adapter = adapter
        self.connection = connection
        self.session_id = session_id
        self.close_signal: asyncio.Event = asyncio.Event()
        self.response_waiters: dict[str, asyncio.Future] = {}

    @property
    def alive(self) -> bool:
        return not self.close_signal.is_set()

    async def message_receive(self):

        while True:
            message = await self.connection.receive()

            if message["type"] == "websocket.disconnect":
                break
            yield self, decode(message["text"])
        self.close_signal.set()

    async def message_handle(self):
        async for conn, data in self.message_receive():
            print(f"Received message: {data}")
            if token := data.get("token"):
                if token in self.response_waiters:
                    self.response_waiters[token].set_result(data)
                continue
            event_type = data.get("type")
            if event_type == "message_create":
                event = await message_receive(data["data"], self)
            else:
                event = Event(EventType.INTERNAL, datetime.now(), self.adapter.logins[self.session_id])
            event._type = event_type
            event._data = data.get("data")
            asyncio.create_task(self.adapter.server.post(event))

    async def connection_closed(self):
        self.close_signal.set()

    async def call_api(self, action: str, params: dict | None = None) -> dict:
        future = asyncio.get_running_loop().create_future()
        token = token_hex(16)
        self.response_waiters[token] = future
        try:
            await self.send({"action": action, "data": params or {}, "token": token})
            result = await asyncio.wait_for(future, timeout=60)
        finally:
            self.response_waiters.pop(token, None)
        if result["status"] != "ok":
            raise ActionFailed(result.get("error", "Unknown error"), result)
        return result.get("data", {})

    async def send(self, payload: dict) -> None:
        return await self.connection.send_text(encode(payload))


def apply(adapter: WebUIAdapter):
    @adapter.route(Api.MESSAGE_CREATE)
    async def _message_create(request: Request[MessageParam]):
        conn = adapter.connections[request.self_id]
        result = await conn.call_api("message_create", {**request.params})
        return [MessageObject(result["id"], request.params["content"])]


class WebUIAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.connections: dict[str, WebsocketConnection] = {}
        self.logins: dict[str, Login] = {}

        apply(self)

    def ensure(self, platform: str, self_id: str) -> bool:
        return platform == "webui" and self_id == "entari"
    
    async def get_logins(self) -> list[Login]:
        logins = list(self.logins.values())
        for index, login in enumerate(logins):
            login.sn = index
        return logins

    @property
    def required(self) -> set[str]:
        return {"satori-python.server", "asgi.service/uvicorn"}

    @property
    def stages(self) -> set[Phase]:
        return {"preparing", "blocking", "cleanup"}

    def get_routes(self):
        return [
            WebSocketRoute("/api/chat", self.websocket_server_handler),
        ]
    
    async def websocket_server_handler(self, ws: WebSocket):
        sid = None
        if not is_local_mode():
            sid = ws.cookies.get("webui_sid")
            from entari_plugin_webui import _session_store

            if _session_store.get(sid) is None:
                await ws.close(code=1008, reason="Invalid session")
                return

        sid = sid or "entari"
        if sid in self.connections:
            old = self.connections[sid]
            if old.alive:
                await ws.close(code=1008, reason="Duplicate connection")
                return
            self.connections.pop(sid, None)

        await ws.accept()
        conn = WebsocketConnection(self, ws, session_id=sid)
        self.connections[sid] = conn

        if sid not in self.logins:
            self.logins[sid] = Login(
                platform="webui",
                user=User(id=sid, name="Entari"),
                status=LoginStatus.ONLINE,
            )
            await self.server.post(
                Event(EventType.LOGIN_ADDED, datetime.now(), self.logins[sid])
            )
        else:
            self.logins[sid].status = LoginStatus.ONLINE
            await self.server.post(
                Event(EventType.LOGIN_UPDATED, datetime.now(), self.logins[sid])
            )

        try:
            await any_completed(
                conn.message_handle(),
                conn.close_signal.wait(),
            )
        finally:
            await conn.connection_closed()
            self.connections.pop(sid, None)
            if conn.response_waiters:
                for future in conn.response_waiters.values():
                    future.cancel()
            self.logins[sid].status = LoginStatus.OFFLINE
            await self.server.post(
                Event(EventType.LOGIN_REMOVED, datetime.now(), self.logins[sid])
            )

    def get_platform(self) -> str:
        return "webui"

    async def handle_internal(self, request: Request, path: str) -> Response:
        if path.startswith("_api"):
            self_id = request.self_id
            return JSONResponse(await self.connections[self_id].call_api(path[5:], await request.origin.json()))
        async with self.server.session.get(path) as resp:
            return Response(await resp.read())

    async def launch(self, manager: Launart):
        async with self.stage("preparing"):
            pass

        async with self.stage("blocking"):
            await manager.status.wait_for_sigexit()

        async with self.stage("cleanup"):
            pass
