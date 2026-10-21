from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(name="bs")
def _bs():
    from entari_plugin_webui.services import builtin_service

    return builtin_service


def _cfg(data=None):
    cfg = MagicMock()
    cfg.data = data if data is not None else {"plugins": {}}
    cfg.save = MagicMock()
    return cfg


class _Result:
    """模拟 entari 的 _LoadResult：加载失败时为假值。"""

    def __init__(self, error=None):
        self.error = error
        self.plugin = None if error is not None else object()

    def __bool__(self):
        return self.plugin is not None


def _plugin(*, available=True, static=False, name="Echo", description="desc"):
    plug = MagicMock()
    plug.is_available = available
    plug.is_static = static
    plug.metadata = SimpleNamespace(name=name, description=description)
    plug.disable = MagicMock()
    return plug


def _bind(monkeypatch, bs, cfg, modules, plugins=None, load_error=None, mutate_ok=True):
    from arclet.entari.config.model import ApplyError, ApplyReport

    from entari_plugin_webui.services import config_service

    monkeypatch.setattr(bs, "EntariConfig", SimpleNamespace(instance=cfg))
    monkeypatch.setattr(bs, "_iter_builtin_modules", lambda: modules)
    monkeypatch.setattr(bs, "find_plugin", lambda pid: (plugins or {}).get(pid))

    async def _mutate(section, mutate, **kwargs):
        key = section.split(":", 1)[1]
        plugins_map = cfg.data.setdefault("plugins", {})
        raw = next((k for k in (key, f"~{key}", f"?{key}") if k in plugins_map), None)
        entry = dict(plugins_map.get(raw, {})) if raw is not None else {}
        desired = mutate(entry)
        if raw is not None:
            plugins_map.pop(raw, None)
        plugins_map[key] = desired
        if not mutate_ok:
            return ApplyReport(ok=False, applied=True, errors=[ApplyError(key, "boom")])
        return ApplyReport(ok=True, applied=True)

    monkeypatch.setattr(config_service, "mutate_section", _mutate)
    return MagicMock(), AsyncMock(), AsyncMock()


def test_extract_metadata_positional(bs, tmp_path):
    path = tmp_path / "echo.py"
    path.write_text(
        'from arclet.entari import metadata\n\nmetadata("Echo", author=[], description="Echo the content")\n',
        encoding="utf-8",
    )
    assert bs._extract_metadata(path) == ("Echo", "Echo the content")


def test_extract_metadata_named(bs, tmp_path):
    path = tmp_path / "lang.py"
    path.write_text(
        'from arclet.entari import metadata\n\nmetadata(name="语言本地化管理", description="i18n配置相关功能")\n',
        encoding="utf-8",
    )
    assert bs._extract_metadata(path) == ("语言本地化管理", "i18n配置相关功能")


def test_extract_metadata_missing(bs, tmp_path):
    path = tmp_path / "plain.py"
    path.write_text("x = 1\n", encoding="utf-8")
    assert bs._extract_metadata(path) == (None, None)


def test_list_builtins_includes_loaded_and_available(bs, tmp_path, monkeypatch):
    echo = tmp_path / "echo.py"
    echo.write_text('metadata("Echo", description="Echo the content")\n', encoding="utf-8")
    pipe = tmp_path / "pipe.py"
    pipe.write_text('metadata(name="管道命令", description="连接命令")\n', encoding="utf-8")
    cfg = _cfg()
    _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", echo), ("pipe", pipe)],
        plugins={"arclet.entari.builtins.echo": _plugin()},
    )

    result = bs.list_builtins()
    assert [item["name"] for item in result] == ["echo", "pipe"]
    loaded, unloaded = result
    assert loaded["enabled"] is True
    assert loaded["loaded"] is True
    assert loaded["title"] == "Echo"
    assert unloaded["enabled"] is False
    assert unloaded["loaded"] is False
    assert unloaded["title"] == "管道命令"
    assert unloaded["key"] == "::pipe"


@pytest.mark.asyncio
async def test_enable_adds_config_and_loads(bs, tmp_path, monkeypatch):
    cfg = _cfg()
    load, _, _ = _bind(monkeypatch, bs, cfg, [("echo", tmp_path / "echo.py")])

    await bs.set_builtin_enabled("echo", True)

    assert cfg.data["plugins"] == {"::echo": {}}


@pytest.mark.asyncio
async def test_enable_restores_optional_config_without_duplicate(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"?::echo": {"foo": 1}}})
    load, _, _ = _bind(monkeypatch, bs, cfg, [("echo", tmp_path / "echo.py")])

    await bs.set_builtin_enabled("echo", True)

    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}


@pytest.mark.asyncio
async def test_enable_loaded_disabled_clears_disable(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"~::echo": {"foo": 1}}})
    plug = _plugin(available=False)
    _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": plug},
    )

    await bs.set_builtin_enabled("echo", True)

    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}


@pytest.mark.asyncio
async def test_enable_failure_reports_error(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"?::echo": {"foo": 1}}})
    _bind(monkeypatch, bs, cfg, [("echo", tmp_path / "echo.py")], mutate_ok=False)

    from entari_plugin_webui.core.error import MarketError

    with pytest.raises(MarketError):
        await bs.set_builtin_enabled("echo", True)

    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}


@pytest.mark.asyncio
async def test_disable_writes_disable_marker_without_unload(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"::echo": {"foo": 1}}})
    plug = _plugin()
    _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": plug},
    )

    await bs.set_builtin_enabled("echo", False)

    assert cfg.data["plugins"] == {"::echo": {"foo": 1, "$disable": True}}


@pytest.mark.asyncio
async def test_unload_writes_optional(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"::echo": {"foo": 1}}})
    _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": _plugin()},
    )

    await bs.set_builtin_unloaded("echo")

    assert cfg.data["plugins"] == {"::echo": {"foo": 1, "$optional": True}}


@pytest.mark.asyncio
async def test_load_builtin_clears_optional(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"?::echo": {"foo": 1}}})
    _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": _plugin()},
    )

    assert await bs.load_builtin("echo") is True
    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}


@pytest.mark.asyncio
async def test_disable_static_rejected(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"::echo": {"foo": 1}}})
    _, _, unload = _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": _plugin(static=True)},
    )

    from entari_plugin_webui.core.error import MarketError

    with pytest.raises(MarketError):
        await bs.set_builtin_enabled("echo", False)

    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}
    unload.assert_not_awaited()


@pytest.mark.asyncio
async def test_unload_static_rejected(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"::echo": {"foo": 1}}})
    _, _, unload = _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": _plugin(static=True)},
    )

    from entari_plugin_webui.core.error import MarketError

    with pytest.raises(MarketError):
        await bs.set_builtin_unloaded("echo")

    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}
    unload.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_builtin_rejected(bs, tmp_path, monkeypatch):
    cfg = _cfg()
    _bind(monkeypatch, bs, cfg, [("echo", tmp_path / "echo.py")])

    from entari_plugin_webui.core.error import MarketError

    with pytest.raises(MarketError):
        await bs.set_builtin_enabled("nope", True)
