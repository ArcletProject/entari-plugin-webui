from __future__ import annotations

import asyncio
from typing import Any

from arclet.entari.config.file import EntariConfig
from arclet.entari.plugin import (
    enable_plugin,
    disable_plugin,
    find_plugin,
    get_plugin_references,
    get_plugin_referents,
    get_plugins,
    load_plugin,
    unload_plugin_async,
)
from arclet.entari.plugin.model import Plugin, PluginMetadata


class PluginNotFound(Exception):
    pass


def _authors(meta: PluginMetadata) -> list[str]:
    out = []
    for a in meta.author or []:
        if isinstance(a, dict):
            out.append(a.get("name", str(a)))
        else:
            out.append(str(a))
    return out


def serialize_plugin(plug: Plugin) -> dict[str, Any]:
    meta = plug.metadata
    configurable = bool(meta and getattr(meta, "config", None))
    return {
        "id": plug.id,
        "uid": plug.uid,
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
