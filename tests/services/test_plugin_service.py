from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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
    monkeypatch.setattr(ps, "evaluate_disable", lambda expr: True)
    s = ps.serialize_plugin(p)
    assert s["state"] == "disabled"
    assert s["disable_expr"] == "os.name == 'nt'"


def test_serialize_disable_expr_false_is_enabled(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    monkeypatch.setattr(ps, "get_plugin_references", lambda p: set())
    monkeypatch.setattr(ps, "get_plugin_referents", lambda p: set())
    monkeypatch.setattr(ps, "evaluate_disable", lambda expr: False)
    p = _mk(available=True)
    p.config = {"$disable": "os.name == 'nt'"}
    s = ps.serialize_plugin(p)
    assert s["state"] == "enabled"
    assert s["disable_expr"] == "os.name == 'nt'"


def test_serialize_disable_expr_true_is_disabled(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    monkeypatch.setattr(ps, "get_plugin_references", lambda p: set())
    monkeypatch.setattr(ps, "get_plugin_referents", lambda p: set())
    monkeypatch.setattr(ps, "evaluate_disable", lambda expr: True)
    p = _mk(available=False)
    p.config = {"$disable": "os.name == 'nt'"}
    s = ps.serialize_plugin(p)
    assert s["state"] == "disabled"


def test_serialize(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    monkeypatch.setattr(ps, "get_plugin_references", lambda p: set())
    monkeypatch.setattr(ps, "get_plugin_referents", lambda p: set())
    s = ps.serialize_plugin(_mk())
    assert s["id"] == "p1"
    assert s["enabled"] is True
    assert s["configurable"] is False


def _capture_mutation(monkeypatch, ps, entry):
    from arclet.entari.config.model import ApplyReport

    captured = {}

    async def fake_mutate(section, mutate, **kwargs):
        captured["section"] = section
        captured["entry"] = mutate(entry)
        return ApplyReport(ok=True, applied=True)

    from entari_plugin_webui.services import config_service as cs

    monkeypatch.setattr(cs, "mutate_section", fake_mutate)
    return captured


@pytest.mark.asyncio
async def test_toggle_top_level_writes_disable_via_config(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk("demo")
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(ps, "get_plugin", lambda pid: {"id": pid})
    captured = _capture_mutation(monkeypatch, ps, {"x": 1})

    await ps.toggle_plugin("demo", enable=False)

    assert captured["section"] == "plugins:demo"
    assert captured["entry"] == {"x": 1, "$disable": True}


@pytest.mark.asyncio
async def test_toggle_top_level_enable_clears_disable_and_optional(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk("demo")
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(ps, "get_plugin", lambda pid: {"id": pid})
    captured = _capture_mutation(monkeypatch, ps, {"x": 1, "$disable": True, "$optional": True})

    await ps.toggle_plugin("demo", enable=True)

    assert captured["section"] == "plugins:demo"
    assert captured["entry"] == {"x": 1}


@pytest.mark.asyncio
async def test_toggle_child_uses_child_section(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    parent = _mk("demo_parent")
    child = _mk("demo_parent.child")
    child._config_key = "demo_parent"
    child.config = {"$optional": True}
    monkeypatch.setattr(ps, "find_plugin", lambda i: child)
    monkeypatch.setattr(
        ps,
        "plugin_service",
        SimpleNamespace(
            _subplugined={"demo_parent.child": "demo_parent"},
            plugins={"demo_parent": parent, "demo_parent.child": child},
            _unloaded=set(),
        ),
    )
    monkeypatch.setattr(ps, "get_plugin", lambda pid: {"id": pid})
    captured = _capture_mutation(monkeypatch, ps, {"$optional": True})

    await ps.toggle_plugin("demo_parent.child", enable=True)

    assert captured["section"] == "plugins:demo_parent.child"
    assert captured["entry"] == {}


@pytest.mark.asyncio
async def test_toggle_child_rejected_when_parent_disabled(monkeypatch):
    from entari_plugin_webui.core.error import PluginError
    from entari_plugin_webui.services import plugin_service as ps

    parent = _mk("demo_parent", available=False)
    child = _mk("demo_parent.child")
    monkeypatch.setattr(ps, "find_plugin", lambda i: child)
    monkeypatch.setattr(
        ps,
        "plugin_service",
        SimpleNamespace(
            _subplugined={"demo_parent.child": "demo_parent"},
            plugins={"demo_parent": parent},
            _unloaded=set(),
        ),
    )
    with pytest.raises(PluginError):
        await ps.toggle_plugin("demo_parent.child", enable=True)


@pytest.mark.asyncio
async def test_reload_child_uses_reload_subplugin(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    child = _mk("demo_parent.child")
    monkeypatch.setattr(ps, "find_plugin", lambda i: child)
    monkeypatch.setattr(ps, "plugin_service", SimpleNamespace(_subplugined={"demo_parent.child": "demo_parent"}))
    called = {}

    async def _sub(pid):
        called["id"] = pid
        return True

    monkeypatch.setattr(ps, "_reload_subplugin", _sub)
    assert await ps.reload_plugin("demo_parent.child") is True
    assert called["id"] == "demo_parent.child"


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


async def test_update_config(monkeypatch):
    import copy
    from pathlib import Path
    from types import SimpleNamespace

    from arclet.entari.config.model import ApplyReport

    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk()
    p._config_key = "p1"
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(cs, "find_plugin", lambda i: p)
    monkeypatch.setattr(cs, "plugin_service", SimpleNamespace(_subplugined={}, plugins={"p1": p}), raising=False)

    lives = []
    for _ in range(2):
        cfg = MagicMock()
        cfg.basic = {}
        cfg.data = {"plugins": {"p1": {}}}
        cfg.plugin = cfg.data["plugins"]
        cfg.path = Path("/tmp/entari.yml")
        cfg.plugin_extra_files = []
        cfg.remap_records = MagicMock()
        cfg.save = MagicMock()
        lives.append(cfg)
    live, detached = lives
    detached.data = copy.deepcopy(live.data)
    detached.plugin = detached.data["plugins"]

    cfg_cls = MagicMock(instance=live)
    cfg_cls.load = MagicMock(return_value=detached)
    monkeypatch.setattr(cs, "EntariConfig", cfg_cls)
    monkeypatch.setattr(cs, "compute_etag", lambda cfg: "etag")

    async def _post(event, **kwargs):
        return SimpleNamespace(value=ApplyReport(ok=True, applied=True))

    monkeypatch.setattr(cs, "post", _post)
    report = await ps.update_plugin_config("p1", {"x": 1}, if_match="etag")
    assert report.applied
    assert detached.plugin["p1"] == {"x": 1}
    detached.save.assert_called_once()
    live.save.assert_not_called()


@pytest.mark.asyncio
async def test_unload_writes_optional_via_config(monkeypatch):
    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk("demo")
    p.path = "entari_plugin_demo"
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(ps, "serialize_plugin", lambda plug, _force=False: {"id": plug.id, "path": plug.path})
    monkeypatch.setattr(cs, "get_plugin_config_path", lambda pid: ["demo"])
    captured = _capture_mutation(monkeypatch, ps, {"x": 1, "$disable": True})
    ps._unloaded_snapshots.clear()

    out = await ps.unload_plugin("demo")

    assert captured["section"] == "plugins:demo"
    assert captured["entry"] == {"x": 1, "$optional": True}
    assert out["unloaded"] is True
    assert "demo" in ps._unloaded_snapshots


def test_list_unloaded_plugins_reads_optional(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    cfg = MagicMock()
    cfg.plugin = {"demo": {"$optional": True, "x": 1}}
    cfg.data = {"plugins": {"demo": {"$optional": True, "x": 1}}}
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    monkeypatch.setattr(ps, "plugin_service", SimpleNamespace(plugins={}, _subplugined={}, _unloaded=set()))
    ps._unloaded_snapshots.clear()

    out = ps.list_unloaded_plugins()
    assert out[0]["key"] == "demo"
    assert out[0]["display_key"] == "?demo"
    assert out[0]["state"] == "unloaded"
    assert out[0]["config"] == {"x": 1}


@pytest.mark.asyncio
async def test_load_unloaded_clears_optional_via_config(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    cfg = MagicMock()
    cfg._plugin_names = {}
    cfg.plugin_prefixes = {}
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    loaded = _mk("entari_plugin_demo")
    loaded.is_available = True
    monkeypatch.setattr(
        ps,
        "find_plugin",
        lambda pid: loaded if pid == "entari_plugin_demo" else None,
    )
    monkeypatch.setattr(ps, "serialize_plugin", lambda plug, _force=False: {"id": plug.id})
    captured = _capture_mutation(monkeypatch, ps, {"$optional": True, "x": 1})

    out = await ps.load_unloaded("demo")

    assert captured["section"] == "plugins:demo"
    assert captured["entry"] == {"x": 1}
    assert out["id"] == "entari_plugin_demo"


@pytest.mark.asyncio
async def test_load_unloaded_failure_raises(monkeypatch):
    from arclet.entari.config.model import ApplyError, ApplyReport

    from entari_plugin_webui.core.error import PluginError
    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    cfg = MagicMock()
    cfg._plugin_names = {}
    cfg.plugin_prefixes = {}
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    monkeypatch.setattr(ps, "find_plugin", lambda pid: None)

    async def fake_mutate(section, mutate, **kwargs):
        mutate({"$optional": True, "x": 1})
        return ApplyReport(ok=False, applied=True, errors=[ApplyError("demo", "boom")])

    monkeypatch.setattr(cs, "mutate_section", fake_mutate)

    with pytest.raises(PluginError):
        await ps.load_unloaded("demo")


@pytest.mark.asyncio
async def test_unload_disabled_plugin_preserves_body(monkeypatch):
    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk("demo")
    p.path = "entari_plugin_demo"
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(ps, "serialize_plugin", lambda plug, _force=False: {"id": plug.id})
    monkeypatch.setattr(cs, "get_plugin_config_path", lambda pid: ["demo"])
    captured = _capture_mutation(monkeypatch, ps, {"x": 1, "$disable": True})

    await ps.unload_plugin("demo")

    assert captured["section"] == "plugins:demo"
    assert captured["entry"] == {"x": 1, "$optional": True}


@pytest.mark.asyncio
async def test_unload_snapshot_keyed_by_config_key(monkeypatch):
    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk("entari_plugin_demo")
    p._config_key = "demo"
    p.path = "entari_plugin_demo"
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)
    monkeypatch.setattr(ps, "serialize_plugin", lambda plug, _force=False: {"id": plug.id, "name": plug.id})
    monkeypatch.setattr(ps, "plugin_service", SimpleNamespace(plugins={}, _subplugined={}, _unloaded=set()))
    plugins = {"demo": {"x": 1}}
    cfg = MagicMock()
    cfg.data = {"plugins": plugins}
    cfg.plugin = plugins
    cfg._plugin_names = {}
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    monkeypatch.setattr(cs, "get_plugin_config_path", lambda pid: ["demo"])
    _capture_mutation(monkeypatch, ps, {"x": 1})
    ps._unloaded_snapshots.clear()

    await ps.unload_plugin("entari_plugin_demo")

    assert "demo" in ps._unloaded_snapshots
    assert "entari_plugin_demo" not in ps._unloaded_snapshots


@pytest.mark.asyncio
async def test_unload_rejects_static_rootless_and_child(monkeypatch):
    from entari_plugin_webui.core.error import PluginError
    from entari_plugin_webui.services import plugin_service as ps

    static = _mk("p_static")
    static.is_static = True
    monkeypatch.setattr(ps, "find_plugin", lambda i: static)
    with pytest.raises(PluginError):
        await ps.unload_plugin("p_static")

    rootless = _mk("$rootless")
    monkeypatch.setattr(ps, "find_plugin", lambda i: rootless)
    with pytest.raises(PluginError):
        await ps.unload_plugin("$rootless")

    child = _mk("parent.child")
    monkeypatch.setattr(ps, "find_plugin", lambda i: child)
    monkeypatch.setattr(ps, "plugin_service", SimpleNamespace(_subplugined={"parent.child": "parent"}))
    with pytest.raises(PluginError):
        await ps.unload_plugin("parent.child")


def test_list_unloaded_plugins_reads_raw_question_mark(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    cfg = MagicMock()
    cfg.plugin = {"?demo": {"x": 1}}
    cfg.data = {"plugins": {"?demo": {"x": 1}}}
    cfg._plugin_names = {}
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    monkeypatch.setattr(ps, "plugin_service", SimpleNamespace(plugins={}, _subplugined={}, _unloaded=set()))
    ps._unloaded_snapshots.clear()

    out = ps.list_unloaded_plugins()
    assert out[0]["key"] == "demo"
    assert out[0]["display_key"] == "?demo"
    assert out[0]["config"] == {"x": 1}


@pytest.mark.asyncio
async def test_load_unloaded_raw_question_mark(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    cfg = MagicMock()
    cfg._plugin_names = {}
    cfg.plugin_prefixes = {}
    monkeypatch.setattr(ps, "EntariConfig", MagicMock(instance=cfg))
    loaded = _mk("entari_plugin_demo")
    monkeypatch.setattr(
        ps,
        "find_plugin",
        lambda pid: loaded if pid == "entari_plugin_demo" else None,
    )
    monkeypatch.setattr(ps, "serialize_plugin", lambda plug, _force=False: {"id": plug.id})
    captured = _capture_mutation(monkeypatch, ps, {"$optional": True, "x": 1})

    out = await ps.load_unloaded("demo")

    assert out["id"] == "entari_plugin_demo"
    assert captured["entry"] == {"x": 1}


@pytest.mark.asyncio
async def test_uninstall_plugin_unloads_then_deletes(monkeypatch):
    from entari_plugin_webui.services import plugin_service as ps

    p = _mk("demo")
    p.path = "entari_plugin_demo"
    calls = []
    monkeypatch.setattr(ps, "find_plugin", lambda i: p)

    async def unload(pid):
        calls.append(("unload", pid))
        return {"id": pid, "unloaded": True}

    async def market(pid, module):
        return {"name": "demo-pkg", "pip_name": "entari-demo"}

    async def delete(name):
        calls.append(("delete", name))
        return "tid"

    monkeypatch.setattr(ps, "unload_plugin", unload)
    monkeypatch.setattr(
        ps,
        "market_service",
        SimpleNamespace(find_market_entry=market, start_uninstall=delete),
        raising=False,
    )
    assert await ps.uninstall_plugin("demo") == "tid"
    assert calls == [("unload", "demo"), ("delete", "demo-pkg")]
