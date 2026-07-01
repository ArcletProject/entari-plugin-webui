def test_manifest(client, monkeypatch):
    from entari_plugin_webui.api import extensions as E

    monkeypatch.setattr(E, "get_all_menus", lambda: [{"label_key": "x", "path": "/x", "order": 1}])
    monkeypatch.setattr(E, "get_all_pages", lambda: [])
    monkeypatch.setattr(E, "get_permissions", lambda: [])
    r = client.get("/api/extensions/manifest")
    assert r.json()["menus"][0]["label_key"] == "x"
