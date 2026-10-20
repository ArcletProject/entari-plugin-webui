from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from arclet.entari.config.file import EntariConfig
from arclet.entari.config.schema.registry import _schema_fragments
from arclet.entari.filter.parse import evaluate_disable
from arclet.entari.plugin import (
    find_plugin,
    get_plugin_references,
    get_plugin_referents,
    get_plugins,
    load_plugin,
    unload_plugin_async,
)
from arclet.entari.plugin import reload_plugin as _reload_plugin
from arclet.entari.plugin import reload_subplugin as _reload_subplugin
from arclet.entari.plugin.model import Plugin, PluginMetadata
from arclet.entari.plugin.service import plugin_service

from ..core.error import PluginError, PluginNotFound
from . import market_service

_unloaded_snapshots: dict[str, dict[str, Any]] = {}


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
    if isinstance(disable, str):
        try:
            disabled = evaluate_disable(disable)
        except Exception:
            disabled = not plug.is_available
    else:
        disabled = bool(disable)
    state = "disabled" if disabled else ("enabled" if plug.is_available else "unavailable")
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


def _plugin_entry(path: list[str]) -> dict[str, Any]:
    node = EntariConfig.instance.data.setdefault("plugins", {})
    root_key = path[0]
    root_entry, raw_key = _find_plugin_entry(node, root_key)
    if root_entry is not None and raw_key != root_key:
        node.pop(raw_key, None)
        node[root_key] = root_entry
    for key in path[:-1]:
        child = node.get(key)
        if not isinstance(child, dict):
            child = {}
            node[key] = child
        node = child
    target = node.get(path[-1])
    if not isinstance(target, dict):
        target = {}
        node[path[-1]] = target
    return target


def _find_plugin_entry(plugins: dict[str, Any], key: str) -> tuple[dict[str, Any] | None, str]:
    """在顶层 ``plugins`` 映射里按 raw form（``key``/``~key``/``?key``）查找条目。"""
    for candidate in (key, f"~{key}", f"?{key}"):
        value = plugins.get(candidate)
        if isinstance(value, dict):
            return value, candidate
    return None, key


async def toggle_plugin(plugin_id: str, *, enable: bool) -> dict[str, Any]:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    if plug.is_static or plug.id.startswith("$"):
        raise PluginError("Static or rootless plugin cannot be toggled")
    parent = _subplugin_root(plug)
    if parent:
        parent_plug = plugin_service.plugins.get(parent)
        if parent_plug is None or not parent_plug.is_available or parent in plugin_service._unloaded:
            raise PluginError("Parent plugin is not available")
    if enable:
        plug.enable()
    else:
        plug.disable()
    from . import config_service

    path = config_service.get_plugin_config_path(plugin_id)
    if path:
        if len(path) == 1:
            key = path[0]
            plugins = EntariConfig.instance.data.setdefault("plugins", {})
            entry, raw_key = _find_plugin_entry(plugins, key)
            body = {} if entry is None else {k: v for k, v in entry.items() if k not in ("$disable", "$optional")}
            if raw_key != key:
                plugins.pop(raw_key, None)
            plugins[key] = {**body, "$disable": True} if not enable else body
        else:
            entry = _plugin_entry(path)
            entry.pop("$optional", None)
            if enable:
                entry.pop("$disable", None)
            else:
                entry["$disable"] = True
    EntariConfig.instance.save()
    return serialize_plugin(plug, _force=True)


async def reload_plugin(plugin_id: str) -> bool:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    if _subplugin_root(plug) is not None:
        result = await _reload_subplugin(plug.id)
    else:
        result = await _reload_plugin(plug.id)
    return bool(result)


async def unload_plugin(plugin_id: str) -> dict[str, Any]:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    if plug.is_static or plug.id.startswith("$") or _subplugin_root(plug) is not None:
        raise PluginError("Only top-level non-static plugins can be unloaded")
    from . import config_service

    path = config_service.get_plugin_config_path(plugin_id)
    snapshot = serialize_plugin(plug, _force=True)
    cfg = EntariConfig.instance
    plugins = cfg.data.setdefault("plugins", {})
    key = path[0] if path else plug._config_key
    entry, raw_key = _find_plugin_entry(plugins, key)
    body = {} if entry is None else {k: v for k, v in entry.items() if k not in ("$disable", "$optional")}
    if raw_key != key:
        plugins.pop(raw_key, None)
    plugins[key] = {**body, "$optional": True}
    cfg.save()
    _unloaded_snapshots[key] = snapshot
    await unload_plugin_async(plug.id)
    return {**snapshot, "unloaded": True}


