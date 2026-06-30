from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _mk(pid="p1", available=True):
    plug = MagicMock()
    plug.id = pid
    plug.path = "mod.path"
    plug.uid = None
    plug.is_available = available
    plug.available = True
    plug.is_static = False
    plug.reusable = True
    plug.config = {"k": "v"}
    plug.subplugins = set()
    meta = MagicMock()
    meta.name = pid
    meta.version = "1.0"
    meta.description = "desc"
    meta.license = "MIT"
    meta.author = [{"name": "x"}]
    meta.urls = None
    meta.classifier = []
    meta.requirements = []
    meta.config = None
    plug.metadata = meta
    return plug


def test_serialize(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    monkeypatch.setattr(ps, "get_plugin_references", lambda p: set())
    monkeypatch.setattr(ps, "get_plugin_referents", lambda p: set())
    s = ps.serialize_plugin(_mk())
    assert s["id"] == "p1"
    assert s["enabled"] is True
    assert s["configurable"] is False


def test_toggle(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk()
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    ps.toggle_plugin("p1", enable=True)
    p.enable.assert_called_once()


@pytest.mark.asyncio
async def test_reload(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk()
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(ps, "enable_plugin", lambda *a, **k: None)

    async def _unload(i):
        return True

    monkeypatch.setattr(ps, "unload_plugin_async", _unload)
    monkeypatch.setattr(ps, "load_plugin", lambda i: p)
    assert await ps.reload_plugin("p1") is True


def test_update_config(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk()
    p._config_key = "p1"
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    cfg = MagicMock()
    cfg.plugin = {"p1": {}}
    cfg.save = MagicMock()
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    ps.update_plugin_config("p1", {"x": 1})
    assert cfg.plugin["p1"] == {"x": 1}
    cfg.save.assert_called_once()
