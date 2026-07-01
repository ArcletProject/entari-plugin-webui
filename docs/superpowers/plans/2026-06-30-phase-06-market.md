# Phase 06 — 插件市场（registry + 包管理器任务）

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** `market_service` 远程拉目录（失败回退本地缓存），`/api/market/plugins[/{name}]`、` POST install/uninstall` 启**探测到的包管理器**子进程任务、`GET /api/market/tasks/{id}` 轮询；**安装名必须命中当前目录条目**，按其声明的 `pip_name` 执行。

**Architecture:** `services/package_manager.py` 探测当前环境使用的包管理器（uv / pdm / poetry / rye / pipenv / pip），参考 `entari_cli.project` 的 `CHECK_PM_MAP` / `select_package_manager`；`services/market_service.py` 用 `aiohttp` 拉 `registry_url`，缓存到 `static/marketplace.json`（TTL 1h），安装/卸载/列举已装均委托给 `package_manager`。**虚拟环境下 `pip` 不一定存在**（uv/pdm 创建的 venv 默认不含 pip），故必须按探测结果分发命令。

**Tech Stack:** aiohttp、asyncio、subprocess、fastapi、starlette。

---

## 包管理器命令矩阵

探测优先级：① 项目根锁文件 → ② `shutil.which` 可执行 → ③ `python -m pip` 兜底。

| PM        | 锁文件 / 探测       | 列举已装（JSON）                                   | install                          | uninstall                          |
| --------- | ------------------- | -------------------------------------------------- | -------------------------------- | ---------------------------------- |
| uv        | `uv.lock` / `uv`    | `uv pip list --format=json`                        | `uv add <pkg>`                   | `uv remove <pkg>`                  |
| pdm       | `pdm.lock` / `pdm`  | `pdm list --json`                                  | `pdm add <pkg>`                  | `pdm remove <pkg>`                 |
| poetry    | `poetry.lock` / `poetry` | `poetry show --format=json`                   | `poetry add <pkg>`               | `poetry remove <pkg>`              |
| rye       | `requirements.lock` / `rye` | `rye pip list --format=json`                 | `rye add <pkg>`                  | `rye remove <pkg>`                 |
| pipenv    | `Pipfile.lock` / `pipenv` | `pipenv run python -m pip list --format=json` | `pipenv install <pkg>`           | `pipenv uninstall <pkg>`           |
| pip       | `requirements.txt` / 兜底 | `<python> -m pip list --format=json`        | `<python> -m pip install -U <pkg>` | `<python> -m pip uninstall -y <pkg>` |

