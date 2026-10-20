from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _mk(pid="p1", available=True, metadata=True):
    plug = MagicMock()
    plug.id = pid
    plug.path = "mod.path"
    plug.uid = None
    plug._config_key = pid
    plug.is_available = available
    plug.available = True
    plug.is_static = False
    plug.reusable = True
    plug.config = {}
    plug.subplugins = set()
    plug.module = SimpleNamespace(__file__=None)
    if metadata:
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
    else:
        plug.metadata = None
    return plug


def test_fragment_parts_only_matches_first_segment(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    assert ps._fragment_parts((".bar",), ".bar") == ()
    assert ps._fragment_parts((".bar", "baz"), ".bar") == ("baz",)
    assert ps._fragment_parts((".bar.baz",), ".bar") is None


def test_has_own_schema_for_child_fragment(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    monkeypatch.setattr(
        ps,
        "_schema_fragments",
        {"parent": [SimpleNamespace(path=(".child",), fragment={}, replace=False)]},
        raising=False,
    )
    monkeypatch.setattr(
        ps,
        "plugin_service",
        SimpleNamespace(_subplugined={"parent.child": "parent"}, plugins={}, _unloaded=set()),
    )
    child = _mk("parent.child")
    child._config_key = "parent"
    assert ps._has_own_schema(child) is True


def test_serialize_metadata_less_and_state(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    monkeypatch.setattr(ps, "is_project_module", lambda m: False)
    monkeypatch.setattr(ps, "get_plugin_references", lambda p: set())
    monkeypatch.setattr(ps, "get_plugin_referents", lambda p: set())
    monkeypatch.setattr(ps, "_schema_fragments", {}, raising=False)

    s = ps.serialize_plugin(_mk("entari_plugin_plain", metadata=False))
    assert s["has_metadata"] is False
    assert s["has_config_schema"] is False
    assert s["name"] == "entari_plugin_plain"
    assert s["state"] == "enabled"
    assert s["parent_enabled"] is None

    p = _mk()
    p.config = {"$disable": "os.name == 'nt'"}
    p.is_available = False
    s = ps.serialize_plugin(p)
    assert s["state"] == "disabled"
    assert s["disable_expr"] == "os.name == 'nt'"


def test_serialize(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    monkeypatch.setattr(ps, "get_plugin_references", lambda p: set())
    monkeypatch.setattr(ps, "get_plugin_referents", lambda p: set())
    s = ps.serialize_plugin(_mk())
    assert s["id"] == "p1"
    assert s["enabled"] is True
    assert s["configurable"] is False


@pytest.mark.asyncio
async def test_toggle(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk()

    async def _enable(plugin_id: str) -> bool:
        assert plugin_id == "p1"
        _ = p.enable()
        return True

    monkeypatch.setattr(ps, "enable_plugin", _enable)
    await ps.toggle_plugin("p1", enable=True)
    p.enable.assert_called_once()


@pytest.mark.asyncio
async def test_reload(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk()
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)

    async def _reload(i):
        assert i == "p1"
        return True

    monkeypatch.setattr(ps, "_reload_plugin", _reload)
    assert await ps.reload_plugin("p1") is True


def test_update_config(monkeypatch):
    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk()
    p._config_key = "p1"
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(cs, "find_plugin", lambda i: p)
    monkeypatch.setattr(cs, "plugin_service", SimpleNamespace(_subplugined={}, plugins={"p1": p}), raising=False)
    data = {"plugins": {"p1": {}}}
    cfg = MagicMock()
    cfg.basic = {}
    cfg.plugin = data["plugins"]
    cfg.data = data
    cfg.save = MagicMock()
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    ps.update_plugin_config("p1", {"x": 1})
    assert cfg.plugin["p1"] == {"x": 1}
    cfg.save.assert_called_once()
