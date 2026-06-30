# Phase 04 — 配置编辑（entari.yml）

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** 实现 `config_service` 读写 `entari.yml` 各 section 并生成 JSON Schema，提供 `/api/config`、`/api/config/{section}`、`/api/config/{section}/schema`、PUT 写入。

**Architecture:** `services/config_service.py` 封装 `EntariConfig.instance`（data/basic/adapters/plugin 段）与 `config_model_schema(BasicConfig | plugin.metadata.config)`；注入 `$disable/$priority/$filter/$prefix/$static/$optional` 元属性。`api/config.py` 薄路由，本地直通、远程 `require_auth`。

**Tech Stack:** arclet.entari.config（`EntariConfig`、`config_model_schema`、`config_model_keys`、`config_model_dump`）、`BasicConfig`、ruamel CommentedMap 解包、fastapi。

---

## 文件结构

- Create: `src/entari_plugin_webui/services/config_service.py`
- Create: `src/entari_plugin_webui/api/config.py`
- Modify: `api/router.py` 挂 router
- Create: `tests/services/test_config_service.py`、`tests/api/test_config.py`

---

## Task 4.1：config_service

**Files:** Create `services/config_service.py`

- [ ] **Step 1: 测试 `tests/services/test_config_service.py`**

```python
from __future__ import annotations

from unittest.mock import MagicMock

from entari_plugin_webui.services import config_service as cs


def _cfg(data):
    cfg = MagicMock()
    cfg.basic = data.get("basic", {})
    cfg.plugin = data.get("plugins", {})
    cfg.data = data
    cfg.save = MagicMock()
    return cfg


def test_list_sections(monkeypatch):
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg(
        {"basic": {"prefix": ["/"]}, "plugins": {"webui": {}}, "adapters": []})))
    out = cs.list_sections()
    assert "basic" in out["sections"]
    assert "plugins.webui" in out["plugin_sections"]


def test_get_section_basic(monkeypatch):
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg({"basic": {"prefix": ["/"]}})))
    out = cs.get_section("basic")
    assert out == {"prefix": ["/"]}


def test_get_section_plugin(monkeypatch):
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=_cfg({"plugins": {"webui": {"password": "x"}}})))
    out = cs.get_section("plugins.webui")
    assert out == {"password": "x"}


def test_update_section(monkeypatch):
    cfg = _cfg({"basic": {"prefix": ["/"]}})
    monkeypatch.setattr(cs, "EntariConfig", MagicMock(instance=cfg))
    cs.update_section("basic", {"prefix": ["/a"]})
    assert cfg.data["basic"]["prefix"] == ["/a"]
    cfg.save.assert_called_once()


def test_inject_meta_properties(monkeypatch):
    import types
    SchemaModel = types.SimpleNamespace
    monkeypatch.setattr(cs, "config_model_schema", lambda m, ref_root=None: {"type": "object", "properties": {}})
    out = cs.get_schema_for_section("basic")
    for key in ("$disable", "$priority", "$filter", "$prefix", "$static", "$optional"):
        assert key in out["schema"]["properties"]
```

- [ ] **Step 2: 实现 `services/config_service.py`**

```python
from __future__ import annotations

from typing import Any

from arclet.entari import find_plugin
from arclet.entari.config import EntariConfig, config_model_schema

META_PROPS = {
    "$disable": {"type": ["boolean", "string", "null"], "title": "禁用", "default": None},
    "$priority": {"type": ["integer", "null"], "title": "加载优先级", "default": None},
    "$filter": {"type": ["string", "null"], "title": "条件过滤", "default": None},
    "$prefix": {"type": ["string", "null"], "title": "前缀覆盖", "default": None},
    "$static": {"type": ["boolean", "null"], "title": "静态", "default": None},
    "$optional": {"type": ["boolean", "null"], "title": "可选", "default": None},
}


def _unwrap(obj: Any) -> Any:
    if hasattr(obj, "items") and callable(obj.items):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            out[k] = _unwrap(v)
        return out
    if isinstance(obj, list):
        return [_unwrap(v) for v in obj]
    return obj


def list_sections() -> dict[str, Any]:
    cfg = EntariConfig.instance
    data = _unwrap(cfg.data)
    plugin_sections = [f"plugins.{k}" for k in (cfg.plugin or {})]
    return {
        "sections": ["basic", "plugins", "adapters"],
        "plugin_sections": plugin_sections,
        "data": data,
    }


def get_section(section: str) -> Any:
    cfg = EntariConfig.instance
    if section == "basic":
        return _unwrap(cfg.basic)
    if section == "adapters":
        return _unwrap(cfg.data.get("adapters", []))
    if section == "plugins":
        return _unwrap(cfg.plugin)
    if section.startswith("plugins."):
        key = section[len("plugins.") :]
        return _unwrap((cfg.plugin or {}).get(key, {}))
    raise KeyError(section)


class ConfigSectionNotFound(Exception):
    pass


def update_section(section: str, data: Any) -> None:
    cfg = EntariConfig.instance
    if section == "basic":
        cfg.data["basic"] = data
    elif section == "adapters":
        cfg.data["adapters"] = data
    elif section == "plugins":
        cfg.data["plugins"] = data
    elif section.startswith("plugins."):
        key = section[len("plugins.") :]
        cfg.data.setdefault("plugins", {})[key] = data
    else:
        raise ConfigSectionNotFound(section)
    cfg.save()


def _with_meta_properties(schema: dict[str, Any]) -> dict[str, Any]:
    imports = schema.setdefault("properties", {})
    for k, v in META_PROPS.items():
        imports.setdefault(k, v)
    required = schema.setdefault("required", [])
    return schema


def get_schema_for_section(section: str) -> dict[str, Any]:
    if section == "basic":
        from arclet.entari.config import BasicConfig  # type: ignore  # noqa: PLC0415

        schema = config_model_schema(BasicConfig, ref_root="/properties/basic/")
    elif section == "adapters":
        schema = {"type": "array", "items": {"type": "object", "additionalProperties": True}}
    elif section == "plugins":
        schema = {"type": "object", "additionalProperties": True}
    elif section.startswith("plugins."):
        plugin_id = section[len("plugins.") :]
        if plugin_id.startswith("::"):
            plugin_id = "arclet.entari.builtins." + plugin_id[2:]
        plug = find_plugin(plugin_id)
        meta = getattr(plug, "metadata", None) if plug else None
        model = getattr(meta, "config", None) if meta else None
        if model is not None:
            base = config_model_schema(model)
            schema = _with_meta_properties(base)
        else:
            schema = _with_meta_properties({"type": "object", "additionalProperties": True})
    else:
        raise ConfigSectionNotFound(section)
    return {"schema": schema}
```

