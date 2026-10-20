from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from arclet.entari.config.file import EntariConfig
from arclet.entari.config.schema.registry import _schema_fragments
from arclet.entari.plugin import (
    disable_plugin,
    enable_plugin,
    find_plugin,
    get_plugin_references,
    get_plugin_referents,
    get_plugins,
)
from arclet.entari.plugin import reload_plugin as _reload_plugin
from arclet.entari.plugin.model import Plugin, PluginMetadata
from arclet.entari.plugin.service import plugin_service

from ..core.error import PluginNotFound


def _authors(meta: PluginMetadata) -> list[str]:
    out = []
    for a in meta.author or []:
        if isinstance(a, dict):
            out.append(a.get("name", str(a)))
        else:
            out.append(str(a))
    return out


PROJECT_ROOT = EntariConfig.instance.path.parent.resolve()
ENV_ROOT = Path(sys.prefix).resolve()


def is_project_module(module):

    path = getattr(module, "__file__", None)
    if path is None:
        return False  # 内建模块

    path = Path(path).resolve()

    return path.is_relative_to(PROJECT_ROOT) and not path.is_relative_to(ENV_ROOT)


def _subplugin_root(plug: Plugin) -> str | None:
    return plugin_service._subplugined.get(plug.id)


def _relative_key(plug: Plugin) -> str | None:
    root = _subplugin_root(plug)
    return plug.id[len(root) :] if root else None


def _fragment_parts(record_path: tuple[str, ...], relative_key: str) -> tuple[str, ...] | None:
    if not record_path or record_path[0] != relative_key:
        return None
    return record_path[1:]


def _has_own_schema(plug: Plugin) -> bool:
    meta = plug.metadata
    if meta is not None and getattr(meta, "config", None):
        return True
    # entari 0.19 没有公开的"按路径查询 fragment"API，只能读私有注册表
    records = _schema_fragments.get(plug._config_key, [])
    relative = _relative_key(plug)
    if relative is None:
        return bool(records)
    return any(_fragment_parts(record.path, relative) is not None for record in records)


def serialize_plugin(plug: Plugin, _force: bool = False) -> dict[str, Any]:
    meta = plug.metadata
    if plug.id == "$":
        return {}
    configurable = _has_own_schema(plug) or bool(plug.config)
    type = "common"
    if plug.id.startswith("$"):
        type = "rootless"
    elif plug.id.startswith("arclet.entari"):
        type = "built-in"
    elif is_project_module(plug.module):
        type = "local"
    parent = plugin_service._subplugined.get(plug.id)
    parent_plug = plugin_service.plugins.get(parent) if parent else None
    parent_enabled = None
    if parent:
        parent_enabled = bool(parent_plug and parent_plug.is_available and parent not in plugin_service._unloaded)
    disable = plug.config.get("$disable") if plug.config else None
    state = "disabled" if disable else ("enabled" if plug.is_available else "unavailable")
    return {
        "id": plug.id,
        "uid": plug.uid,
        "type": type,
        "path": plug.path,
        "name": meta.name if meta else plug.id,
        "version": meta.version if meta else None,
        "description": meta.description if meta else None,
        "license": meta.license if meta else None,
        "authors": _authors(meta) if meta else [],
        "icon": meta.icon if meta else None,
        "urls": (meta.urls or {}) if meta else {},
        "classifier": (meta.classifier or []) if meta else [],
        "requirements": (meta.requirements or []) if meta else [],
        "enabled": plug.is_available,
        "available": plug.available,
        "is_static": plug.is_static,
        "reusable": plug.reusable,
        "subplugins": sorted(plug.subplugins or set()),
        "config": dict(plug.config or {}),
        "configurable": configurable,
        "references": sorted(get_plugin_references(plug)),
        "referents": sorted(get_plugin_referents(plug)),
        "readme": meta.readme if meta else None,
        "parent": parent,
        "has_metadata": meta is not None,
        "has_config_schema": _has_own_schema(plug),
        "config_key": plug._config_key,
        "unloaded": False,
        "can_unload": bool(not plug.is_static and not plug.id.startswith("$") and parent is None),
        "state": state,
        "disable_expr": disable if isinstance(disable, str) else None,
        "parent_enabled": parent_enabled,
    }


def list_plugins() -> list[dict[str, Any]]:
    results = [serialize_plugin(p) for p in get_plugins(subplugged=True)]
    return [r for r in results if r]


def get_plugin(plugin_id: str) -> dict[str, Any]:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    return serialize_plugin(plug, _force=True)


async def toggle_plugin(plugin_id: str, *, enable: bool) -> bool:
    return (await enable_plugin(plugin_id)) if enable else (await disable_plugin(plugin_id))


async def reload_plugin(plugin_id: str) -> bool:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    result = await _reload_plugin(plug.id)
    return bool(result)


def update_plugin_config(plugin_id: str, config: dict[str, Any]) -> None:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    # 复用 config_service 的路径解析，子插件写到父配置的 `.child` 下
    from .config_service import update_section

    update_section(f"plugins:{plugin_id}", config)