def _module_path_for(key: str) -> str:
    if key.startswith("::"):
        return f"arclet.entari.builtins.{key[2:]}"
    if "." in key or key.startswith("entari_plugin_"):
        return key
    names = EntariConfig.instance._plugin_names.get(key)
    if names:
        return names[0]
    return f"entari_plugin_{key}"


def list_unloaded_plugins() -> list[dict[str, Any]]:
    cfg = EntariConfig.instance
    results = []
    for raw_key, value in (cfg.plugin or {}).items():
        if not isinstance(value, dict):
            continue
        key = raw_key
        optional = bool(value.get("$optional"))
        if raw_key.startswith("?"):
            key = raw_key[1:]
            optional = True
        if not optional:
            continue
        if key in plugin_service.plugins:
            continue
        snapshot = _unloaded_snapshots.get(key, {})
        config = {k: v for k, v in value.items() if k not in ("$optional", "$disable")}
        if key.startswith("::"):
            pid = _module_path_for(key)
            ptype = "built-in"
        else:
            pid = snapshot.get("id", key)
            ptype = snapshot.get("type", "common")
        results.append(
            {
                "key": key,
                "id": pid,
                "display_key": f"?{key}",
                "name": snapshot.get("name", key),
                "description": snapshot.get("description"),
                "config": config,
                "module_path": _module_path_for(key),
                "type": ptype,
                "state": "unloaded",
            }
        )
    return results


async def load_unloaded(key: str) -> dict[str, Any]:
    cfg = EntariConfig.instance
    plugins = cfg.data.setdefault("plugins", {})
    entry = plugins.get(key)
    raw_key = key
    if entry is None:
        qkey = f"?{key}"
        if qkey in plugins:
            entry = plugins[qkey]
            raw_key = qkey
    if entry is None or not isinstance(entry, dict):
        raise PluginError(f"Unloaded plugin not found: {key}")
    clean = {k: v for k, v in entry.items() if k not in ("$optional", "$disable")}
    module_path = _module_path_for(key)
    original_names = cfg._plugin_names.get(key)
    cfg._plugin_names[key] = [module_path]
    try:
        result = load_plugin(key, clean)
    except Exception:
        result = None
    if result is None or getattr(result, "plugin", None) is None:
        if raw_key != key:
            plugins.pop(key, None)
        plugins[raw_key] = entry
        cfg.save()
        if original_names is None:
            cfg._plugin_names.pop(key, None)
        else:
            cfg._plugin_names[key] = original_names
        raise PluginError(f"Failed to load plugin: {key}")
    plugins.pop(raw_key, None)
    plugins[key] = clean
    cfg.save()
    if original_names is None:
        cfg._plugin_names.pop(key, None)
    else:
        cfg._plugin_names[key] = original_names
    _unloaded_snapshots.pop(key, None)
    return serialize_plugin(result.plugin, _force=True)


async def unload_market_plugin(market_name: str) -> str | None:
    for plug in list(plugin_service.plugins.values()):
        if _subplugin_root(plug) is not None:
            continue
        entry = await market_service.find_market_entry(plug.id, plug.path)
        if entry and entry["name"] == market_name:
            await unload_plugin(plug.id)
            return plug.id
    return None


async def uninstall_plugin(plugin_id: str) -> str:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    if plug.is_static or plug.id.startswith("$") or _subplugin_root(plug) is not None:
        raise PluginError("Only top-level non-static plugins can be uninstalled")
    entry = await market_service.find_market_entry(plug.id, plug.path)
    if entry is None:
        raise PluginError("Plugin is not installed from the marketplace")
    await unload_plugin(plug.id)
    return await market_service.start_uninstall(entry["name"])


def update_plugin_config(plugin_id: str, config: dict[str, Any]) -> None:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    # 复用 config_service 的路径解析，子插件写到父配置的 `.child` 下
    from .config_service import update_section

    update_section(f"plugins:{plugin_id}", config)