- [ ] **Step 3:** Run `pdm run pytest tests/services/test_config_service.py -v` → PASS。提交 `git commit -m "feat(service): config_service sections + schema"`.

---

## Task 4.2：config 路由

**Files:** Create `api/config.py`

- [ ] **Step 1: 实现**

```python
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .deps import require_auth
from ..services.config_service import (
    ConfigSectionNotFound,
    get_schema_for_section,
    get_section,
    list_sections,
    update_section,
)

router = APIRouter(prefix="/api/config", tags=["config"], dependencies=[Depends(require_auth)])


class SectionBody(BaseModel):
    data: dict | list


@router.get("")
async def list_():
    return {"success": True, **list_sections()}


@router.get("/{section}")
async def get_(section: str):
    try:
        return {"success": True, "section": section, "data": get_section(section)}
    except KeyError:
        return {"success": False, "code": "section_not_found"}, 404


@router.put("/{section}")
async def put_(section: str, body: SectionBody):
    try:
        update_section(section, body.data)
        return {"success": True, "message": "已保存"}
    except ConfigSectionNotFound:
        return {"success": False, "code": "section_not_found"}, 404


@router.get("/{section}/schema")
async def schema(section: str):
    try:
        return {"success": True, "section": section, **get_schema_for_section(section)}
    except ConfigSectionNotFound:
        return {"success": False, "code": "section_not_found"}, 404
```

> 注意：`GET /{section}/schema` 需在 `GET /{section}` 之前注册以避免 FastAPI 路径冲突——用 `router.api_route("/{section}/schema", methods=["GET"])` 置于 `get_` 之前，或在 include 时显式排序。FastAPI 按声明顺序匹配，先写 schema 路由即可。

- [ ] **Step 2:** 调整声明顺序：把 `schema` 路由放在 `get_` 之前；挂 router。

- [ ] **Step 3:** Run `pdm run format && pdm run lint && pdm run typecheck`。提交。

---

## Task 4.3：api 集成测试

**Files:** `tests/api/test_config.py`

- [ ] **Step 1: 测试**

```python
def test_list_sections(client, monkeypatch):
    from entari_plugin_webui.api import config as C
    monkeypatch.setattr(C, "list_sections", lambda: {"sections": ["basic"], "plugin_sections": [], "data": {}})
    r = client.get("/api/config")
    assert r.json()["success"] is True


def test_get_basic(client, monkeypatch):
    from entari_plugin_webui.api import config as C
    monkeypatch.setattr(C, "get_section", lambda s: {"prefix": ["/"]})
    r = client.get("/api/config/basic")
    assert r.json()["data"]["prefix"] == ["/"]


def test_get_schema(client, monkeypatch):
    from entari_plugin_webui.api import config as C
    monkeypatch.setattr(C, "get_schema_for_section", lambda s: {"schema": {"type": "object"}})
    r = client.get("/api/config/basic/schema")
    assert r.json()["schema"]["type"] == "object"


def test_update(client, monkeypatch):
    from entari_plugin_webui.api import config as C
    captured = {}
    monkeypatch.setattr(C, "update_section", lambda s, d: captured.update(s=s, d=d))
    r = client.put("/api/config/basic", json={"data": {"prefix": ["/a"]}})
    assert r.json()["success"] is True
    assert captured["d"] == {"prefix": ["/a"]}
```

- **第二步：** 挂载路由前需确保 `schema` 路由优先于 `{section}`；在 TestClient 中 `GET /api/config/basic/schema` 应命中 schema 而非 get_。运行测试 → PASS。

- [ ] **第三步：** 提交 `git commit -m "test(api): config section routes"`。

---

## Phase 4 完成标准

- `/api/config`（列出）、`GET/PUT /api/config/{section}`、`GET /api/config/{section}/schema` 可用（本地直通）
- schema 含元属性注入；插件无 config 模型时回退 `additionalProperties: true`
- service 与 api 测试通过；ruff/pyright/pytest 全绿