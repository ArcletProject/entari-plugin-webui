from __future__ import annotations

import asyncio

from entari_plugin_server import add_websocket_route
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..core.log_stream import get_log_buffer
from ..core.security import is_local_mode


@add_websocket_route("/ws/logs")
async def websocket_logs(ws: WebSocket) -> None:
    if not is_local_mode():
        sid = ws.cookies.get("webui_sid")
        from entari_plugin_webui import _session_store

        if _session_store.get(sid) is None:
            await ws.close(code=1008)
            return

    await ws.accept()
    buffer = get_log_buffer()
    history_data, last_pos = buffer.get_recent(100)
    await ws.send_json({"type": "history", "data": history_data})
    try:
        while True:
            text, last_pos = buffer.get_new_since(last_pos)
            if text:
                await ws.send_json({"type": "log", "data": text})
            await asyncio.sleep(0.5)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except Exception:  # noqa: BLE001
        pass
    finally:
        from contextlib import suppress

        with suppress(Exception):
            await ws.close()
