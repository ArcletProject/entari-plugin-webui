from __future__ import annotations

import asyncio
from contextlib import suppress
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
import pytest_asyncio
from creart import it
from fastapi import FastAPI
from fastapi.testclient import TestClient
from launart import Launart

ENTARI_YML_TEXT = pytest.StashKey[str]()
ENTARI_WEBUI_CONFIG = pytest.StashKey[dict[str, Any]]()


def pytest_configure(config: pytest.Config):
    config.stash[ENTARI_YML_TEXT] = """
basic:
  log:
    level: debug
    ignores:
      - "aiosqlite.core"
      - "asyncio.selector_events"
"""
    config.stash[ENTARI_WEBUI_CONFIG] = {}


@pytest.fixture(scope="session", autouse=True)
def entari_yml_text(request: pytest.FixtureRequest):
    dir_ = TemporaryDirectory()
    dir_.__enter__()
    file = Path(dir_.name) / "entari.yml"
    file.write_text(request.config.stash[ENTARI_YML_TEXT])
    try:
        yield file
    finally:
        dir_.__exit__(None, None, None)


@pytest.fixture(scope="session", autouse=True)
def _entari_init(request: pytest.FixtureRequest, entari_yml_text: Path):
    from arclet.entari import Entari

    return Entari.load(entari_yml_text)


@pytest.fixture(scope="session", autouse=True)
def after_entari_init(_entari_init: None, request: pytest.FixtureRequest):
    from arclet.entari import load_plugin

    load_plugin("entari_plugin_server", {"port": 9555})
    load_plugin("entari_plugin_database", {"name": ":memory:"})
    load_plugin("entari_plugin_webui", config=request.config.stash[ENTARI_WEBUI_CONFIG])


@pytest_asyncio.fixture(scope="session", autouse=True)
async def entari_init(_entari_init, after_entari_init: None):
    from arclet.letoderea.utils import set_event_loop
    from entari_plugin_database import service as db_service

    set_event_loop(asyncio.get_running_loop())
    manager = it(Launart)
    task = asyncio.create_task(_entari_init.run_async())

    await manager.status.wait_for_blocking()
    await db_service.status.wait_for("blocking")

    yield _entari_init

    manager._on_sys_signal(None, None, task)

    with suppress(asyncio.CancelledError):
        await task


@pytest.fixture(name="entari")
def entari_instance(entari_init):
    pass


@pytest.fixture
def app(after_entari_init: None) -> FastAPI:
    from entari_plugin_server import server

    return server.app  # type: ignore


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_global_state(after_entari_init: None):
    from entari_plugin_webui import webui_config
    from entari_plugin_webui.core.security import set_local_mode
    from entari_plugin_webui.services import market_service as _ms

    set_local_mode(True)
    webui_config.password = ""
    webui_config.registry_url = ""
    webui_config.package_manager = ""

    _ms._PM = None
    _ms._loaded_cache = None
    _ms._loaded_at = 0.0
    _ms._TASKS.clear()

    yield
    set_local_mode(True)
    webui_config.password = ""
    webui_config.registry_url = ""
    webui_config.package_manager = ""
    _ms._PM = None
    _ms._loaded_cache = None
    _ms._loaded_at = 0.0
    _ms._TASKS.clear()
