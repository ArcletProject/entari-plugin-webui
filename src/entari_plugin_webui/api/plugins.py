"""插件管理 API"""

import sys
import json
import asyncio
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any

from pydantic import BaseModel
from arclet.entari.config import EntariConfig
from fastapi.responses import JSONResponse

from entari_plugin_server import add_route
from arclet.entari.plugin import (
    PluginMetadata,
    get_plugins,
    find_plugin,
    get_plugin_references,
    get_plugin_referents,
)

from ..core.auth import require_auth


class TogglePluginRequest(BaseModel):
    enable: bool = True


class UpdatePluginConfigRequest(BaseModel):
    config: dict[str, Any] = {}


class InstallPluginRequest(BaseModel):
    name: str = ""


# 插件市场元数据文件
PLUGINS_JSON = Path(__file__).parent.parent / "static" / "plugins.json"


def register_plugin_routes():
    """注册插件相关路由"""
    pass  # 路由通过装饰器注册


def _normalize_authors(raw_authors) -> list[dict[str, str]]:
    """标准化作者信息为 [{name, email}] 列表。"""
    if not raw_authors:
        return []

    if not isinstance(raw_authors, list):
        raw_authors = [raw_authors]

    result: list[dict[str, str]] = []
    for item in raw_authors:
        if isinstance(item, str):
            result.append({"name": item, "email": ""})
        elif isinstance(item, dict):
            result.append({
                "name": str(item.get("name", "")),
                "email": str(item.get("email", "")),
            })
        else:
            result.append({"name": str(item), "email": ""})
    return result


def _authors_to_text(authors: list[dict[str, str]]) -> str:
    if not authors:
        return "unknown"
    values = []
    for author in authors:
        name = author.get("name", "")
        email = author.get("email", "")
        if name and email:
            values.append(f"{name} <{email}>")
        else:
            values.append(name or email or "unknown")
    return "; ".join(values)


def _serialize_metadata(meta: PluginMetadata) -> dict:
    return {
        "name": meta.name,
        "author": meta.author,
        "version": meta.version,
        "license": meta.license,
        "urls": meta.urls if isinstance(meta.urls, dict) else {},
        "description": meta.description,
        "icon": meta.icon,
        "readme": meta.readme,
        "classifier": meta.classifier if isinstance(meta.classifier, list) else [],
        "requirements": meta.requirements if isinstance(meta.requirements, list) else [],
    }


def _serialize_plugin(plugin) -> dict:
    """序列化插件对象（含 metadata、references、referents）。"""
    meta = plugin.metadata
    authors = _normalize_authors(getattr(meta, "author", None) if meta else None)

    config = plugin.config if isinstance(plugin.config, dict) else {}
    references = sorted(list(get_plugin_references(plugin)))
    referents = sorted(list(get_plugin_referents(plugin)))

    return {
        "id": plugin.id,
        "uid": plugin.uid,
        "name": meta.name if meta else plugin.id,
        "description": meta.description if meta else "",
        "version": meta.version if meta else None,
        "license": meta.license if meta else None,
        "author": _authors_to_text(authors),
        "authors": authors,
        "enabled": plugin.is_available,
        "available": plugin.available,
        "reusable": plugin.reusable,
        "is_static": plugin.is_static,
        "subplugins": sorted(list(plugin.subplugins)),
        "path": plugin.path,
        "configurable": bool(config),
        "config": config,
        "meta": _serialize_metadata(plugin.metadata) if meta else None,
        "references": references,
        "referents": referents,
        **plugin._extra,
    }


@add_route("/api/plugins", methods=["GET"])
@require_auth
async def list_plugins() -> JSONResponse:
    """
    获取已加载的插件列表
    
    Returns:
        [
            {
                "id": "plugin-id",
                "name": "插件名称",
                "description": "插件描述",
                "version": "0.1.0",
                "author": "作者",
                "enabled": true,
                "configurable": true,
                "config": {...}
            }
        ]
    """
    plugins = get_plugins()
    result = [_serialize_plugin(plugin) for plugin in plugins]
    return JSONResponse(result)


