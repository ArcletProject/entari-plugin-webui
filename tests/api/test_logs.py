import pytest


def test_ws_local_mode_history(client):
    from entari_plugin_webui.core.security import set_local_mode

    set_local_mode(True)
    with client.websocket_connect("/ws/logs") as ws:
        data = ws.receive_json()
        assert data["type"] == "history"
        assert isinstance(data["data"], str)


def test_ws_remote_no_session_denied(client):
    from starlette.websockets import WebSocketDisconnect as WSD

    from entari_plugin_webui.core.security import set_local_mode

    set_local_mode(False)
    with pytest.raises(WSD), client.websocket_connect("/ws/logs") as ws:
        ws.receive()
