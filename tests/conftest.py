from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _entari_config():
    """Initialize EntariConfig so module imports don't trip over PluginLoader."""
    from arclet.entari.config.file import EntariConfig

    EntariConfig(Path("/tmp/entari-test-config.yml"))


@pytest.fixture()
def app():
    from entari_plugin_webui.api import create_app

    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)
