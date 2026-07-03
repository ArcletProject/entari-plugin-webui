from __future__ import annotations

from typing import Any, TypedDict

from arclet.entari.config import config_model_schema
from arclet.entari.config.file import EntariConfig
from arclet.entari.config.model import BasicConfig
from arclet.entari.plugin import find_plugin, get_plugins
from ruamel.yaml import CommentedMap
from tarina.tools import nest_dict_update, nest_list_update

from ..core.error import ConfigSectionNotFound


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


def list_sections() -> dict[str, Any]:
    cfg = EntariConfig.instance
    data = _unwrap(cfg.data)
    plugin_sections = {f"plugins:{plg._config_key}": plg.id for plg in get_plugins()}
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
        plugin_keys = {plg.id: plg._config_key for plg in get_plugins()}
        config_key = plugin_keys.get(key, key)
        return _unwrap((cfg.plugin or {}).get(config_key, {}))
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
        plugin_keys = {plg.id: plg._config_key for plg in get_plugins()}
        config_key = plugin_keys.get(key, key)
        target = cfg.data.setdefault("plugins", {}).setdefault(config_key, {})
        nest_dict_update(target, data)
    else:
        raise ConfigSectionNotFound(message=f"Section not found: {section}")
    cfg.save()


PLUGIN_META_PROPERTIES = {
    "$disable": {"type": "string", "description": "Expression for whether disable this plugin"},
    "$priority": {
        "type": "integer",
        "description": "Plugin loading priority, lower value means higher priority (default: 16)",
    },
    "$filter": {
        "type": "string",
        "description": "Plugin filter expression, which will be evaluated in the context of the plugin",
    },
    "$optional": {"type": "boolean", "description": "Whether this plugin is optional"},
}

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
        plugin_sections = {f"plugins:{plg._config_key}": plg.id for plg in get_plugins()}
        plugin_id = plugin_sections.get(section, section[len("plugins:") :])
        plug = find_plugin(plugin_id)
        if not plug:
            raise ConfigSectionNotFound(message=f"Plugin not found: {plugin_id}")
        if plug.metadata and plug.metadata.config:
            schema = config_model_schema(plug.metadata.config, ref_root="/")
            schema["properties"].update(PLUGIN_META_PROPERTIES)
        elif plug.metadata is not None:
            schema = {
                "type": "object",
                "description": f"{plug.metadata.description or plug.metadata.name}; no configuration required",
                "additionalProperties": True,
                "properties": PLUGIN_META_PROPERTIES,
            }
        else:
            schema = {
                "type": "object",
                "description": "No configuration required",
                "additionalProperties": True,
                "properties": PLUGIN_META_PROPERTIES,
            }
    else:
        raise ConfigSectionNotFound(message=f"Section not found: {section}")
    return {"schema": schema}
