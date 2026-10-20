def test_list(client, monkeypatch):
    from entari_plugin_webui.api import market as M

    async def _l():
        return {"plugins": [{"name": "demo", "installed": False}], "fallback": False}

    monkeypatch.setattr(M, "list_plugins", _l)
    r = client.get("/api/market/plugins")
    assert r.json()["plugins"][0]["name"] == "demo"


def test_builtins_list(client, monkeypatch):
    from entari_plugin_webui.api import market as M

    monkeypatch.setattr(M, "list_builtins", lambda: [{"name": "echo", "enabled": True}])
    r = client.get("/api/market/builtins")
    assert r.status_code == 200
    assert r.json() == {"success": True, "data": [{"name": "echo", "enabled": True}]}


def test_builtin_toggle(client, monkeypatch):
    from entari_plugin_webui.api import market as M

    calls = []

    async def _toggle(name, enable):
        calls.append((name, enable))

    monkeypatch.setattr(M, "set_builtin_enabled", _toggle)
    r = client.post(
        "/api/market/builtins/echo/toggle",
        json={"enable": False},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert r.status_code == 200
    assert r.json() == {"success": True, "enabled": False}
    assert calls == [("echo", False)]


def test_install_success(client, monkeypatch):
    from entari_plugin_webui.api import market as M

    async def _i(name):
        return "fake-tid"

    monkeypatch.setattr(M, "start_install", _i)
    r = client.post("/api/market/install", json={"name": "x"}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert r.status_code == 200
    assert r.json() == {"success": True, "task_id": "fake-tid"}


def test_install_unknown_400(client, monkeypatch):
    from entari_plugin_webui.api import market as M
    from entari_plugin_webui.services.market_service import UnknownPlugin

    async def _i(name):
        raise UnknownPlugin(name)

    monkeypatch.setattr(M, "start_install", _i)
    r = client.post("/api/market/install", json={"name": "x"}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert r.status_code == 400
    assert r.json() == {"success": False, "code": "unknown_plugin", "message": "x"}


def test_builtin_unload_and_load(client, monkeypatch):
    from entari_plugin_webui.api import market as M

    calls = []

    async def _unload(name):
        calls.append(("unload", name))

    async def _load(name):
        calls.append(("load", name))
        return True

    monkeypatch.setattr(M, "set_builtin_unloaded", _unload)
    monkeypatch.setattr(M, "load_builtin", _load)
    headers = {"X-Requested-With": "XMLHttpRequest"}
    r = client.post("/api/market/builtins/echo/unload", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"success": True}
    r = client.post("/api/market/builtins/echo/load", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"success": True}
    assert calls == [("unload", "echo"), ("load", "echo")]


def test_uninstall_unloads_first(client, monkeypatch):
    from entari_plugin_webui.api import market as M

    calls = []

    async def _unload(name):
        calls.append(("unload", name))

    async def _delete(name):
        calls.append(("delete", name))
        return "tid"

    monkeypatch.setattr(M, "unload_market_plugin", _unload)
    monkeypatch.setattr(M, "start_uninstall", _delete)
    r = client.post("/api/market/uninstall", json={"name": "demo"}, headers={"X-Requested-With": "XMLHttpRequest"})
    assert r.status_code == 200
    assert r.json() == {"success": True, "task_id": "tid"}
    assert calls == [("unload", "demo"), ("delete", "demo")]