> 来源：uv `uv pip list`（[docs.astral.sh](https://docs.astral.sh/uv/reference/cli/#uv-pip-list)）、pdm `list --json`（[pdm-project.org](https://pdm-project.org/en/latest/reference/cli/#list)）、poetry `show --format=json`（[python-poetry.org](https://python-poetry.org/docs/cli/#show)）、pipenv `install`/`uninstall` + `run python -m pip list`（[pipenv.pypa.io](https://pipenv.pypa.io/en/latest/commands.html)）、rye 兼容 `pip` 子命令（`rye pip list`）。

---

## 文件结构

- Create: `src/entari_plugin_webui/services/package_manager.py`
- Create: `src/entari_plugin_webui/services/market_service.py`
- Create: `src/entari_plugin_webui/api/market.py`
- Create: `src/entari_plugin_webui/static/marketplace.json`（空目录种子 `{"plugins": []}`）
- Modify: `api/router.py` 挂 router
- Create: `tests/services/test_package_manager.py`、`tests/services/test_market_service.py`、`tests/api/test_market.py`

---

## Task 6.1：包管理器探测模块

**Files:** Create `services/package_manager.py`、`tests/services/test_package_manager.py`

- [ ] **Step 1: 测试 `tests/services/test_package_manager.py`**

```python
from __future__ import annotations

import asyncio
import sys

import pytest

from entari_plugin_webui.services import package_manager as pm


def test_detect_by_lock_file(tmp_path, monkeypatch):
    (tmp_path / "uv.lock").write_text("")
    monkeypatch.setattr(pm, "_project_root", lambda cwd=None: tmp_path)
    monkeypatch.setattr(pm.shutil, "which", lambda name: f"/usr/bin/{name}")
    detected = pm.detect_package_manager()
    assert detected.name == "uv"
    assert detected.executable == "/usr/bin/uv"


def test_detect_falls_back_to_pip(tmp_path, monkeypatch):
    monkeypatch.setattr(pm, "_project_root", lambda cwd=None: tmp_path)
    monkeypatch.setattr(pm.shutil, "which", lambda name: None)
    detected = pm.detect_package_manager()
    assert detected.name == "pip"
    assert detected.executable == sys.executable


def test_install_args_uv():
    m = pm.PackageManager(name="uv", executable="/usr/bin/uv")
    assert m.install_args("entari-demo") == ["/usr/bin/uv", "add", "entari-demo"]


def test_uninstall_args_pip():
    m = pm.PackageManager(name="pip", executable=sys.executable)
    assert m.uninstall_args("entari-demo") == [
        sys.executable, "-m", "pip", "uninstall", "-y", "entari-demo"
    ]


def test_list_args_pdm():
    m = pm.PackageManager(name="pdm", executable="/usr/bin/pdm")
    assert m.list_args() == ["/usr/bin/pdm", "list", "--json"]


@pytest.mark.asyncio
async def test_list_installed_parses_json(monkeypatch):
    m = pm.PackageManager(name="pip", executable=sys.executable)

    class FakeProc:
        async def communicate(self):
            return (b'[{"name": "Demo"}, {"name": "Other"}]', b"")

    async def fake_exec(*args, **kw):
        return FakeProc()

    monkeypatch.setattr(pm.asyncio, "create_subprocess_exec", fake_exec)
    names = await pm.list_installed(m)
    assert names == {"demo", "other"}


@pytest.mark.asyncio
async def test_list_installed_returns_empty_on_failure(monkeypatch):
    m = pm.PackageManager(name="pip", executable=sys.executable)

    async def boom(*args, **kw):
        raise FileNotFoundError()

    monkeypatch.setattr(pm.asyncio, "create_subprocess_exec", boom)
    assert await pm.list_installed(m) == set()
```

- [ ] **Step 2: 实现 `services/package_manager.py`**

```python
from __future__ import annotations

import asyncio
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PM_INSTALL_CMD = {
    "uv": "add",
    "pdm": "add",
    "poetry": "add",
    "rye": "add",
    "pip": "install",
    "pipenv": "install",
}
PM_UNINSTALL_CMD = {
    "uv": "remove",
    "pdm": "remove",
    "poetry": "remove",
    "rye": "remove",
    "pip": "uninstall",
    "pipenv": "uninstall",
}
# 锁文件 -> 包管理器（按优先级顺序）
PM_LOCK_FILES: dict[str, str] = {
    "uv.lock": "uv",
    "pdm.lock": "pdm",
    "poetry.lock": "poetry",
    "requirements.lock": "rye",
    "Pipfile.lock": "pipenv",
    "requirements.txt": "pip",
}
# 探测顺序（无锁文件时按此顺序 which）
PM_ORDER = ("uv", "pdm", "poetry", "rye", "pipenv")


@dataclass
class PackageManager:
    name: str          # uv / pdm / poetry / rye / pipenv / pip
    executable: str    # 解析到的可执行路径；pip 兜底时为 python 解释器

    def list_args(self) -> list[str]:
        if self.name == "pip":
            return [self.executable, "-m", "pip", "list", "--format=json"]
        if self.name == "uv":
            return [self.executable, "pip", "list", "--format=json"]
        if self.name == "pdm":
            return [self.executable, "list", "--json"]
        if self.name == "poetry":
            return [self.executable, "show", "--format=json"]
        if self.name == "rye":
            return [self.executable, "pip", "list", "--format=json"]
        if self.name == "pipenv":
            return [self.executable, "run", "python", "-m", "pip", "list", "--format=json"]
        raise ValueError(f"unknown package manager: {self.name}")

    def install_args(self, pip_name: str) -> list[str]:
        if self.name == "pip":
            return [self.executable, "-m", "pip", "install", "-U", pip_name]
        return [self.executable, PM_INSTALL_CMD[self.name], pip_name]

    def uninstall_args(self, pip_name: str) -> list[str]:
        if self.name == "pip":
            return [self.executable, "-m", "pip", "uninstall", "-y", pip_name]
        return [self.executable, PM_UNINSTALL_CMD[self.name], pip_name]


def _project_root(cwd: Optional[Path] = None) -> Path:
    """向上查找包含 pyproject.toml / setup.py 的目录（参考 entari_cli.project.get_project_root）。"""
    base = Path(cwd or Path.cwd())
    for parent in [base, *base.parents]:
        if (parent / "pyproject.toml").exists() or (parent / "setup.py").exists():
            return parent
    return base


def detect_package_manager(cwd: Optional[Path] = None) -> PackageManager:
    """按锁文件 → 可执行 → pip 兜底 的顺序探测当前环境使用的包管理器。

    虚拟环境下 pip 不一定存在（uv/pdm 创建的 venv 默认不含 pip），所以不能假设
    `python -m pip` 永远可用；优先用项目实际使用的 PM。
    """
    root = _project_root(cwd)
    # ① 锁文件命中 + 对应可执行存在
    for lock, name in PM_LOCK_FILES.items():
        if (root / lock).exists():
            exe = shutil.which(name)
            if exe:
                return PackageManager(name=name, executable=exe)
    # ② 按 PM_ORDER 探测可执行
    for name in PM_ORDER:
        exe = shutil.which(name)
        if exe:
            return PackageManager(name=name, executable=exe)
    # ③ pip 兜底（用当前解释器，-m pip 在装了 pip 的 venv 里仍可用）
    return PackageManager(name="pip", executable=sys.executable)


async def list_installed(pm_: PackageManager) -> set[str]:
    """返回当前环境中已安装包名（小写）。失败返回空集。"""
    try:
        proc = await asyncio.create_subprocess_exec(
            *pm_.list_args(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        items = json.loads(out.decode("utf-8", errors="replace"))
        return {item["name"].lower() for item in items}
    except Exception:  # noqa: BLE001
        return set()


async def run_action(pm_: PackageManager, action: str, pip_name: str) -> tuple[int, str]:
    """执行 install/uninstall，返回 (returncode, 合并后的输出文本)。"""
    if action == "install":
        args = pm_.install_args(pip_name)
    elif action == "uninstall":
        args = pm_.uninstall_args(pip_name)
    else:
        raise ValueError(f"unknown action: {action}")
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    out, _ = await proc.communicate()
    return proc.returncode or 0, out.decode("utf-8", errors="replace")
```

- [ ] **Step 3:** Run `pdm run pytest tests/services/test_package_manager.py -v`。提交。

---

## Task 6.2：目录种子与服务

**Files:** Create `static/marketplace.json`、`services/market_service.py`

- [ ] **Step 1:** 种子目录

`src/entari_plugin_webui/static/marketplace.json`：

```json
{"plugins": []}
```

- [ ] **Step 2: 测试 `tests/services/test_market_service.py`**

```python
from __future__ import annotations

import pytest

from entari_plugin_webui.services import market_service as ms


def test_parse_rate_ok():
    assert ms.MarketError is not None


@pytest.mark.asyncio
async def test_list_uses_remote(monkeypatch, tmp_path):
    cache = tmp_path / "marketplace.json"
    monkeypatch.setattr(ms, "_CACHE_PATH", cache)
    monkeypatch.setattr(ms, "_registry_url", lambda: "http://reg/x.json")

    async def fake_fetch(url):
        return {"plugins": [{"name": "demo", "pip_name": "entari-demo", "version": "1.0", "description": "d"}]}

    monkeypatch.setattr(ms, "_fetch_remote", fake_fetch)
    # 隔离真实环境：假定已装集合为空
    monkeypatch.setattr(ms, "_installed_pip_names", _empty_installed)
    out = await ms.list_plugins()
    names = [p["name"] for p in out["plugins"]]
    assert "demo" in names
    assert cache.exists()  # 已写入缓存


async def _empty_installed() -> set[str]:
    return set()


@pytest.mark.asyncio
async def test_install_unknown_rejected(monkeypatch):
    monkeypatch.setattr(ms, "_registry_url", lambda: "")
    monkeypatch.setattr(ms, "_installed_pip_names", _empty_installed)
    out = await ms.list_plugins()  # 默认空目录 → 全部未知
    with pytest.raises(ms.MarketError):
        await ms.start_install("does-not-exist")


@pytest.mark.asyncio
async def test_start_install_spawns_action(monkeypatch):
    # 让目录里有一个已知插件
    async def fake_catalog():
        return {"plugins": [{"name": "demo", "pip_name": "entari-demo"}], "__fallback": False}

    monkeypatch.setattr(ms, "_ensure_catalog", fake_catalog)
    monkeypatch.setattr(ms, "_installed_pip_names", _empty_installed)
    captured: dict = {}

    async def fake_run(pm_, action, pip_name):
        captured.update(pm=pm_.name, action=action, pip_name=pip_name)
        return 0, "ok"

    monkeypatch.setattr(ms.package_manager, "run_action", fake_run)
    tid = await ms.start_install("demo")
    task = ms.get_task(tid)
    assert task is not None and task.status == "success"
    assert captured == {"pm": "pip", "action": "install", "pip_name": "entari-demo"}
```

- [ ] **Step 3: 实现 `services/market_service.py`**

```python
from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp

from .. import webui_config
from . import package_manager as _pm

_CACHE_PATH = Path(__file__).resolve().parent.parent / "static" / "marketplace.json"
_CACHE_TTL = 3600
_TASKS: dict[str, "InstallTask"] = {}

# 探测结果缓存（同进程内只探测一次；config 可覆盖）
_PM: _pm.PackageManager | None = None


class MarketError(Exception):
    pass


class UnknownPlugin(MarketError):
    pass


@dataclass
class InstallTask:
    task_id: str
    pip_name: str
    action: str  # "install" | "uninstall"
    status: str = "pending"  # pending|running|success|failed
    percent: int = 0
    message: str = ""


def _registry_url() -> str:
    return getattr(webui_config, "registry_url", "") or ""


def _get_package_manager() -> _pm.PackageManager:
    """优先使用 config.package_manager；否则探测并缓存。"""
    global _PM
    if _PM is not None:
        return _PM
    override = getattr(webui_config, "package_manager", "") or ""
    if override and override in _pm.PM_INSTALL_CMD:
        exe = __import__("shutil").which(override) or __import__("sys").executable
        _PM = _pm.PackageManager(name=override, executable=exe)
    else:
        _PM = _pm.detect_package_manager()
    return _PM


_loaded_cache: dict[str, Any] | None = None
_loaded_at: float = 0.0


async def _fetch_remote(url: str) -> dict[str, Any] | None:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
    except Exception:  # noqa: BLE001
        return None


def _load_local_cache() -> dict[str, Any]:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"plugins": []}


def _save_local_cache(data: dict[str, Any]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False), "utf-8")


async def _ensure_catalog() -> dict[str, Any]:
    global _loaded_cache, _loaded_at
    now = time.time()
    if _loaded_cache is not None and now - _loaded_at < _CACHE_TTL:
        return _loaded_cache
    url = _registry_url()
    data: dict[str, Any] | None = None
    if url:
        data = await _fetch_remote(url)
        if data is not None:
            _save_local_cache(data)
    if data is None:
        data = _load_local_cache()
        data["__fallback"] = True
    _loaded_cache = data
    _loaded_at = now
    return data


async def _installed_pip_names() -> set[str]:
    """委托给 package_manager.list_installed；失败/无 pip 时返回空集。"""
    return await _pm.list_installed(_get_package_manager())


async def list_plugins() -> dict[str, Any]:
    catalog = await _ensure_catalog()
    installed = await _installed_pip_names()
    plugins = []
    for p in catalog.get("plugins", []):
        p = dict(p)
        p["installed"] = (p.get("pip_name", "") or "").lower() in installed
        plugins.append(p)
    return {"plugins": plugins, "fallback": bool(catalog.get("__fallback"))}


async def get_plugin(name: str) -> dict[str, Any] | None:
    catalog = await _ensure_catalog()
    for p in catalog.get("plugins", []):
        if p.get("name") == name:
            installed = await _installed_pip_names()
            out = dict(p)
            out["installed"] = (p.get("pip_name", "") or "").lower() in installed
            return out
    return None


async def _lookup(name: str) -> dict[str, Any]:
    p = await get_plugin(name)
    if p is None:
        raise UnknownPlugin(name)
    return p


async def start_install(name: str) -> str:
    p = await _lookup(name)
    return _spawn(p["pip_name"], "install")


async def start_uninstall(name: str) -> str:
    p = await _lookup(name)
    if not p.get("installed"):
        raise MarketError("not_installed")
    return _spawn(p["pip_name"], "uninstall")


def _spawn(pip_name: str, action: str) -> str:
    tid = uuid.uuid4().hex
    task = InstallTask(task_id=tid, pip_name=pip_name, action=action)
    _TASKS[tid] = task
    asyncio.create_task(_run(task))
    return tid


async def _run(task: InstallTask) -> None:
    task.status = "running"
    task.percent = 10
    try:
        pm_ = _get_package_manager()
        rc, out = await _pm.run_action(pm_, task.action, task.pip_name)
        task.percent = 100
        if rc == 0:
            task.status = "success"
        else:
            task.status = "failed"
        task.message = out[-500:]
    except Exception as e:  # noqa: BLE001
        task.status = "failed"
        task.message = str(e)


def get_task(task_id: str) -> InstallTask | None:
    return _TASKS.get(task_id)
```

- [ ] **Step 4:** Run `pdm run pytest tests/services/test_market_service.py -v`。测试通过 `from entari_plugin_webui import webui_config` 设置 `registry_url`/`package_manager`，conftest 的 `_reset_global_state`（Phase 2 Task 2.5）已自动重置 `registry_url` 为 `""`，并需同步重置 `market_service._PM = None`。提交。

---

## Task 6.3：market 路由

**Files:** Create `api/market.py`

- [ ] **Step 1:** 实现（含安装名校验由 service 强制）

```python
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..api.deps import require_auth
from ..services.market_service import (
    MarketError,
    UnknownPlugin,
    get_plugin,
    get_task,
    list_plugins,
    start_install,
    start_uninstall,
)

router = APIRouter(prefix="/api/market", tags=["market"], dependencies=[Depends(require_auth)])


class NameBody(BaseModel):
    name: str


@router.get("/plugins")
async def list_():
    return {"success": True, **(await list_plugins())}


@router.get("/plugins/{name}")
async def detail(name: str):
    p = await get_plugin(name)
    if p is None:
        return {"success": False, "code": "plugin_not_found"}, 404
    return {"success": True, "data": p}


@router.post("/install")
async def install(body: NameBody):
    try:
        tid = await start_install(body.name)
        return {"success": True, "task_id": tid}
    except UnknownPlugin:
        return {"success": False, "code": "unknown_plugin"}, 400
    except MarketError as e:
        return {"success": False, "code": "market_error", "message": str(e)}, 400


@router.post("/uninstall")
async def uninstall(body: NameBody):
    try:
        tid = await start_uninstall(body.name)
        return {"success": True, "task_id": tid}
    except UnknownPlugin:
        return {"success": False, "code": "unknown_plugin"}, 400
    except MarketError as e:
        return {"success": False, "code": "market_error", "message": str(e)}, 400


@router.get("/tasks/{task_id}")
async def task(task_id: str):
    t = get_task(task_id)
    if t is None:
        return {"success": False, "code": "task_not_found"}, 404
    return {
        "success": True,
        "task_id": t.task_id,
        "pip_name": t.pip_name,
        "action": t.action,
        "status": t.status,
        "percent": t.percent,
        "message": t.message,
    }
```

- [ ] **Step 2:** 挂 router。`pdm run format && pdm run lint && pdm run typecheck`。提交。

---

## Task 6.4：api 测试

**Files:** `tests/api/test_market.py`

- [ ] **Step 1:**

```python
def test_list(client, monkeypatch):
    from entari_plugin_webui.api import market as M
    async def _l():
        return {"plugins": [{"name": "demo", "installed": False}], "fallback": False}
    monkeypatch.setattr(M, "list_plugins", _l)
    r = client.get("/api/market/plugins")
    assert r.json()["plugins"][0]["name"] == "demo"


def test_install_unknown_400(client, monkeypatch):
    from entari_plugin_webui.api import market as M
    from entari_plugin_webui.services.market_service import UnknownPlugin
    async def _i(name):
        raise UnknownPlugin(name)
    monkeypatch.setattr(M, "start_install", _i)
    r = client.post("/api/market/install", json={"name": "x"})
    assert r.status_code == 400 and r.json()["code"] == "unknown_plugin"
```

- [ ] **Step 2:** Run → PASS。提交。

---

## Phase 6 完成标准

- 远程拉取成功 → 写缓存；失败 → 回退本地缓存并标记 `fallback`
- 包管理器按「锁文件 → 可执行 → pip 兜底」探测，虚拟环境无 pip 时仍可工作；config `package_manager` 可强制覆盖
- 安装/卸载名必须命中目录；按声明 `pip_name` 经探测到的 PM 执行；任务轮询可用
- ruff/pyright/pytest 全绿
