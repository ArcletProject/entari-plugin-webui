from __future__ import annotations

import asyncio
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

PM_INSTALL_CMD: dict[str, str] = {
    "uv": "add",
    "pdm": "add",
    "poetry": "add",
    "rye": "add",
    "pip": "install",
    "pipenv": "install",
}
PM_UNINSTALL_CMD: dict[str, str] = {
    "uv": "remove",
    "pdm": "remove",
    "poetry": "remove",
    "rye": "remove",
    "pip": "uninstall",
    "pipenv": "uninstall",
}
PM_LOCK_FILES: dict[str, str] = {
    "uv.lock": "uv",
    "pdm.lock": "pdm",
    "poetry.lock": "poetry",
    "requirements.lock": "rye",
    "Pipfile.lock": "pipenv",
    "requirements.txt": "pip",
}
PM_ORDER = ("uv", "pdm", "poetry", "rye", "pipenv")


@dataclass
class PackageManager:
    name: str
    executable: str

    def list_args(self) -> list[str]:
        if self.name == "pip":
            return [self.executable, "-m", "pip", "list", "--format=json"]
        if self.name == "uv":
            return [self.executable, "pip", "list", "--format=json"]
        if self.name == "pdm":
            return [self.executable, "list", "--json"]
        if self.name == "poetry":
            return [self.executable, "show", "--format=json"]
        if self.name == "rye":
            return [self.executable, "pip", "list", "--format=json"]
        if self.name == "pipenv":
            return [self.executable, "run", "python", "-m", "pip", "list", "--format=json"]
        raise ValueError(f"unknown package manager: {self.name}")

    def install_args(self, pip_name: str) -> list[str]:
        if self.name == "pip":
            return [self.executable, "-m", "pip", "install", "-U", pip_name]
        return [self.executable, PM_INSTALL_CMD[self.name], pip_name]

    def uninstall_args(self, pip_name: str) -> list[str]:
        if self.name == "pip":
            return [self.executable, "-m", "pip", "uninstall", "-y", pip_name]
        return [self.executable, PM_UNINSTALL_CMD[self.name], pip_name]


def _project_root(cwd: Path | None = None) -> Path:
    base = Path(cwd or Path.cwd())
    for parent in [base, *base.parents]:
        if (parent / "pyproject.toml").exists() or (parent / "setup.py").exists():
            return parent
    return base


def detect_package_manager(cwd: Path | None = None) -> PackageManager:
    root = _project_root(cwd)
    for lock, name in PM_LOCK_FILES.items():
        if (root / lock).exists():
            exe = shutil.which(name)
            if exe:
                return PackageManager(name=name, executable=exe)
    for name in PM_ORDER:
        exe = shutil.which(name)
        if exe:
            return PackageManager(name=name, executable=exe)
    return PackageManager(name="pip", executable=sys.executable)


async def list_installed(pm_: PackageManager) -> set[str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *pm_.list_args(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        items = json.loads(out.decode("utf-8", errors="replace"))
        return {item["name"].lower() for item in items}
    except Exception:  # noqa: BLE001
        return set()


async def run_action(pm_: PackageManager, action: str, pip_name: str) -> tuple[int, str]:
    if action == "install":
        args = pm_.install_args(pip_name)
    elif action == "uninstall":
        args = pm_.uninstall_args(pip_name)
    else:
        raise ValueError(f"unknown action: {action}")
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await proc.communicate()
    return proc.returncode or 0, out.decode("utf-8", errors="replace")
