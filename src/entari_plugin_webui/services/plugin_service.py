from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from arclet.entari.config.file import EntariConfig
from arclet.entari.plugin import (
    disable_plugin,
    enable_plugin,
    find_plugin,
    get_plugin_references,
    get_plugin_referents,
    get_plugins,
    load_plugin,
    unload_plugin_async,
)
from arclet.entari.plugin.model import Plugin, PluginMetadata, RootlessPlugin

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


def serialize_plugin(plug: Plugin) -> dict[str, Any]:
    meta = plug.metadata
    configurable = bool(meta and getattr(meta, "config", None))
    type = "common"
    if isinstance(plug, RootlessPlugin):
        type = "rootless"
    elif plug.id.startswith("arclet.entari"):
        type = "built-in"
    elif is_project_module(plug.module):
        type = "local"
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
    }


def list_plugins() -> list[dict[str, Any]]:
    return [serialize_plugin(p) for p in get_plugins()]


def get_plugin(plugin_id: str) -> dict[str, Any]:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    return serialize_plugin(plug)


async def toggle_plugin(plugin_id: str, *, enable: bool) -> bool:
    return await (enable_plugin(plugin_id) if enable else disable_plugin(plugin_id))


async def reload_plugin(plugin_id: str) -> bool:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    pid = plug.id
    _conf = plug.config.copy()
    del plug
    await unload_plugin_async(pid)
    new = load_plugin(pid, _conf)
    if new is not None:
        del new
        return True
    return False


def update_plugin_config(plugin_id: str, config: dict[str, Any]) -> None:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    key = getattr(plug, "_config_key", plugin_id)
    EntariConfig.instance.plugin[key] = config
    EntariConfig.instance.save()
