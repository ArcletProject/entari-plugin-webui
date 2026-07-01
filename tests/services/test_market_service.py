from __future__ import annotations

import asyncio

import pytest


def test_market_error_exists():
    from entari_plugin_webui.services.market_service import MarketError

    assert MarketError is not None


@pytest.mark.asyncio
async def test_list_uses_remote(monkeypatch, tmp_path):
    from entari_plugin_webui.services import market_service as ms

    cache = tmp_path / "marketplace.json"
    monkeypatch.setattr(ms, "_CACHE_PATH", cache)
    monkeypatch.setattr(ms, "_registry_url", lambda: "http://reg/x.json")

    async def fake_fetch(url):
        return {"plugins": [{"name": "demo", "pip_name": "entari-demo", "version": "1.0", "description": "d"}]}

    monkeypatch.setattr(ms, "_fetch_remote", fake_fetch)
    monkeypatch.setattr(ms, "_installed_pip_names", _empty_installed)

    out = await ms.list_plugins()
    names = [p["name"] for p in out["plugins"]]
    assert "demo" in names
    assert cache.exists()


async def _empty_installed() -> set[str]:
    return set()


@pytest.mark.asyncio
async def test_install_unknown_rejected(monkeypatch):
    from entari_plugin_webui.services import market_service as ms

    monkeypatch.setattr(ms, "_registry_url", lambda: "")
    monkeypatch.setattr(ms, "_installed_pip_names", _empty_installed)

    with pytest.raises(ms.MarketError):
        await ms.start_install("does-not-exist")


@pytest.mark.asyncio
async def test_start_install_spawns_action(monkeypatch):
    from entari_plugin_webui.services import market_service as ms
    from entari_plugin_webui.services import package_manager as pm

    async def fake_catalog():
        return {"plugins": [{"name": "demo", "pip_name": "entari-demo"}], "__fallback": False}

    monkeypatch.setattr(ms, "_ensure_catalog", fake_catalog)
    monkeypatch.setattr(ms, "_installed_pip_names", _empty_installed)

    captured: dict = {}

    async def fake_run(pm_, action, pip_name):
        captured.update(pm=pm_.name, action=action, pip_name=pip_name)
        return 0, "ok"

    monkeypatch.setattr(pm, "run_action", fake_run)

    tid = await ms.start_install("demo")
    assert isinstance(tid, str)
    task = ms.get_task(tid)
    assert task is not None
    assert task.pip_name == "entari-demo"
    assert task.action == "install"
    # wait for background task
    await asyncio.sleep(0.1)
    task = ms.get_task(tid)
    assert task
    assert task.status == "success"
    assert captured == {"pm": "pdm", "action": "install", "pip_name": "entari-demo"}


@pytest.mark.asyncio
async def test_start_uninstall_not_installed_rejected(monkeypatch):
    from entari_plugin_webui.services import market_service as ms

    async def fake_catalog():
        return {"plugins": [{"name": "demo", "pip_name": "entari-demo"}], "__fallback": False}

    monkeypatch.setattr(ms, "_ensure_catalog", fake_catalog)
    monkeypatch.setattr(ms, "_installed_pip_names", _empty_installed)

    with pytest.raises(ms.MarketError, match="not_installed"):
        await ms.start_uninstall("demo")
