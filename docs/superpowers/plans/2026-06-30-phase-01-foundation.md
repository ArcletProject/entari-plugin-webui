# Phase 01 — 项目骨架与基础设施

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans. Steps use `- [ ]` for tracking.

**Goal:** 建立可在 `pdm run pytest` 下运行（即便空测试）的 Python 包骨架，含依赖、配置模型、插件入口的 `/api/health` 与 SPA fallback 占位、CORS、lint（ruff + pyright）与构建脚本。

**Architecture:** 包 `entari_plugin_webui`；`api/router.py` 用 `FastAPI` 聚合后 `entari_plugin_server.replace_asgi(app)` 替换 server app；扩展路由仍以 `add_route` 在 startup 挂到 `server.app`。配置模型 `Config` 用 `BasicConfModel`。

**Tech Stack:** Python ≥3.10、pdm-backend、arclet-entari、entari-plugin-server、entari-plugin-database、fastapi、starlette、httpx、ruff、pyright、pytest。

---

## 文件结构（本 phase 产出）

- Modify: `pyproject.toml`（覆盖现有）
- Create: `src/entari_plugin_webui/__init__.py` — 插件元数据、入口、server wiring、health、SPA fallback
- Create: `src/entari_plugin_webui/config.py` — `Config` 模型
- Create: `src/entari_plugin_webui/api/__init__.py` — re-export router builder
- Create: `src/entari_plugin_webui/api/router.py` — 构建 FastAPI app
- Create: `src/entari_plugin_webui/api/health.py` — `/api/health`
- Create: `src/entari_plugin_webui/core/__init__.py`（空占位）
- Create: `src/entari_plugin_webui/services/__init__.py`（空占位）
- Create: `src/entari_plugin_webui/models/__init__.py`（空占位）
- Create: `src/entari_plugin_webui/static/.gitkeep`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py` — 共享 fixture（app/client）
- Create: `tests/test_health.py`

---

## Task 1.1：pyproject.toml 依赖与工具链

**Files:** Modify `pyproject.toml`

- [ ] **Step 1: 写入依赖与 PDM scripts、ruff/pyright 配置**

```toml
[project]
name = "entari-plugin-webui"
version = "0.1.0"
description = "WebUI Plugin for Entari"
authors = [{name = "RF-Tar-Railt", email = "rf_tar_railt@qq.com"}]
dependencies = [
    "arclet-entari[dotenv,yaml]>=0.18.0",
    "entari-plugin-server>=0.7.1",
    "entari-plugin-database>=0.3.2",
    "fastapi>=0.135.1",
    "httpx>=0.27",
    "ansi2html>=1.9.2",
]
requires-python = ">=3.10"
readme = "README.md"
license = {text = "MIT"}

[dependency-groups]
dev = [
    "arclet-entari[reload]>=0.18.0",
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "ruff>=0.15",
    "pyright>=1.1",
    "anyio>=4",
]

[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"

[tool.pdm]
distribution = true

[tool.pdm.build]
includes = ["src/entari_plugin_webui"]

[tool.pdm.scripts]
build-frontend = "cd frontend && npm ci && npm run build"
build-all = { composite = ["build-frontend", "pdm build"] }
dev = "cd frontend && npm run dev"
format = "ruff format src/ tests/"
lint = "ruff check src/ tests/ --fix"
typecheck = "pyright src/entari_plugin_webui"
test = "pytest -q"

[tool.ruff]
line-length = 120
target-version = "py310"
include = ["src/**.py", "tests/**.py"]
respect-gitignore = true

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "W", "C", "T", "PYI", "PT", "Q"]
ignore = ["C901", "T201", "E731", "E402", "PYI055"]

[tool.ruff.lint.isort]
force-sort-within-sections = false
extra-standard-library = ["typing_extensions"]


[tool.pyright]
pythonVersion = "3.10"
pythonPlatform = "All"
typeCheckingMode = "basic"
venvPath = "."
venv = ".venv"
reportMissingImports = true
```

- [ ] **Step 2: 安装**

Run: `pdm install`
Expected: 依赖解析成功；生成 `pdm.lock`、`.venv`。

- [ ] **Step 3: 提交**

```bash
git add pyproject.toml pdm.lock
git commit -m "chore: pin dependencies and tooling (ruff/pyright/pytest)"
```

---

## Task 1.2：Config 模型

**Files:** Create `src/entari_plugin_webui/config.py`

- [ ] **Step 1: 写配置模型**

```python
from arclet.entari.config.models.default import BasicConfModel


