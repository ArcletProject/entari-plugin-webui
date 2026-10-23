from __future__ import annotations

import os
import platform
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unknown"


def _cpu_name() -> str:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as file:
            for line in file:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine() or "unknown"


def get_system_info() -> dict[str, Any]:
    from .. import __version__

    return {
        "system": f"{platform.system()} {platform.release()}".strip(),
        "cpu": _cpu_name(),
        "cpu_count": os.cpu_count() or 0,
        "python": platform.python_version(),
        "entari_version": _package_version("arclet-entari"),
        "webui_version": __version__,
    }
