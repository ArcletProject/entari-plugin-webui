from __future__ import annotations

from typing import Any, TypedDict

from arclet.entari.config import config_model_schema
from arclet.entari.config.file import EntariConfig
from arclet.entari.config.model import BasicConfig
from arclet.entari.config.schema.plugin import PLUGIN_META_PROPERTIES, plugin_config_schema
from arclet.entari.config.schema.rebase import update_schema
from arclet.entari.config.schema.registry import _schema_fragments
from arclet.entari.plugin import find_plugin, get_plugins
from arclet.entari.plugin.model import Plugin
from arclet.entari.plugin.service import plugin_service
from ruamel.yaml import CommentedMap
from tarina.tools import nest_dict_update, nest_list_update

from ..core.error import ConfigSectionNotFound
from .plugin_service import _fragment_parts, _relative_key


def _unwrap(obj: Any) -> Any:
    if isinstance(obj, CommentedMap):
        return dict(obj)
    if isinstance(obj, dict):
        return {k: _unwrap(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_unwrap(item) for item in obj]
    return obj


class Sections(TypedDict):
    sections: list[str]
    plugin_sections: dict[str, str]
    data: dict[str, Any]


def _resolve_plugin(key: str) -> Plugin | None:
    """按插件 id 查找；找不到时按配置键回退（兼容旧的 section 链接）"""
    if (plug := find_plugin(key)) is not None:
        return plug
    for candidate in get_plugins(subplugged=True):
        if candidate._config_key != key:
            continue
        # 子插件的 _config_key 与父插件相同，不能用配置键反查
        if candidate.id.startswith("$") or candidate.id not in plugin_service._subplugined:
            return candidate
    return None


def _plugin_config_path(plug: Plugin) -> list[str]:
    """插件配置在 ``plugins`` 映射中的键路径"""
    if plug.id == "$":
        return []
    if plug.id.startswith("$"):
        segments = [segment for segment in plug.id[1:].split(".") if segment]
        return [f".{segment}" for segment in segments]
    root_id = plugin_service._subplugined.get(plug.id)
    if not root_id:
        return [plug._config_key]
    root = plugin_service.plugins.get(root_id)
    root_key = root._config_key if root is not None else root_id
    relative = plug.id[len(root_id) :]
    segments = [segment for segment in relative.split(".") if segment]
    return [root_key, *(f".{segment}" for segment in segments)]


def get_plugin_config_path(plugin_id: str) -> list[str] | None:
    plug = _resolve_plugin(plugin_id)
    return _plugin_config_path(plug) if plug is not None else None


def _get_by_path(path: list[str]) -> Any:
    node: Any = EntariConfig.instance.plugin or {}
    for key in path:
        if not isinstance(node, dict):
            return {}
        node = node.get(key)
        if node is None:
            return {}
    return _unwrap(node)


def _update_by_path(path: list[str], data: Any) -> None:
    node = EntariConfig.instance.data.setdefault("plugins", {})
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
    nest_dict_update(target, data)


def list_sections() -> dict[str, Any]:
    cfg = EntariConfig.instance
    data = _unwrap(cfg.data)
    plugs = [plug for plug in get_plugins(subplugged=True) if plug.id != "$"]
    plugin_sections = {f"plugins:{plug.id}": plug.id for plug in plugs}
    # 兼容以配置键命名的旧 section；子插件的配置键与父插件重复，不参与
    for plug in plugs:
        if plug.id.startswith("$") or plug.id not in plugin_service._subplugined:
            plugin_sections.setdefault(f"plugins:{plug._config_key}", plug.id)
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
    if section.startswith("plugins:"):
        key = section[len("plugins:") :]
        plug = _resolve_plugin(key)
        if plug is None:
            return _unwrap((cfg.plugin or {}).get(key, {}))
        path = _plugin_config_path(plug)
        if not path:
            return _unwrap(cfg.plugin or {})
        return _get_by_path(path)
    raise ConfigSectionNotFound(message=f"Section not found: {section}")


def update_section(section: str, data: Any) -> None:
    cfg = EntariConfig.instance
    if section == "basic":
        nest_dict_update(cfg.data["basic"], data)
    elif section == "adapters":
        nest_list_update(cfg.data["adapters"], data)
    elif section == "plugins":
        nest_dict_update(cfg.data["plugins"], data)
    elif section.startswith("plugins:"):
        key = section[len("plugins:") :]
        plug = _resolve_plugin(key)
        path = _plugin_config_path(plug) if plug is not None else [key]
        if not path:
            raise ConfigSectionNotFound(message=f"Section not found: {section}")
        _update_by_path(path, data)
    else:
        raise ConfigSectionNotFound(message=f"Section not found: {section}")
    cfg.save()


ADAPTER_SCHEMA = {
    "type": "array",
    "description": "Adapter configurations",
    "items": {
        "type": "object",
        "description": "Adapter configuration",
        "properties": {"$path": {"type": "string", "description": "Adapter Module Path"}},
        "required": ["$path"],
        "additionalProperties": True,
    },
}

PLUGINS_SCHEMA = {
    "type": "object",
    "description": "Plugin configurations",
    "properties": {
        "$prefix": {
            "description": "List of prefix config",
            "items": {
                "properties": {
                    "key": {"description": "Prefix key", "title": "Key", "type": "string"},
                    "plugins": {
                        "anyOf": [
                            {"type": "string"},
                            {
                                "type": "array",
                                "items": {"type": "string", "description": "Plugin name"},
                                "uniqueItems": True,
                            },
                        ],
                        "description": "List of plugins under the prefix, or select an item of $files to apply plugins",
                        "title": "Plugins",
                    },
                },
                "required": ["key"],
                "title": "Prefix Config",
                "type": "object",
            },
            "type": "array",
        },
        "$prelude": {
            "type": "array",
            "items": {"type": "string", "description": "Plugin name"},
            "description": "List of prelude plugins to load",
            "default": [],
            "uniqueItems": True,
        },
        "$files": {
            "type": "array",
            "items": {"type": "string", "description": "File path"},
            "description": "List of configuration files to load",
            "default": [],
            "uniqueItems": True,
        },
    },
}


def get_schema_for_section(section: str) -> dict[str, Any]:
    if section == "basic":
        schema = config_model_schema(BasicConfig, ref_root="/")
    elif section == "adapters":
        schema = ADAPTER_SCHEMA
    elif section == "plugins":
        schema = PLUGINS_SCHEMA
    elif section.startswith("plugins:"):
        key = section[len("plugins:") :]
        plug = _resolve_plugin(key)
        if plug is None:
            raise ConfigSectionNotFound(message=f"Plugin not found: {key}")
        relative = _relative_key(plug)
        if relative is None or plug.id.startswith("$"):
            schema = plugin_config_schema(plug, ref_root="/")
        else:
            meta = plug.metadata
            if meta is not None and getattr(meta, "config", None):
                schema = config_model_schema(meta.config, ref_root="/")
            else:
                schema = {
                    "type": "object",
                    "description": "No configuration required",
                    "additionalProperties": True,
                }
            schema.setdefault("properties", {})
            for name, prop in PLUGIN_META_PROPERTIES.items():
                schema["properties"].setdefault(name, dict(prop))
            for record in _schema_fragments.get(plug._config_key, []):
                parts = _fragment_parts(record.path, relative)
                if parts is None:
                    continue
                update_schema(schema, plug._config_key, "/", parts, record.fragment, record.replace)
    else:
        raise ConfigSectionNotFound(message=f"Section not found: {section}")
    return {"schema": schema}