class Config(BasicConfModel):
    password: str = ""
    registry_url: str = ""
    session_ttl: int = 43200
    log_buffer_lines: int = 5000
    login_rate_limit: str = "5/60s"
```

- [ ] **Step 2: 提交**

```bash
git add src/entari_plugin_webui/config.py
git commit -m "feat(config): add plugin Config model"
```

---

## Task 1.3：健康端点

**Files:** Create `src/entari_plugin_webui/api/health.py`

- [ ] **Step 1: 写 /api/health 路由**

```python
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])

_START = datetime.utcnow()


@router.get("/health")
async def health() -> dict:
    from pathlib import Path

    frontend_built = (Path(__file__).resolve().parent.parent / "static" / "frontend" / "index.html").exists()
    return {
        "status": "ok",
        "uptime_seconds": int((datetime.utcnow() - _START).total_seconds()),
        "frontend_built": frontend_built,
    }
```

- [ ] **Step 2: 提交**

```bash
git add src/entari_plugin_webui/api/health.py
git commit -m "feat(api): add /api/health endpoint"
```

---

## Task 1.4：router 聚合 + 插件入口 + server wiring

**Files:** Create `src/entari_plugin_webui/api/__init__.py`, `api/router.py`, 修改 `__init__.py`

- [ ] **Step 1: api/__init__.py 暴露 create_app**

```python
from .router import create_app

__all__ = ["create_app"]
```

- [ ] **Step 2: api/router.py 构建 FastAPI 并挂 router**

```python
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

from .health import router as health_router


def create_app() -> FastAPI:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
    app = FastAPI(title="Entari WebUI", middleware=middleware)
    app.include_router(health_router)
    return app
```

- [ ] **Step 3: 写插件入口 `__init__.py`**

```python
"""Entari Plugin: WebUI 服务（重设计版）"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from starlette.responses import FileResponse, Response

from arclet.entari import plugin
from arclet.entari.event.lifespan import Startup
from entari_plugin_server import add_route, replace_asgi, server

from .config import Config

__version__ = "0.1.0"
__all__ = ["webui_extend", "MenuItem", "WebUIExtension"]

_STATIC_DIR = Path(__file__).parent / "static"
_FRONTEND_DIR = _STATIC_DIR / "frontend"


# ---------- 插件元数据 ----------
plugin.metadata(
    "WebUI 服务",
    [{"name": "RF-Tar-Railt", "email": "rf_tar_railt@qq.com"}],
    __version__,
    description="基于 Vite + Vue 3 + Element Plus 的可视化管理面板",
    urls={"homepage": "https://github.com/ArcletProject/entari-plugin-webui"},
    config=Config,
)


# ---------- 替换为我们的 FastAPI app ----------
from .api import create_app as _create_app  # noqa: E402

replace_asgi(_create_app())


# ---------- 静态资源挂载 ----------
if _FRONTEND_DIR.exists():
    if (_FRONTEND_DIR / "assets").exists():
        server.mount("/assets", str(_FRONTEND_DIR / "assets"))
    # Vite 默认产物 chunk 路径为 assets/，无 _nuxt；保留通用挂载点
    if (_FRONTEND_DIR / "_nuxt").exists():
        server.mount("/_nuxt", str(_FRONTEND_DIR / "_nuxt"))


# ---------- SPA fallback ----------
@add_route("/{path:path}", methods=["GET"])
async def _spa_fallback(path: str) -> Response:
    if path.startswith("api/") or path.startswith("ws/"):
        return Response(status_code=404)
    if not _FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'pdm run build-frontend'.",
            status_code=503,
        )
    file_path = _FRONTEND_DIR / path
    if file_path.is_file():
        return FileResponse(file_path)
    index = _FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return Response(status_code=404)


@add_route("/", methods=["GET"])
async def _root() -> Response:
    if not _FRONTEND_DIR.exists():
        return Response(
            content="Frontend not built. Run 'pdm run build-frontend'.",
            status_code=503,
        )
    index = _FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return Response(status_code=404)


@plugin.listen(Startup)
async def _on_startup() -> None:
    host = server.host or "127.0.0.1"
    port = server.port
    plugin.logger.info(f"[WebUI] 管理面板已启动: http://{host}:{port}/")
```

> 注：`replace_asgi` 替换 server.app 并保留旧路由；`add_route` 注册到当前 `server.app`。`plugin.logger` 为 entari logger 别名（若不可用则回退 `from loguru import logger`）。
>
> **导入副作用提醒**：`__init__.py` 在 import 时即调用 `replace_asgi(...)`，会触碰 entari-plugin-server 的全局 `server` 单例。若测试 `from entari_plugin_webui.api import create_app` 因 global server 未初始化而报错，改为延迟装配：把 `replace_asgi(_create_app())` 移入 `_wire_server()` 函数，仅在 `Startup` listener 中调用一次；`add_route` 装饰的静态/SPA fallback 也迁入 `_wire_server` 之后。同时在 `__init__.py` 顶部加懒初始化标志避免重复 wiring。最终保持 `create_app()` 可被 TestClient 独立导入、不受全局 server 影响。

- [ ] **Step 4: 校验导入与 lint**

Run: `pdm run format && pdm run lint && pdm run typecheck`
Expected: 无错误。

- [ ] **Step 5: 提交**

```bash
git add src/entari_plugin_webui/
git commit -m "feat: bootstrap plugin entry, app wiring, SPA fallback"
```

---

## Task 1.5：测试夹具与 health 集成测

**Files:** Create `tests/conftest.py`, `tests/test_health.py`

- [ ] **Step 1: conftest 启动真实 Entari 实例 + 提供 client fixture**

注意：测试通过 `pytest_configure` 的 stash 注入 entari 配置，使用 session-scoped fixture 启动完整 Entari 实例（加载本插件）。`app` fixture 返回 `server.app`（已通过 `replace_asgi` 替换过的 Entari server ASGI app），后续 phase 测试均透过此 fixture 访问所有路由（含 `add_route`/`add_websocket_route` 注册的路由）。

```python
from __future__ import annotations

import asyncio
from creart import it
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
import pytest_asyncio
from launart import Launart
from fastapi import FastAPI
from fastapi.testclient import TestClient


ENTARI_YML_TEXT = pytest.StashKey[str]()
ENTARI_WEBUI_CONFIG = pytest.StashKey[dict[str, Any]]()


def pytest_configure(config: pytest.Config):
    config.stash[ENTARI_YML_TEXT] = """
