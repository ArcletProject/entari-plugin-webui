def test_list_plugins(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P

    monkeypatch.setattr(P, "list_plugins", lambda: [{"id": "echo", "name": "Echo", "enabled": True}])
    r = client.get("/api/plugins")
    assert r.status_code == 200
    assert r.json()["data"][0]["id"] == "echo"


def test_toggle(client, monkeypatch):
    from entari_plugin_webui.api import plugins as P

    called = {}
    monkeypatch.setattr(P, "toggle_plugin", lambda pid, *, enable: called.update(pid=pid, en=enable) or True)
    r = client.post("/api/plugins/echo/toggle", json={"enable": False}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert r.status_code == 200
    assert r.json()["enabled"] is False


def test_menus(client):
    r = client.get("/api/menus")
    labels = [m["label_key"] for m in r.json()["menus"]]
    assert labels == ["menu.dashboard", "menu.plugins", "menu.market", "menu.config", "menu.logs", "menu.chat"]
