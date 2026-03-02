"""WebSocket 路由"""

import asyncio
from ansi2html import Ansi2HTMLConverter

from fastapi import WebSocket, WebSocketDisconnect

from entari_plugin_server import add_websocket_route

from ..utils.log_stream import get_log_buffer


# ANSI 转 HTML 转换器
_converter = Ansi2HTMLConverter(inline=True, scheme="xterm")


def register_ws_routes():
    """注册 WebSocket 路由"""
    pass  # 路由通过装饰器注册


@add_websocket_route("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """
    实时日志 WebSocket
    
    连接时先推送缓冲区中的历史日志，然后持续推送新日志
    """
    await websocket.accept()
    
    buffer = get_log_buffer()
    last_position = 0
    
    try:
        # 先发送历史日志
        history = buffer.get_recent(100)
        if history:
            await websocket.send_json({
                "type": "history",
                "data": history
            })
        last_position = buffer.position
        
        # 持续推送新日志
        while True:
            await asyncio.sleep(0.5)  # 500ms 轮询间隔
            
            new_logs, last_position = buffer.get_new_since(last_position)
            if new_logs:
                await websocket.send_json({
                    "type": "log",
                    "data": new_logs
                })
    
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