basic:
  log:
    level: debug
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

    load_plugin("entari_plugin_webui", config=request.config.stash[ENTARI_WEBUI_CONFIG])


@pytest_asyncio.fixture(scope="session", autouse=True)
async def entari_init(_entari_init, after_entari_init: None):
    from arclet.letoderea.utils import set_event_loop

    set_event_loop(asyncio.get_running_loop())
    manager = it(Launart)
    task = asyncio.create_task(_entari_init.run_async())

    await manager.status.wait_for_blocking()

    yield _entari_init

    manager._on_sys_signal(None, None, task)
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.fixture(name="entari")
def entari_instance(entari_init):
    pass


@pytest.fixture()
def app(after_entari_init: None) -> FastAPI:
    from entari_plugin_server import server

    return server.app  # type: ignore


@pytest.fixture()
def client(app):
    return TestClient(app)
```

- [ ] **Step 2: 写健康测试**

```python
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert isinstance(body["uptime_seconds"], int)
    assert body["frontend_built"] is False
```

- [ ] **Step 3: 运行**

Run: `pdm run pytest tests/test_health.py -v`
Expected: PASS。

- [ ] **Step 4: 提交**

```bash
git add tests/
git commit -m "test: health endpoint integration test"
```

---

## Task 1.6：占位包与 .gitignore

**Files:** Create `core/__init__.py`、`services/__init__.py`、`models/__init__.py`、`static/.gitkeep`；更新 `.gitignore`

- [ ] **Step 1: 建立 `__init__.py`**

```bash
for d in core services models; do echo '"""'"$d"' package"""' > src/entari_plugin_webui/$d/__init__.py; done
touch src/entari_plugin_webui/static/.gitkeep
```

- [ ] **Step 2: .gitignore 追加**

```
src/entari_plugin_webui/static/frontend/
*.pyc
__pycache__/
.venv/
.pdm-build/
dist/
frontend/node_modules/
frontend/dist/
```

- [ ] **Step 3: 提交**

```bash
git add src/entari_plugin_webui/{core,services,models,__init__}.py* .gitignore src/entari_plugin_webui/static/.gitkeep
git commit -m "chore: placeholder packages and gitignore"
```

---

## Phase 1 完成标准

- `pdm run format && pdm run lint && pdm run typecheck` 全绿
- `pdm run pytest -q` 通过（至少 health 测试）
- `python -c "import entari_plugin_webui"` 无错误
