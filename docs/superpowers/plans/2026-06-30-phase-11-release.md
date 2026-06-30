# Phase 11 — 测试补齐、CI、Docker、发布

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** 补齐端到端与 WS 测试、统一错误中间件、CI workflow、Dockerfile、docker-compose、README；最终全绿并可独立部署。

**Architecture:** 后端统一 `APIError` 中间件替换各路由手写返回+状态码；CI 三 job；Dockerfile 多阶段。

**Tech Stack:** pytest/pytest-asyncio、GitHub Actions、Docker（node:20 + python:3.11）、pdm。

---

## 文件结构

- Modify: `src/entari_plugin_webui/api/router.py`（统一异常中间件 + 路由返回改造）
- Modify: 各 `api/*.py`（service 抛领域异常后删除手写 `return ..., 404`，改抛 `HTTPException` 或业务异常）
- Create: `.github/workflows/ci.yml`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `README.md`（含安装/配置/认证/故障恢复/扩展开发）
- Modify: `tests/conftest.py`、补测试

---

## Task 11.1：统一错误中间件

**Files:** Modify `api/router.py`

- [ ] **Step 1:** 定义 `APIError` 体系在 `core/errors.py`：

```python
from __future__ import annotations


class AppError(Exception):
    code: str = "error"
    status: int = 400
    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.code
        super().__init__(self.message)


class PluginNotFound(AppError): code = "plugin_not_found"; status = 404
class ConfigSectionNotFound(AppError): code = "section_not_found"; status = 404
class MarketError(AppError): code = "market_error"; status = 400
class UnknownPlugin(MarketError): code = "unknown_plugin"; status = 400
class AuthRequired(AppError): code = "auth_required"; status = 401
class Forbidden(AppError): code = "forbidden"; status = 403
class TooManyRequests(AppError): code = "rate_limited"; status = 429
```

> 原 `services/plugin_service.py`、`services/market_service.py` 中的 `PluginNotFound`/`UnknownPlugin` 改为从此导入。`LoginThrottle` 触发抛 `TooManyRequests`。

- [ ] **Step 2:** router.py 中间件：

```python
from starlette.responses import JSONResponse
from ..core.errors import AppError

@app.middleware("http")
async def _error_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except AppError as e:
        return JSONResponse({"success": False, "code": e.code, "message": e.message}, status_code=e.status)
    except Exception as e:  # noqa: BLE001
        import logging
        logging.getLogger(__name__).exception("unhandled")
        return JSONResponse({"success": False, "code": "internal_error", "message": str(e)}, status_code=500)
```

- [ ] **Step 3:** 各路由删去 `return {...}, 404` 风格手写响应；改让 service 抛 `AppError` 子类，路由内不再 try/except；`LoginThrottle` 在 auth.py 命中时抛 `TooManyRequests`（中间件映射 429 + Retry-After 由路由前置装饰器或中间件补头）。

> Retry-After 头：`TooManyRequests` 携带 `headers`——在中间件中按 `e` 属性输出：为 `TooManyRequests` 添加类属性 `retry_after: int | None`；中间件 `headers={"Retry-After": str(e.retry_after)} if e.retry_after else None`。

- [ ] **Step 4:** `pdm run test` 通过；`pdm run format && pdm run lint && pdm run typecheck`。提交 `git commit -m "refactor(api): unified AppError middleware"`。

---

## Task 11.2：WS 端到端测试

**Files:** Create `tests/test_live_routes.py`（可选）

由于 `app` fixture 已返回 `server.app`（含 `add_websocket_route("ws/logs")` 注册的 WS 路由），直接复用现有 `client` fixture 即可。LogRingBuffer 是进程级单例，可直接清空写入：

```python
def test_ws_history_and_increment(client):
    set_local_mode(True)
    from entari_plugin_webui.core.log_stream import get_log_buffer
    buf = get_log_buffer()
    buf.clear()
    buf.write("hello\n")
    with client.websocket_connect("/ws/logs") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "history" and "hello" in msg["data"]
        buf.write("world\n")
        msg2 = ws.receive_json()
        assert msg2["type"] == "log" and "world" in msg2["data"]
```

注意：此测试依赖 `set_local_mode(True)` 和 `client`（即 `server.app`）。由于 `get_log_buffer()` 返回单例，`clear()` 不影响其他并行测试（pytest 按序执行）。

提交 `git commit -m "test: ws logs e2e"`。

---

## Task 11.3：CI workflow

**Files:** Create `.github/workflows/ci.yml`

- [ ] **Step 1:**

```yaml
name: CI
on: [push, pull_request]
jobs:
  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci && npm run lint
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pdm-project/setup-pdm@v4
        with: { python-version: '3.11' }
      - run: pdm install
      - run: pdm run format && pdm run lint && pdm run typecheck
      - run: pdm run pyright src/entari_plugin_webui
  build:
    needs: [lint-frontend, lint-backend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - uses: pdm-project/setup-pdm@v4
        with: { python-version: '3.11' }
      - run: cd frontend && npm ci && npm run build
      - run: pdm install
      - run: pdm run test
```

- [ ] **Step 2:** 提交 `git commit -m "ci: lint + build + test matrix"`.

---

## Task 11.4：Dockerfile & compose

**Files:** Create `Dockerfile`、`docker-compose.yml`

- [ ] **Step 1: Dockerfile**（多阶段）

```dockerfile
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend
RUN pip install pdm
WORKDIR /app
COPY pyproject.toml pdm.lock* ./
COPY src/ ./src/
COPY README.md ./
COPY --from=frontend /build/../src/entari_plugin_webui/static/frontend ./src/entari_plugin_webui/static/frontend
RUN pdm build

FROM python:3.11-slim
WORKDIR /app
COPY --from=backend /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl
EXPOSE 5150
CMD ["python", "-m", "arclet.entari"]
```

- [ ] **Step 2: docker-compose.yml**

```yaml
services:
  entari-webui:
    build: .
    container_name: entari-webui
    ports: ["5150:5150"]
    volumes:
      - ./entari.yml:/app/entari.yml:ro
      - ./data:/app/data
    environment:
      TZ: Asia/Shanghai
    restart: unless-stopped
```

- [ ] **Step 3:** 提交 `git commit -m "build: multi-stage Dockerfile and compose"`.

---

## Task 11.5：README

**Files:** Create `README.md`

- [ ] **Step 1:** 内容含：功能特性、安装（pip/pdm）、`entari.yml` 配置示例（database + server + webui）、认证说明（本地免认证、远程首次生成）、**故障恢复**（删除 `plugins.webui.password` 重启即重生成口令）、Docker 部署、扩展开发示例（`webui_extend` 注册菜单/页面/路由/i18n/权限）、风险须知（扩展 iframe 沙箱、来源仅限本机插件）。

- [ ] **Step 2:** 提交 `git commit -m "docs: README with setup, recovery, extension guide"`.

---

## Task 11.6：最终验证

- [ ] **Step 1:**

Run:
```bash
pdm run format && pdm run lint && pdm run typecheck
pdm run test
cd frontend && npm run lint && npm run build
```

Expected: 全部通过；前端产物落在 `src/entari_plugin_webui/static/frontend/index.html`。

- [ ] **Step 2:** 提交验证记录（如必要）。`git log --oneline` 复核 commit 序列。

---

## Phase 11 完成标准

- 统一错误中间件生效；路由层无手写 `return ..., 40x`
- WS 端到端测试通过
- CI 三 job 配置就绪且本地等价命令全绿
- Dockerfile/compose 可构建运行
- README 覆盖安装/认证/恢复/扩展