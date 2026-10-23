from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from arclet.entari.config import config_model_schema
from arclet.entari.config.action import config_model_dump, config_model_validate
from arclet.entari.config.file import EntariConfig
from arclet.entari.config.model import ApplyReport, BasicConfig
from arclet.entari.config.schema.plugin import PLUGIN_META_PROPERTIES, plugin_config_schema
from arclet.entari.config.schema.rebase import update_schema
from arclet.entari.config.schema.registry import _schema_fragments
from arclet.entari.event.config import ConfigModify
from arclet.entari.plugin import find_plugin, get_plugins
from arclet.entari.plugin.model import Plugin
from arclet.entari.plugin.service import plugin_service
from arclet.letoderea import post
from ruamel.yaml import CommentedMap

from ..core.error import (
    AppError,
    ConfigConflict,
    ConfigPreconditionRequired,
    ConfigSectionNotFound,
)
from . import config_ops
from .plugin_service import _fragment_parts, _relative_key

_save_lock = asyncio.Lock()


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


def _get_by_path(cfg: EntariConfig, path: list[str]) -> Any:
    node: Any = cfg.plugin or {}
    for key in path:
        if not isinstance(node, dict):
            return {}
        node = node.get(key)
        if node is None:
            return {}
    return _unwrap(node)


def read_section(cfg: EntariConfig, section: str) -> Any:
    """读取任意 EntariConfig 实例上的 raw 配置（不含模型默认值）。"""
    if section == "basic":
        return _unwrap(cfg.data.get("basic", {}))
    if section == "adapters":
        return _unwrap(cfg.data.get("adapters", []))
    if section == "plugins":
        return _unwrap(cfg.plugin or {})
    if section.startswith("plugins:"):
        key = section[len("plugins:") :]
        plug = _resolve_plugin(key)
        if plug is None:
            return _unwrap((cfg.plugin or {}).get(key, {}))
        path = _plugin_config_path(plug)
        if not path:
            return _unwrap(cfg.plugin or {})
        return _get_by_path(cfg, path)
    raise ConfigSectionNotFound(message=f"Section not found: {section}")


def _extra_files(cfg: EntariConfig) -> list[Path]:
    root = Path(cfg.path).resolve().parent
    files: list[Path] = []
    for raw in cfg.plugin_extra_files or []:
        path = Path(raw)
        if not path.is_absolute():
            path = root / path
        files.append(path.resolve())
    return files


def _hash_path(digest: Any, path: Path) -> None:
    digest.update(path.as_posix().encode())
    digest.update(b"\0")
    if path.is_dir():
        children = sorted(
            child for child in path.rglob("*") if child.is_file() and not child.name.endswith(".schema.json")
        )
        for child in children:
            digest.update(child.relative_to(path).as_posix().encode())
            digest.update(b"\0")
            digest.update(child.read_bytes())
            digest.update(b"\0")
        digest.update(b"<directory>")
    else:
        try:
            digest.update(path.read_bytes())
        except FileNotFoundError:
            digest.update(b"<missing>")
    digest.update(b"\0")


def compute_etag(cfg: EntariConfig) -> str:
    digest = hashlib.sha256()
    for path in [Path(cfg.path).resolve(), *_extra_files(cfg)]:
        _hash_path(digest, path)
    return digest.hexdigest()


def get_etag() -> str:
    return compute_etag(EntariConfig.instance)


def _effective(section: str) -> Any:
    cfg = EntariConfig.instance
    if section == "basic":
        try:
            return config_model_dump(cfg.basic)
        except (AttributeError, TypeError):
            return cfg.basic if isinstance(cfg.basic, dict) else {}
    if section.startswith("plugins:"):
        key = section[len("plugins:") :]
        plug = _resolve_plugin(key)
        if plug is None or plug.metadata is None or plug.metadata.config is None:
            return {}
        raw = read_section(cfg, section)
        if not isinstance(raw, dict):
            return {}
        return config_model_dump(config_model_validate(plug.metadata.config, raw))
    return {}


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
    return read_section(EntariConfig.instance, section)


def _section_path(section: str) -> list[str]:
    if section in ("basic", "adapters", "plugins"):
        return [section]
    if section.startswith("plugins:"):
        key = section[len("plugins:") :]
        plug = _resolve_plugin(key)
        return _plugin_config_path(plug) if plug is not None else [key]
    raise ConfigSectionNotFound(message=f"Section not found: {section}")


def _ensure_mapping(node: Any) -> dict[str, Any]:
    if isinstance(node, CommentedMap):
        return node
    if isinstance(node, dict):
        return node
    raise AppError(message="Configuration node is not a mapping", code="config_invalid", status=422)


