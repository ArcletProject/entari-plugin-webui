def test_stats(client, monkeypatch):
    from entari_plugin_webui.api import stats as S

    async def _get():
        return {
            "today_messages": 5,
            "week_messages": [1, 2, 3, 4, 5, 6, 7],
            "total_messages": 21,
            "plugins_enabled": 2,
            "plugins_total": 3,
            "runtime_minutes": 0,
            "start_time": "x",
        }

    monkeypatch.setattr(S, "get_stats", _get)
    r = client.get("/api/stats")
    assert r.json()["today_messages"] == 5
