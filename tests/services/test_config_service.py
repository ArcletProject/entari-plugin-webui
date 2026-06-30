from __future__ import annotations

from unittest.mock import MagicMock


def _cfg(data):
    cfg = MagicMock()
    cfg.basic = data.get("basic", {})
    cfg.plugin = data.get("plugins", {})
    cfg.data = data
    cfg.save = MagicMock()
    return cfg


def test_list_sections(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    plug = MagicMock()
    plug._config_key = "webui"
    plug.id = "entari_plugin_webui"
    monkeypatch.setattr(cs, "get_plugins", lambda: [plug])
    data = {"basic": {"prefix": ["/"]}, "plugins": {"webui": {}}, "adapters": []}
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg(data)))
    out = cs.list_sections()
    assert "basic" in out["sections"]
    assert "plugins:webui" in out["plugin_sections"]


def test_get_section_basic(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg({"basic": {"prefix": ["/"]}})))
    out = cs.get_section("basic")
    assert out == {"prefix": ["/"]}


def test_get_section_plugin(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    monkeypatch.setattr(
        cs, "EntariConfig", MagicMock(instance=_cfg({"plugins": {"webui": {"password": "x"}}}))
    )
    out = cs.get_section("plugins:webui")
    assert out == {"password": "x"}


def test_update_section(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    cfg = _cfg({"basic": {"prefix": ["/"]}})
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    cs.update_section("basic", {"prefix": ["/a"]})
    assert cfg.data["basic"]["prefix"] == ["/a"]
    cfg.save.assert_called_once()



def test_inject_meta_properties(monkeypatch):
    from entari_plugin_webui.services import config_service as cs

    monkeypatch.setattr(cs, "config_model_schema", lambda m, ref_root=None: {"type": "object", "properties": {}})
    out = cs.get_schema_for_section("plugins")
    for key in ("$prefix", "$files", "$prelude"):
        assert key in out["schema"]["properties"]
    plug = MagicMock()
    plug._config_key = "webui"
    plug.id = "entari_plugin_webui"
    monkeypatch.setattr(cs, "get_plugins", lambda: [plug])
    out1 = cs.get_schema_for_section("plugins:webui")
    for key in ("$disable", "$priority", "$filter", "$optional"):
        assert key in out1["schema"]["properties"]
