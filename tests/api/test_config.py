def test_list_sections(client, monkeypatch):
    from entari_plugin_webui.api import config as C

    monkeypatch.setattr(C, "list_sections", lambda: {"sections": ["basic"], "plugin_sections": [], "data": {}})
    r = client.get("/api/config")
    assert r.json()["success"] is True


def test_get_basic(client, monkeypatch):
    from entari_plugin_webui.api import config as C

    monkeypatch.setattr(C, "get_section", lambda s: {"prefix": ["/"]})
    r = client.get("/api/config/basic")
    assert r.json()["data"]["prefix"] == ["/"]


def test_get_schema(client, monkeypatch):
    from entari_plugin_webui.api import config as C

    monkeypatch.setattr(C, "get_schema_for_section", lambda s: {"schema": {"type": "object"}})
    r = client.get("/api/config/basic/schema")
    assert r.json()["schema"]["type"] == "object"


def test_update(client, monkeypatch):
    from entari_plugin_webui.api import config as C

    captured = {}
    monkeypatch.setattr(C, "update_section", lambda s, d: captured.update(s=s, d=d))
    headers = {"X-Requested-With": "XMLHttpRequest"}
    r = client.put("/api/config/basic", json={"data": {"prefix": ["/a"]}}, headers=headers)
    assert r.json()["success"] is True
    assert captured["d"] == {"prefix": ["/a"]}
