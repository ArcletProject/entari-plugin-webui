from __future__ import annotations

import sys

import pytest


def test_detect_by_lock_file(tmp_path, monkeypatch):
    from entari_plugin_webui.services import package_manager as pm

    (tmp_path / "uv.lock").write_text("")
    monkeypatch.setattr(pm, "_project_root", lambda cwd=None: tmp_path)
    monkeypatch.setattr(pm.shutil, "which", lambda name: f"/usr/bin/{name}")
    detected = pm.detect_package_manager()
    assert detected.name == "uv"
    assert detected.executable == "/usr/bin/uv"


def test_detect_falls_back_to_pip(tmp_path, monkeypatch):
    from entari_plugin_webui.services import package_manager as pm

    monkeypatch.setattr(pm, "_project_root", lambda cwd=None: tmp_path)
    monkeypatch.setattr(pm.shutil, "which", lambda name: None)
    detected = pm.detect_package_manager()
    assert detected.name == "pip"
    assert detected.executable == sys.executable


def test_install_args_uv():
    from entari_plugin_webui.services import package_manager as pm

    m = pm.PackageManager(name="uv", executable="/usr/bin/uv")
    assert m.install_args("entari-demo") == ["/usr/bin/uv", "add", "entari-demo"]


def test_uninstall_args_pip():
    from entari_plugin_webui.services import package_manager as pm

    m = pm.PackageManager(name="pip", executable=sys.executable)
    assert m.uninstall_args("entari-demo") == [
        sys.executable,
        "-m",
        "pip",
        "uninstall",
        "-y",
        "entari-demo",
    ]


def test_list_args_pdm():
    from entari_plugin_webui.services import package_manager as pm

    m = pm.PackageManager(name="pdm", executable="/usr/bin/pdm")
    assert m.list_args() == ["/usr/bin/pdm", "list", "--json"]


@pytest.mark.asyncio
async def test_list_installed_parses_json(monkeypatch):
    from entari_plugin_webui.services import package_manager as pm

    m = pm.PackageManager(name="pip", executable=sys.executable)

    class FakeProc:
        async def communicate(self):
            return (b'[{"name": "Demo"}, {"name": "Other"}]', b"")

    async def fake_exec(*args: object, **kw: object):
        return FakeProc()

    monkeypatch.setattr(pm.asyncio, "create_subprocess_exec", fake_exec)
    names = await pm.list_installed(m)
    assert names == {"demo", "other"}


@pytest.mark.asyncio
async def test_list_installed_returns_empty_on_failure(monkeypatch):
    from entari_plugin_webui.services import package_manager as pm

    m = pm.PackageManager(name="pip", executable=sys.executable)

    async def boom(*args: object, **kw: object):
        raise FileNotFoundError()

    monkeypatch.setattr(pm.asyncio, "create_subprocess_exec", boom)
    assert await pm.list_installed(m) == set()


def test_project_root_finds_parent(tmp_path):
    from entari_plugin_webui.services import package_manager as pm

    child = tmp_path / "sub" / "deep"
    child.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("")
    root = pm._project_root(child)
    assert root == tmp_path


def test_project_root_fallback(tmp_path):
    from entari_plugin_webui.services import package_manager as pm

    root = pm._project_root(tmp_path)
    assert root == tmp_path
