from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from pydantic import BaseModel


def _cfg(data):
    cfg = MagicMock()
    cfg.basic = data.get("basic", {})
    cfg.plugin = data.get("plugins", {})
    cfg.data = data
    cfg.save = MagicMock()
    return cfg


def _plugin(plugin_id, config_key, *, subplugins=(), metadata_config=None):
    plug = MagicMock()
    plug.id = plugin_id
    plug._config_key = config_key
    plug.subplugins = list(subplugins)
    if metadata_config is None:
        plug.metadata = None
    else:
        plug.metadata = MagicMock(config=metadata_config, description="demo", name=plugin_id)
    return plug


def _bind_plugins(monkeypatch, cs, plugins, parents=None):
    parents = parents or {}
    table = {p.id: p for p in plugins}
    monkeypatch.setattr(cs, "find_plugin", lambda pid: table.get(pid))
    monkeypatch.setattr(
        cs,
        "plugin_service",
        SimpleNamespace(_subplugined=dict(parents), plugins=table),
        raising=False,
    )
    return table


def test_list_sections(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    plug = _plugin("entari_plugin_webui", "webui")
    monkeypatch.setattr(cs, "get_plugins", lambda subplugged=False: [plug])
    monkeypatch.setattr(cs, "plugin_service", SimpleNamespace(_subplugined={}, plugins={}), raising=False)
    data = {"basic": {"prefix": ["/"]}, "plugins": {"webui": {}}, "adapters": []}
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg(data)))
    out = cs.list_sections()
    assert "basic" in out["sections"]
    assert out["plugin_sections"]["plugins:entari_plugin_webui"] == "entari_plugin_webui"
    assert out["plugin_sections"]["plugins:webui"] == "entari_plugin_webui"


def test_list_sections_includes_subplugins(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    monkeypatch.setattr(cs, "get_plugins", lambda subplugged=False: [parent, child])
    monkeypatch.setattr(
        cs,
        "plugin_service",
        SimpleNamespace(
            _subplugined={"demo_parent.child": "demo_parent"},
            plugins={"demo_parent": parent, "demo_parent.child": child},
        ),
        raising=False,
    )
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg({"plugins": {}})))
    out = cs.list_sections()
    assert out["plugin_sections"]["plugins:demo_parent"] == "demo_parent"
    assert out["plugin_sections"]["plugins:demo_parent.child"] == "demo_parent.child"


def test_get_section_basic(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg({"basic": {"prefix": ["/"]}})))
    out = cs.get_section("basic")
    assert out == {"prefix": ["/"]}


def test_get_section_plugin(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    monkeypatch.setattr(cs, "find_plugin", lambda pid: None)
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg({"plugins": {"webui": {"password": "x"}}})))
    out = cs.get_section("plugins:webui")
    assert out == {"password": "x"}


def test_get_section_subplugin_reads_own_config(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    data = {"plugins": {"demo_parent": {"foo": 1, ".child": {"bar": 2}}}}
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg(data)))
    assert cs.get_section("plugins:demo_parent.child") == {"bar": 2}


def test_get_section_subplugin_deeply_nested(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child.deep"])
    child = _plugin("demo_parent.child.deep", "demo_parent")
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child.deep": "demo_parent"})
    data = {"plugins": {"demo_parent": {".child": {".deep": {"baz": 3}}}}}
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg(data)))
    assert cs.get_section("plugins:demo_parent.child.deep") == {"baz": 3}


def test_get_section_rootless_uses_config_key(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    plug = _plugin("$.commands", ".commands")
    _bind_plugins(monkeypatch, cs, [plug], {"$.commands": "$"})
    data = {"plugins": {".commands": {"use_config_prefix": False}}}
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg(data)))
    assert cs.get_section("plugins:$.commands") == {"use_config_prefix": False}


def _install_detached(monkeypatch, cs, data, *, etag="etag"):
    import copy
    from pathlib import Path
    from types import SimpleNamespace

    from arclet.entari.config.model import ApplyReport

    live = _cfg(data)
    live.path = Path("/tmp/entari.yml")
    live.plugin_extra_files = []
    live.remap_records = MagicMock()
    live._root_plugin_keys = {k for k in data.get("plugins", {}) if not k.startswith("$")}
    detached = _cfg(copy.deepcopy(data))
    detached.path = live.path
    detached.plugin_extra_files = []
    detached.remap_records = MagicMock()
    detached._root_plugin_keys = set(live._root_plugin_keys)

    cfg_cls = MagicMock(instance=live)
    cfg_cls.load = MagicMock(return_value=detached)
    monkeypatch.setattr(cs, "EntariConfig", cfg_cls)
    monkeypatch.setattr(cs, "compute_etag", lambda cfg: etag)

    async def _post(event, **kwargs):
        return SimpleNamespace(value=ApplyReport(ok=True, applied=True))

    monkeypatch.setattr(cs, "post", _post)
    return live, detached