@add_route("/api/plugins/{plugin_id}", methods=["GET"])
@require_auth
async def get_plugin_detail(plugin_id: str) -> JSONResponse:
    """获取插件详情（含 metadata / 引用关系 / 配置模型）。"""
    plugin = find_plugin(plugin_id)
    if plugin is None:
        return JSONResponse({
            "success": False,
            "message": f"插件 {plugin_id} 不存在",
        }, status_code=404)

    return JSONResponse({
        "success": True,
        "data": _serialize_plugin(plugin),
    })


@add_route("/api/plugins/{plugin_id}/toggle", methods=["POST"])
@require_auth
async def toggle_plugin(plugin_id: str, body: TogglePluginRequest) -> JSONResponse:
    """
    启用/禁用插件
    
    Request:
        {"enable": true/false}
    """
    enable = body.enable
    
    plugin = find_plugin(plugin_id)
    if plugin is None:
        return JSONResponse({
            "success": False,
            "message": f"插件 {plugin_id} 不存在"
        }, status_code=404)
    
    try:
        if enable:
            plugin.enable()
        else:
            plugin.disable()
        
        return JSONResponse({
            "success": True,
            "enabled": plugin.is_available
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


@add_route("/api/plugins/{plugin_id}/reload", methods=["POST"])
@require_auth
async def reload_plugin(plugin_id: str) -> JSONResponse:
    """
    重载插件
    """
    plugin = find_plugin(plugin_id)
    if plugin is None:
        return JSONResponse({
            "success": False,
            "message": f"插件 {plugin_id} 不存在"
        }, status_code=404)
    
    try:
        # 尝试重载
        reloader = getattr(plugin, "reload", None)
        if callable(reloader):
            result = reloader()
            if asyncio.iscoroutine(result):
                await result
        else:
            # 简单的禁用再启用
            plugin.disable()
            plugin.enable()
        
        return JSONResponse({
            "success": True,
            "message": "插件重载成功"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


@add_route("/api/plugins/{plugin_id}/config", methods=["PUT"])
@require_auth
async def update_plugin_config(plugin_id: str, body: UpdatePluginConfigRequest) -> JSONResponse:
    """
    更新插件配置
    
    同时更新运行时配置和持久化到 entari.yml
    
    Request:
        {"config": {...}}
    """
    new_config = body.config
    
    plugin = find_plugin(plugin_id)
    if plugin is None:
        return JSONResponse({
            "success": False,
            "message": f"插件 {plugin_id} 不存在"
        }, status_code=404)
    
    try:
        # 更新运行时配置
        # 持久化到 entari.yml
        EntariConfig.plugin[plugin._config_key].update(new_config)
        EntariConfig.instance.save()

        return JSONResponse({
            "success": True,
            "message": "配置保存成功"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


# ---------- 插件市场 ----------

@add_route("/api/market/plugins", methods=["GET"])
@require_auth
async def list_market_plugins() -> JSONResponse:
    """
    获取插件市场列表
    """
    if not PLUGINS_JSON.exists():
        return JSONResponse([])
    
    with open(PLUGINS_JSON, 'r', encoding='utf-8') as f:
        plugins = json.load(f)
    
    # 检查安装状态
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        installed = {pkg["name"] for pkg in json.loads(result.stdout)}
    except Exception:
        installed = set()
    
    for plugin in plugins:
        plugin["installed"] = plugin.get("name", "") in installed
    
    return JSONResponse(plugins)


@add_route("/api/market/plugins/{name}", methods=["GET"])
@require_auth
async def get_market_plugin(name: str) -> JSONResponse:
    """
    获取插件市场详情
    """
    if not PLUGINS_JSON.exists():
        return JSONResponse({"error": "插件不存在"}, status_code=404)
    
    with open(PLUGINS_JSON, 'r', encoding='utf-8') as f:
        plugins = json.load(f)
    
    plugin = next((p for p in plugins if p.get("name") == name), None)
    if not plugin:
        return JSONResponse({"error": "插件不存在"}, status_code=404)
    
    # 检查安装状态
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True
        )
        installed = {pkg["name"] for pkg in json.loads(result.stdout)}
        plugin["installed"] = plugin.get("name", "") in installed
    except Exception:
        plugin["installed"] = False
    
    return JSONResponse(plugin)


# ---------- 异步安装/卸载任务 ----------

@dataclass
class InstallTask:
    task_id: str
    plugin_name: str
    status: str = "pending"  # pending, running, success, failed
    percent: int = 0
    message: str = ""


_install_tasks: dict[str, InstallTask] = {}


async def _pip_install(task: InstallTask):
    """异步 pip 安装"""
    task.status = "running"
    task.percent = 10
    
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", "-U", task.plugin_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        task.percent = 50
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            task.status = "success"
            task.percent = 100
            task.message = "安装成功"
        else:
            task.status = "failed"
            task.percent = 0
            task.message = stderr.decode() or "安装失败"
    except Exception as e:
        task.status = "failed"
        task.percent = 0
        task.message = str(e)


async def _pip_uninstall(task: InstallTask):
    """异步 pip 卸载"""
    task.status = "running"
    task.percent = 10
    
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "uninstall", "-y", task.plugin_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        task.percent = 50
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            task.status = "success"
            task.percent = 100
            task.message = "卸载成功"
        else:
            task.status = "failed"
            task.percent = 0
            task.message = stderr.decode() or "卸载失败"
    except Exception as e:
        task.status = "failed"
        task.percent = 0
        task.message = str(e)


@add_route("/api/plugins/install", methods=["POST"])
@require_auth
async def install_plugin(body: InstallPluginRequest) -> JSONResponse:
    """
    安装插件
    
    Request:
        {"name": "package-name"}
    
    Returns:
        {"success": true, "task_id": "xxx"}
    """
    plugin_name = body.name
    
    if not plugin_name:
        return JSONResponse({
            "success": False,
            "message": "未指定插件名称"
        }, status_code=400)
    
    task_id = str(uuid.uuid4())
    task = InstallTask(task_id=task_id, plugin_name=plugin_name)
    _install_tasks[task_id] = task
    
    asyncio.create_task(_pip_install(task))
    
    return JSONResponse({
        "success": True,
        "task_id": task_id
    })


@add_route("/api/plugins/uninstall", methods=["POST"])
@require_auth
async def uninstall_plugin(body: InstallPluginRequest) -> JSONResponse:
    """
    卸载插件
    
    Request:
        {"name": "package-name"}
    """
    plugin_name = body.name
    
    if not plugin_name:
        return JSONResponse({
            "success": False,
            "message": "未指定插件名称"
        }, status_code=400)
    
    task_id = str(uuid.uuid4())
    task = InstallTask(task_id=task_id, plugin_name=plugin_name)
    _install_tasks[task_id] = task
    
    asyncio.create_task(_pip_uninstall(task))
    
    return JSONResponse({
        "success": True,
        "task_id": task_id
    })


@add_route("/api/plugins/task/{task_id}", methods=["GET"])
@require_auth
async def get_task_status(task_id: str) -> JSONResponse:
    """获取安装/卸载任务状态"""
    task = _install_tasks.get(task_id)
    
    if not task:
        return JSONResponse({
            "success": False,
            "message": "任务不存在"
        }, status_code=404)
    
    return JSONResponse({
        "success": True,
        "task_id": task.task_id,
        "plugin_name": task.plugin_name,
        "status": task.status,
        "percent": task.percent,
        "message": task.message
    })