def _target_for(cfg: EntariConfig, section: str) -> tuple[Any, tuple[str, ...], Path]:
    """返回 (目标子树, 目标在所属文件中的记录前缀, 所属文件)。"""
    if section == "basic":
        return _ensure_mapping(cfg.data.setdefault("basic", {})), ("basic",), Path(cfg.path)
    if section == "adapters":
        adapters = cfg.data.setdefault("adapters", [])
        if not isinstance(adapters, list):
            raise AppError(message="adapters is not a list", code="config_invalid", status=422)
        return adapters, ("adapters",), Path(cfg.path)
    if section == "plugins":
        return _ensure_mapping(cfg.data.setdefault("plugins", {})), ("plugins",), Path(cfg.path)

    path = _section_path(section)
    if not path:
        raise ConfigSectionNotFound(message=f"Section not found: {section}")
    root = path[0]
    root_keys = getattr(cfg, "_root_plugin_keys", None)
    is_extra = isinstance(cfg.plugin, dict) and root in cfg.plugin and (root_keys is None or root not in root_keys)
    if is_extra:
        node: Any = cfg.plugin
        file_path = _extra_file_for_stem(cfg, root)
        prefix: tuple[str, ...] = ()
    else:
        node = _ensure_mapping(cfg.data.setdefault("plugins", {}))
        file_path = Path(cfg.path)
        prefix = ("plugins",)
    for key in path[:-1]:
        child = node.get(key)
        if not isinstance(child, dict):
            child = {}
            node[key] = child
        node = child
    last = path[-1]
    if not isinstance(node.get(last), dict):
        node[last] = {}
    record_prefix = tuple(path[1:]) if is_extra else (*prefix, *path)
    return node[last], record_prefix, file_path


def _extra_file_for_stem(cfg: EntariConfig, stem: str) -> Path:
    for entry in _extra_files(cfg):
        if entry.is_file() and entry.stem == stem:
            return entry
        if entry.is_dir():
            for candidate in entry.glob(f"{stem}.*"):
                if candidate.name.endswith(".schema.json"):
                    continue
                return candidate.resolve()
    return Path(cfg.path)


def _remap_records(cfg: EntariConfig, result: config_ops.DiffResult, prefix: tuple[str, ...], file_path: Path) -> None:
    mapper = config_ops.make_remapper(result)

    def record_mapper(parts: tuple[str, ...]):
        if prefix:
            if parts[: len(prefix)] != prefix:
                return parts
            mapped = mapper(parts[len(prefix) :])
            return None if mapped is None else (*prefix, *mapped)
        mapped = mapper(parts)
        return mapped

    cfg.remap_records(file_path, record_mapper)


def report_to_dict(report: ApplyReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "applied": report.applied,
        "changed_basic": list(report.changed_basic),
        "changed_plugins": list(report.changed_plugins),
        "loaded": list(report.loaded),
        "unloaded": list(report.unloaded),
        "reloaded": list(report.reloaded),
        "skipped": list(report.skipped),
        "ignored": report.ignored,
        "errors": [{"plugin": error.plugin, "message": error.message} for error in report.errors],
    }


async def _update_section(
    section: str,
    payload: Any,
    *,
    if_match: str | None,
    check_etag: bool,
    mutate: bool,
    create: bool,
    source: str,
) -> ApplyReport:
    cfg = EntariConfig.instance
    _section_path(section)  # validate before touching files

    async with _save_lock:
        current_etag = compute_etag(cfg)
        if check_etag:
            if if_match is None:
                raise ConfigPreconditionRequired(
                    message="If-Match header is required",
                    etag=current_etag,
                )
            if if_match != current_etag:
                raise ConfigConflict(
                    message="Configuration changed since it was loaded",
                    etag=current_etag,
                    data=get_section(section),
                )

        tmp = EntariConfig.load(cfg.path, detach=True)
        raw = read_section(tmp, section)
        desired = payload(_unwrap(raw)) if mutate else payload
        if desired is None:
            desired = {}
        desired = config_ops.strip_new_defaults(raw, desired, _effective(section))
        result = config_ops.diff(raw, desired)
        if not result.ops and not create:
            return ApplyReport(ok=True, applied=False)

        target, prefix, file_path = _target_for(tmp, section)
        config_ops.apply_ops(target, result.ops)
        _remap_records(tmp, result, prefix, file_path)
        tmp.save()

        res = await post(ConfigModify(tmp.path, source=source), validate=True)
        if res is None:
            raise AppError(
                message="ConfigModify has no handler; entari core may be too old",
                code="config_handler_missing",
                status=503,
            )
        return res.value


async def update_section(section: str, data: Any, *, if_match: str | None = None) -> ApplyReport:
    return await _update_section(
        section,
        data,
        if_match=if_match,
        check_etag=True,
        mutate=False,
        create=False,
        source="webui",
    )


async def mutate_section(
    section: str,
    mutate: Callable[[Any], Any],
    *,
    create: bool = False,
    source: str = "webui",
) -> ApplyReport:
    """在 detached 配置上执行内部变更，不要求 If-Match（供生命周期操作使用）。"""
    return await _update_section(
        section,
        mutate,
        if_match=None,
        check_etag=False,
        mutate=True,
        create=create,
        source=source,
    )


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
            if meta is not None and meta.config is not None:
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