async def test_update_section(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    live, detached = _install_detached(monkeypatch, cs, {"basic": {"prefix": ["/"]}})
    report = await cs.update_section("basic", {"prefix": ["/a"]}, if_match="etag")
    assert report.applied
    assert detached.data["basic"]["prefix"] == ["/a"]
    detached.save.assert_called_once()
    live.save.assert_not_called()


async def test_update_section_subplugin_writes_nested(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    _, detached = _install_detached(
        monkeypatch,
        cs,
        {"plugins": {"demo_parent": {"foo": 1, ".child": {"bar": 2}}}},
    )
    await cs.update_section("plugins:demo_parent.child", {"bar": 3, "baz": 4}, if_match="etag")
    assert detached.data["plugins"]["demo_parent"][".child"] == {"bar": 3, "baz": 4}
    assert "demo_parent.child" not in detached.data["plugins"]
    detached.save.assert_called_once()


async def test_update_section_rootless_writes_config_key(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    plug = _plugin("$.commands", ".commands")
    _bind_plugins(monkeypatch, cs, [plug], {"$.commands": "$"})
    _, detached = _install_detached(
        monkeypatch,
        cs,
        {"plugins": {".commands": {"use_config_prefix": False}}},
    )
    await cs.update_section("plugins:$.commands", {"use_config_prefix": True}, if_match="etag")
    assert detached.data["plugins"][".commands"]["use_config_prefix"] is True
    detached.save.assert_called_once()


async def test_update_section_requires_if_match(monkeypatch):
    from entari_plugin_webui.core.error import ConfigPreconditionRequired
    from entari_plugin_webui.services import config_service as cs

    _install_detached(monkeypatch, cs, {"basic": {}})
    try:
        await cs.update_section("basic", {})
    except ConfigPreconditionRequired as exc:
        assert exc.status == 428
        assert exc.etag == "etag"
    else:
        raise AssertionError("expected ConfigPreconditionRequired")


async def test_update_section_rejects_stale_etag(monkeypatch):
    from entari_plugin_webui.core.error import ConfigConflict
    from entari_plugin_webui.services import config_service as cs

    _install_detached(monkeypatch, cs, {"basic": {}})
    try:
        await cs.update_section("basic", {}, if_match="stale")
    except ConfigConflict as exc:
        assert exc.status == 409
        assert exc.etag == "etag"
    else:
        raise AssertionError("expected ConfigConflict")


async def test_update_section_skips_when_nothing_changed(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    _, detached = _install_detached(monkeypatch, cs, {"basic": {"prefix": ["/"]}})
    report = await cs.update_section("basic", {"prefix": ["/"]}, if_match="etag")
    assert report.ok
    assert not report.applied
    detached.save.assert_not_called()


async def test_mutate_section_applies_mutation_without_etag(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    _, detached = _install_detached(monkeypatch, cs, {"plugins": {"demo": {"x": 1}}})
    report = await cs.mutate_section(
        "plugins:demo",
        lambda entry: {**entry, "$optional": True},
    )
    assert report.applied
    assert detached.data["plugins"]["demo"] == {"x": 1, "$optional": True}
    detached.save.assert_called_once()


async def test_mutate_section_create_writes_empty_entry(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    _, detached = _install_detached(monkeypatch, cs, {"plugins": {}})
    report = await cs.mutate_section("plugins:demo", lambda entry: entry, create=True)
    assert report.applied
    assert detached.data["plugins"]["demo"] == {}
    detached.save.assert_called_once()


async def test_get_section_basic_returns_raw(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    cfg = _cfg({"basic": {"prefix": ["/"]}})
    cfg.basic = {"prefix": ["/"], "nickname": "", "cmd_count": 4096}
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    assert cs.get_section("basic") == {"prefix": ["/"]}


class _DemoConfig(BaseModel):
    foo: int = 1


def test_rootless_subplugin_config_path():
    from entari_plugin_webui.services.config_service import _plugin_config_path

    plug = _plugin("$.commands.extra", "$")
    assert _plugin_config_path(plug) == [".commands", ".extra"]


async def test_update_plugin_config_subplugin_writes_nested(monkeypatch):
    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    monkeypatch.setattr(ps, "find_plugin", lambda pid: {"demo_parent.child": child}.get(pid))
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    _, detached = _install_detached(
        monkeypatch,
        cs,
        {"plugins": {"demo_parent": {"foo": 1, ".child": {"bar": 2}}}},
    )
    await ps.update_plugin_config("demo_parent.child", {"bar": 5}, if_match="etag")
    assert detached.data["plugins"]["demo_parent"][".child"]["bar"] == 5
    assert "demo_parent.child" not in detached.data["plugins"]
    detached.save.assert_called_once()


def test_plugin_schema_uses_entari_meta(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    plug = _plugin("demo_parent", "demo_parent", metadata_config=_DemoConfig)
    _bind_plugins(monkeypatch, cs, [plug])
    out = cs.get_schema_for_section("plugins:demo_parent")
    props = out["schema"]["properties"]
    assert "foo" in props
    for key in ("$disable", "$priority", "$filter"):
        assert key in props
    assert "$optional" not in props


def test_inject_meta_properties(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    out = cs.get_schema_for_section("plugins")
    for key in ("$prefix", "$files", "$prelude"):
        assert key in out["schema"]["properties"]


def test_get_plugin_config_path_public(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    assert cs.get_plugin_config_path("demo_parent.child") == ["demo_parent", ".child"]


def test_child_schema_applies_only_own_fragment(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    class _Inner(BaseModel):
        value: str = "x"

    class _Child(BaseModel):
        inner: _Inner

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    monkeypatch.setattr(
        cs,
        "_schema_fragments",
        {"demo_parent": [SimpleNamespace(path=(".child",), fragment=_Child, replace=False)]},
        raising=False,
    )
    monkeypatch.setattr(cs, "_relative_key", lambda p: ".child" if p.id.endswith(".child") else None)

    out = cs.get_schema_for_section("plugins:demo_parent.child")
    props = out["schema"]["properties"]
    assert "inner" in props
    assert ".child" not in props
    for key in ("$disable", "$priority", "$filter"):
        assert key in props
    assert any("Inner" in key for key in out["schema"].get("$defs", {}))


def test_child_schema_ignores_deeper_child_fragment(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    monkeypatch.setattr(
        cs,
        "_schema_fragments",
        {"demo_parent": [SimpleNamespace(path=(".child.deep",), fragment={"type": "object"}, replace=False)]},
        raising=False,
    )
    monkeypatch.setattr(cs, "_relative_key", lambda p: ".child" if p.id.endswith(".child") else None)
    out = cs.get_schema_for_section("plugins:demo_parent.child")
    props = out["schema"].get("properties", {})
    assert ".deep" not in props
    assert ".child.deep" not in props
    assert ".child" not in props


def test_rootless_plugin_schema_uses_top_level_path(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    plug = _plugin("$.commands", ".commands")
    _bind_plugins(monkeypatch, cs, [plug], {"$.commands": "$"})
    monkeypatch.setattr(cs, "_relative_key", lambda p: ".commands" if p.id.startswith("$") else None)

    def _fake_plugin_config_schema(plug, ref_root="/"):
        return {"type": "object", "properties": {"rootless_marker": {"type": "string"}}}

    monkeypatch.setattr(cs, "plugin_config_schema", _fake_plugin_config_schema)
    out = cs.get_schema_for_section("plugins:$.commands")
    assert out["schema"]["properties"] == {"rootless_marker": {"type": "string"}}


def test_compute_etag_hashes_directory_extra_files(monkeypatch, tmp_path):
    from entari_plugin_webui.services import config_service as cs

    root = tmp_path / "entari.yml"
    root.write_text("plugins: {}\n", encoding="utf-8")
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    child = extra_dir / "demo.yml"
    child.write_text("demo:\n  value: 1\n", encoding="utf-8")

    cfg = _cfg({"plugins": {}})
    cfg.path = root
    cfg.plugin_extra_files = ["extra"]

    first = cs.compute_etag(cfg)
    child.write_text("demo:\n  value: 2\n", encoding="utf-8")
    second = cs.compute_etag(cfg)

    assert first != second


def test_target_for_extra_file_plugin_uses_extra_file(monkeypatch, tmp_path):
    from entari_plugin_webui.services import config_service as cs

    root = tmp_path / "entari.yml"
    root.write_text("plugins:\n  $files:\n    - demo.yml\n", encoding="utf-8")
    extra = tmp_path / "demo.yml"
    extra.write_text("value: 1\n", encoding="utf-8")

    cfg = _cfg({"plugins": {"$files": ["demo.yml"], "demo": {"value": 1}}})
    cfg.path = root
    cfg.plugin_extra_files = ["demo.yml"]
    cfg._root_plugin_keys = set()

    monkeypatch.setattr(cs, "find_plugin", lambda pid: None)
    monkeypatch.setattr(cs, "get_plugins", lambda subplugged=False: [])

    target, prefix, file_path = cs._target_for(cfg, "plugins:demo")

    assert target == {"value": 1}
    assert prefix == ()
    assert file_path == extra.resolve()
