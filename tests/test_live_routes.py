def test_ws_history_and_increment(client):
    from entari_plugin_webui.core.security import set_local_mode
    from entari_plugin_webui.core.log_stream import get_log_buffer

    set_local_mode(True)
    buf = get_log_buffer()
    buf.clear()
    buf.write("hello\n")
    with client.websocket_connect("/ws/logs") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "history" and "hello" in msg["data"]
        buf.write("world\n")
        msg2 = ws.receive_json()
        assert msg2["type"] == "log" and "world" in msg2["data"]
