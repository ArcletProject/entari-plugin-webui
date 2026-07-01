from __future__ import annotations

import asyncio
from typing import Any

from arclet.entari.config.file import EntariConfig
from arclet.entari.plugin import (
    enable_plugin,
    find_plugin,
    get_plugin_references,
    get_plugin_referents,
    get_plugins,
    load_plugin,
    unload_plugin_async,
)


class PluginNotFound(Exception):
    pass


def _authors(meta) -> list[str]:
    out = []
    for a in meta.author or []:
        if isinstance(a, dict):
            out.append(a.get("name", str(a)))
        else:
            out.append(str(a))
    return out


def serialize_plugin(plug) -> dict[str, Any]:
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
    }


def list_plugins() -> list[dict[str, Any]]:
    return [serialize_plugin(p) for p in get_plugins()]


def get_plugin(plugin_id: str) -> dict[str, Any]:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    return serialize_plugin(plug)


def toggle_plugin(plugin_id: str, *, enable: bool) -> bool:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    plug.enable() if enable else plug.disable()
    return True


async def reload_plugin(plugin_id: str) -> bool:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    if hasattr(plug, "reload") and callable(plug.reload):  # type: ignore[attr-defined]
        result = plug.reload()  # type: ignore[attr-defined]
        if asyncio.iscoroutine(result):
            await result
        return True
    await unload_plugin_async(plugin_id)
    new = load_plugin(plugin_id)
    if new is not None:
        _ = await enable_plugin(plugin_id)
        return True
    return False


def update_plugin_config(plugin_id: str, config: dict[str, Any]) -> None:
    plug = find_plugin(plugin_id)
    if plug is None:
        raise PluginNotFound(plugin_id)
    key = getattr(plug, "_config_key", plugin_id)
    EntariConfig.instance.plugin[key] = config
    EntariConfig.instance.save()
