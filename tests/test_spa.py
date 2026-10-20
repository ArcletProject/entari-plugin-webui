from __future__ import annotations


def _frontend(monkeypatch, tmp_path):
    import entari_plugin_webui as webui

    (tmp_path / "index.html").write_text("<!doctype html><div id='app'>SPA_INDEX</div>", encoding="utf-8")
    monkeypatch.setattr(webui, "_FRONTEND_DIR", tmp_path)
    return tmp_path


def test_spa_route_serves_index(client, monkeypatch, tmp_path):
    _frontend(monkeypatch, tmp_path)

    r = client.get("/market")

    assert r.status_code == 200
    assert "SPA_INDEX" in r.text


def test_spa_route_serves_index_for_nested_path(client, monkeypatch, tmp_path):
    _frontend(monkeypatch, tmp_path)

    r = client.get("/extension/demo/sub")

    assert r.status_code == 200
    assert "SPA_INDEX" in r.text


def test_spa_route_keeps_missing_api_as_json_404(client, monkeypatch, tmp_path):
    _frontend(monkeypatch, tmp_path)

    r = client.get("/api/definitely-missing")

    assert r.status_code == 404
    assert r.json() == {"detail": "Not Found"}


def test_spa_route_keeps_missing_asset_404(client, monkeypatch, tmp_path):
    _frontend(monkeypatch, tmp_path)

    r = client.get("/missing.js")

    assert r.status_code == 404
