def test_list_sections(client, monkeypatch):
    from entari_plugin_webui.api import config as C

    monkeypatch.setattr(C, "list_sections", lambda: {"sections": ["basic"], "plugin_sections": [], "data": {}})
    r = client.get("/api/config")
    assert r.json()["success"] is True


def test_get_basic(client, monkeypatch):
    from entari_plugin_webui.api import config as C

    monkeypatch.setattr(C, "get_section", lambda s: {"prefix": ["/"]})
    monkeypatch.setattr(C, "get_etag", lambda: "etag")
    r = client.get("/api/config/basic")
    assert r.json()["data"]["prefix"] == ["/"]
    assert r.json()["etag"] == "etag"


def test_get_schema(client, monkeypatch):
    from entari_plugin_webui.api import config as C

    monkeypatch.setattr(C, "get_schema_for_section", lambda s: {"schema": {"type": "object"}})
    r = client.get("/api/config/basic/schema")
    assert r.json()["schema"]["type"] == "object"


def test_update(client, monkeypatch):
    from arclet.entari.config.model import ApplyReport

    from entari_plugin_webui.api import config as C

    captured = {}

    async def _update(section, data, *, if_match=None):
        captured.update(section=section, data=data, if_match=if_match)
        return ApplyReport(ok=True, applied=True, changed_basic=["prefix"])

    monkeypatch.setattr(C, "update_section", _update)
    monkeypatch.setattr(C, "get_section", lambda s: {"prefix": ["/a"]})
    monkeypatch.setattr(C, "get_etag", lambda: "etag")
    headers = {"X-Requested-With": "XMLHttpRequest", "If-Match": "etag"}
    r = client.put("/api/config/basic", json={"data": {"prefix": ["/a"]}}, headers=headers)
    assert r.json()["success"] is True
    assert r.json()["apply"]["changed_basic"] == ["prefix"]
    assert r.json()["etag"] == "etag"
    assert captured["data"] == {"prefix": ["/a"]}
    assert captured["if_match"] == "etag"
