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


def test_update_section(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    cfg = _cfg({"basic": {"prefix": ["/"]}})
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    cs.update_section("basic", {"prefix": ["/a"]})
    assert cfg.data["basic"]["prefix"] == ["/a"]
    cfg.save.assert_called_once()


def test_update_section_subplugin_writes_nested(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    cfg = _cfg({"plugins": {"demo_parent": {"foo": 1, ".child": {"bar": 2}}}})
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    cs.update_section("plugins:demo_parent.child", {"bar": 3, "baz": 4})
    assert cfg.data["plugins"]["demo_parent"][".child"] == {"bar": 3, "baz": 4}
    assert "demo_parent.child" not in cfg.data["plugins"]
    cfg.save.assert_called_once()


def test_update_section_rootless_writes_config_key(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    plug = _plugin("$.commands", ".commands")
    _bind_plugins(monkeypatch, cs, [plug], {"$.commands": "$"})
    cfg = _cfg({"plugins": {".commands": {"use_config_prefix": False}}})
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    cs.update_section("plugins:$.commands", {"use_config_prefix": True})
    assert cfg.data["plugins"][".commands"]["use_config_prefix"] is True
    cfg.save.assert_called_once()


class _DemoConfig(BaseModel):
    foo: int = 1


def test_rootless_subplugin_config_path():
    from entari_plugin_webui.services.config_service import _plugin_config_path

    plug = _plugin("$.commands.extra", "$")
    assert _plugin_config_path(plug) == [".commands", ".extra"]


def test_update_plugin_config_subplugin_writes_nested(monkeypatch):
    from entari_plugin_webui.services import config_service as cs
    from entari_plugin_webui.services import plugin_service as ps

    parent = _plugin("demo_parent", "demo_parent", subplugins=["demo_parent.child"])
    child = _plugin("demo_parent.child", "demo_parent")
    monkeypatch.setattr(ps, "find_plugin", lambda pid: {"demo_parent.child": child}.get(pid))
    _bind_plugins(monkeypatch, cs, [parent, child], {"demo_parent.child": "demo_parent"})
    cfg = _cfg({"plugins": {"demo_parent": {"foo": 1, ".child": {"bar": 2}}}})
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    ps.update_plugin_config("demo_parent.child", {"bar": 5})
    assert cfg.data["plugins"]["demo_parent"][".child"]["bar"] == 5
    assert "demo_parent.child" not in cfg.data["plugins"]
    cfg.save.assert_called_once()


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
