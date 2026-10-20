def test_list_plugins(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P

    monkeypatch.setattr(P, "list_plugins", lambda: [{"id": "echo", "name": "Echo", "enabled": True}])
    r = client.get("/api/plugins")
    assert r.status_code == 200
    assert r.json()["data"][0]["id"] == "echo"


def test_toggle(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P

    called = {}

    async def _toggle(plugin_id: str, *, enable: bool) -> dict:
        called["plugin_id"] = plugin_id
        called["enable"] = enable
        return {"id": "echo", "enabled": False}

    monkeypatch.setattr(P, "toggle_plugin", _toggle)
    r = client.post("/api/plugins/echo/toggle", json={"enable": False}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert r.status_code == 200
    assert r.json()["data"]["enabled"] is False


def test_unloaded_list(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P

    monkeypatch.setattr(P, "list_unloaded_plugins", lambda: [{"key": "demo", "display_key": "?demo"}])
    r = client.get("/api/plugins/unloaded")
    assert r.status_code == 200
    assert r.json()["plugins"][0]["display_key"] == "?demo"


def test_load_unloaded(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P

    async def _load(key):
        return {"id": key, "unloaded": False}

    monkeypatch.setattr(P, "load_unloaded", _load)
    r = client.post("/api/plugins/load", json={"key": "demo"}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert r.status_code == 200
    assert r.json()["data"]["id"] == "demo"


def test_detail_attaches_market(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P
    from entari_plugin_webui.services import market_service as MS

    monkeypatch.setattr(P, "get_plugin", lambda pid: {"id": pid, "path": "entari_plugin_demo"})

    async def _find(pid, module):
        return {"name": "demo", "pip_name": "entari-demo"}

    monkeypatch.setattr(MS, "find_market_entry", _find)
    r = client.get("/api/plugins/demo")
    assert r.json()["data"]["market"]["pip_name"] == "entari-demo"


def test_menus(client):
    r = client.get("/api/menus")
    labels = [m["label_key"] for m in r.json()["menus"]]
    assert labels == ["menu.dashboard", "menu.settings", "menu.plugins", "menu.market", "menu.logs", "menu.chat"]
