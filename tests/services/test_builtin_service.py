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


def _plugin(*, available=True, static=False, name="Echo", description="desc"):
    return SimpleNamespace(
        is_available=available,
        is_static=static,
        metadata=SimpleNamespace(name=name, description=description),
    )


def _bind(monkeypatch, bs, cfg, modules, plugins=None, load_error=None):
    monkeypatch.setattr(bs, "EntariConfig", SimpleNamespace(instance=cfg))
    monkeypatch.setattr(bs, "_iter_builtin_modules", lambda: modules)
    monkeypatch.setattr(bs, "find_plugin", lambda pid: (plugins or {}).get(pid))

    load = MagicMock(return_value=SimpleNamespace(error=load_error, plugin=object()))
    monkeypatch.setattr(bs, "load_plugin", load)

    async def _enable(pid):
        return True

    async def _unload(pid):
        return True

    enable = AsyncMock(side_effect=_enable)
    unload = AsyncMock(side_effect=_unload)
    monkeypatch.setattr(bs, "enable_plugin", enable)
    monkeypatch.setattr(bs, "unload_plugin_async", unload)
    return load, enable, unload


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
    load.assert_called_once()
    assert load.call_args.args[0] == "::echo"
    cfg.save.assert_called_once()


@pytest.mark.asyncio
async def test_enable_restores_optional_config_without_duplicate(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"?::echo": {"foo": 1}}})
    load, _, _ = _bind(monkeypatch, bs, cfg, [("echo", tmp_path / "echo.py")])

    await bs.set_builtin_enabled("echo", True)

    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}
    load.assert_called_once()


@pytest.mark.asyncio
async def test_enable_loaded_disabled_calls_enable_plugin(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"~::echo": {"foo": 1}}})
    plug = _plugin(available=False)
    _, enable, _ = _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": plug},
    )

    await bs.set_builtin_enabled("echo", True)

    enable.assert_awaited_once_with("::echo")
    assert cfg.data["plugins"] == {"::echo": {"foo": 1}}


@pytest.mark.asyncio
async def test_enable_failure_keeps_existing_config(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"?::echo": {"foo": 1}}})
    _bind(monkeypatch, bs, cfg, [("echo", tmp_path / "echo.py")], load_error=RuntimeError("boom"))

    from entari_plugin_webui.core.error import MarketError

    with pytest.raises(MarketError):
        await bs.set_builtin_enabled("echo", True)

    assert cfg.data["plugins"] == {"?::echo": {"foo": 1}}
    cfg.save.assert_not_called()


@pytest.mark.asyncio
async def test_disable_unloads_and_keeps_optional_config(bs, tmp_path, monkeypatch):
    cfg = _cfg({"plugins": {"::echo": {"foo": 1}}})
    _, _, unload = _bind(
        monkeypatch,
        bs,
        cfg,
        [("echo", tmp_path / "echo.py")],
        plugins={"arclet.entari.builtins.echo": _plugin()},
    )

    await bs.set_builtin_enabled("echo", False)

    assert cfg.data["plugins"] == {"?::echo": {"foo": 1}}
    unload.assert_awaited_once_with("::echo")
    cfg.save.assert_called_once()


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
async def test_unknown_builtin_rejected(bs, tmp_path, monkeypatch):
    cfg = _cfg()
    _bind(monkeypatch, bs, cfg, [("echo", tmp_path / "echo.py")])

    from entari_plugin_webui.core.error import MarketError

    with pytest.raises(MarketError):
        await bs.set_builtin_enabled("nope", True)
