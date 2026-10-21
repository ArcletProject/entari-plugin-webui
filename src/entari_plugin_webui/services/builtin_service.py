from __future__ import annotations

import ast
import pkgutil
from pathlib import Path
from typing import Any

from arclet.entari.config.file import EntariConfig
from arclet.entari.plugin import find_plugin
from arclet.entari.plugin.model import Plugin

from ..core.error import MarketError

BUILTIN_PREFIX = "arclet.entari.builtins."


def _iter_builtin_modules() -> list[tuple[str, Path]]:
    import arclet.entari.builtins as pkg

    root = Path(next(iter(pkg.__path__)))
    modules: list[tuple[str, Path]] = []
    for info in pkgutil.iter_modules(pkg.__path__):
        path = root / (f"{info.name}/__init__.py" if info.ispkg else f"{info.name}.py")
        if path.is_file():
            modules.append((info.name, path))
    return sorted(modules)


def _string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_metadata(path: Path) -> tuple[str | None, str | None]:
    """从内置模块源码中静态读取 metadata(...) 的标题和描述。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None, None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name != "metadata":
            continue
        title = _string(node.args[0]) if node.args else None
        description = None
        for kw in node.keywords:
            if kw.arg == "name":
                title = _string(kw.value) or title
            elif kw.arg == "description":
                description = _string(kw.value)
        if title or description:
            return title, description
    return None, None


def list_builtins() -> list[dict[str, Any]]:
    result = []
    for name, path in _iter_builtin_modules():
        plug = find_plugin(f"{BUILTIN_PREFIX}{name}")
        title, description = _extract_metadata(path)
        if plug is not None and plug.metadata is not None:
            title = plug.metadata.name or title
            description = plug.metadata.description or description
        result.append(
            {
                "name": name,
                "id": f"{BUILTIN_PREFIX}{name}",
                "key": f"::{name}",
                "title": title or name,
                "description": description or "",
                "loaded": plug is not None,
                "enabled": bool(plug is not None and plug.is_available),
                "static": bool(plug is not None and plug.is_static),
            }
        )
    return result


def _raw_key(plugins: dict[str, Any], key: str) -> str | None:
    for raw in plugins:
        if raw.lstrip("~?") == key:
            return raw
    return None


def _clean_entry(entry: Any) -> dict[str, Any]:
    out = dict(entry) if isinstance(entry, dict) else {}
    out.pop("$disable", None)
    out.pop("$optional", None)
    return out


def _find_builtin(name: str) -> Plugin | None:
    return find_plugin(f"{BUILTIN_PREFIX}{name}")


def _errors(report: Any) -> str:
    return "; ".join(f"{error.plugin}: {error.message}" for error in report.errors if error.message)


async def set_builtin_enabled(name: str, enable: bool) -> None:
    if name not in {mod_name for mod_name, _ in _iter_builtin_modules()}:
        raise MarketError(f"Unknown builtin plugin: {name}")

    key = f"::{name}"
    plug = _find_builtin(name)

    if not enable and plug is not None and plug.is_static:
        raise MarketError(f"Builtin plugin {name} is static and cannot be disabled")

    def mutate(entry: dict[str, Any]) -> dict[str, Any]:
        entry = _clean_entry(entry)
        if not enable:
            entry["$disable"] = True
        return entry

    from .config_service import mutate_section

    report = await mutate_section(f"plugins:{key}", mutate, create=True)
    if not report.ok:
        verb = "load" if enable else "disable"
        raise MarketError(f"Failed to {verb} builtin plugin {name}: {_errors(report)}")


async def set_builtin_unloaded(name: str) -> None:
    if name not in {mod_name for mod_name, _ in _iter_builtin_modules()}:
        raise MarketError(f"Unknown builtin plugin: {name}")

    key = f"::{name}"
    plug = _find_builtin(name)
    if plug is not None and plug.is_static:
        raise MarketError(f"Builtin plugin {name} is static and cannot be unloaded")

    def mutate(entry: dict[str, Any]) -> dict[str, Any]:
        entry = _clean_entry(entry)
        entry["$optional"] = True
        return entry

    from .config_service import mutate_section

    report = await mutate_section(f"plugins:{key}", mutate, create=True)
    if not report.ok:
        raise MarketError(f"Failed to unload builtin plugin {name}: {_errors(report)}")


async def load_builtin(name: str) -> bool:
    if name not in {mod_name for mod_name, _ in _iter_builtin_modules()}:
        raise MarketError(f"Unknown builtin plugin: {name}")

    key = f"::{name}"

    def mutate(entry: dict[str, Any]) -> dict[str, Any]:
        return _clean_entry(entry)

    from .config_service import mutate_section

    report = await mutate_section(f"plugins:{key}", mutate, create=True)
    if not report.ok:
        raise MarketError(f"Failed to load builtin plugin {name}: {_errors(report)}")
    return _find_builtin(name) is not None
