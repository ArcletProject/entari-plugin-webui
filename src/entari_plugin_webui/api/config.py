"""配置管理 API"""

from typing import Any
from pydantic import BaseModel
from fastapi import Request
from fastapi.responses import JSONResponse
from ruamel.yaml import CommentedMap
from arclet.entari.config import EntariConfig, config_model_schema
from arclet.entari.config.model import BasicConfig
from arclet.entari.plugin import get_plugins, find_plugin
from entari_plugin_server import add_route

from ..core.auth import require_auth


class UpdateSectionRequest(BaseModel):
    data: dict[str, Any] = {}


def register_config_routes():
    """注册配置相关路由"""
    pass  # 路由通过装饰器注册


def _serialize_config(data):
    """序列化配置数据，处理 CommentedMap 等特殊类型"""
    if isinstance(data, CommentedMap):
        return dict(data)
    if isinstance(data, dict):
        return {k: _serialize_config(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize_config(item) for item in data]
    return data


@add_route("/api/config", methods=["GET"])
@require_auth
async def get_config() -> JSONResponse:
    """
    获取完整配置
    
    Returns:
        {
            "sections": ["basic", "plugins"],
            "data": {...}
        }
    """
    
    return JSONResponse({
        "success": True,
        "sections": ["basic", "plugins", "adapters"],
        "plugin_sections": [f"plugins.{k}" for k in EntariConfig.instance.plugin.keys()],
        "data": _serialize_config(EntariConfig.instance.data)
    })


@add_route("/api/config/{section}", methods=["GET"])
@require_auth
async def get_section(section: str) -> JSONResponse:
    """
    获取指定节的配置
    
    支持嵌套路径，如 "plugins.webui"
    """
    
    def _get(*keys: str, default=None):
        value = EntariConfig.instance.data
        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        
        return value

    # 解析嵌套路径
    keys = section.split(".")
    data = _get(*keys, default={})
    
    return JSONResponse({
        "success": True,
        "section": section,
        "data": _serialize_config(data)
    })


@add_route("/api/config/{section}", methods=["PUT"])
@require_auth
async def update_section(section: str, body: UpdateSectionRequest) -> JSONResponse:
    """
    更新指定节的配置
    
    Request:
        {"data": {...}}
    """
    new_data = body.data

    try:
        # 解析嵌套路径
        keys = section.split(".")
        
        # 导航到父节点
        target = EntariConfig.instance.data
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # 设置值
        target[keys[-1]] = new_data

        return JSONResponse({
            "success": True,
            "message": "配置保存成功"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=500)


@add_route("/api/config/schema/{section}", methods=["GET"])
@require_auth
async def get_schema(section: str) -> JSONResponse:
    """
    获取指定节的表单 Schema
    
    用于前端动态渲染表单
    """
    # 预定义的 schema
    # schemas = {
    #        "basic": config_model_schema(BasicConfig, ref_root="/properties/basic/"), "plugins": {"type": "object", "description": "Plugin configurations", "properties": {"$prelude": {"type": "array", "items": {"type": "string", "description": "Plugin name"}, "description": "List of prelude plugins to load", "default": [], "uniqueItems": True}, "$files": {"type": "array", "items": {"type": "string", "description": "File path"}, "description": "List of configuration files to load", "default": [], "uniqueItems": True}, **plugins_properties}}, "adapters": {"type": "array", "description": "Adapter configurations", "items": {"type": "object", "description": "Adapter configuration", "properties": {"$path": {"type": "string", "description": "Adapter Module Path"}}, "required": ["$path"], "additionalProperties": True}}  # noqa: E501
    #    }
    if section == "basic":
        schema = config_model_schema(BasicConfig, ref_root="/properties/basic/")
    elif section == "adapters":
        schema = {
            "type": "array",
            "description": "Adapter configurations",
            "items": {
                "type": "object",
                "description": "Adapter configuration",
                "properties": {
                    "$path": {
                        "type": "string",
                        "description": "Adapter Module Path"
                    }
                },
                "required": ["$path"],
                "additionalProperties": True
            }
        }
    else:
        plugin_id = section.split(".")[1] if section.startswith("plugins.") else section
        plugin = find_plugin(plugin_id)
        if plugin is None:
            return JSONResponse({
                "success": False,
                "message": f"Plugin '{plugin_id}' not found"
            }, status_code=404)
        plugin_meta_properties = {"$disable": {"type": "string", "description": "Expression for whether disable this plugin"}, "$prefix": {"type": "string", "description": "Plugin name prefix"}, "$priority": {"type": "integer", "description": "Plugin loading priority, lower value means higher priority (default: 16)"}, "$filter": {"type": "string", "description": "Plugin filter expression, which will be evaluated in the context of the plugin"}}  # noqa: E501
        if plugin.metadata is not None:
            if plugin.metadata.config:
                schema = config_model_schema(plugin.metadata.config, ref_root=f"/properties/plugins/properties/{plugin._config_key}/")  # noqa: E501
                schema["properties"].update(plugin_meta_properties)
            else:
                schema = {"type": "object", "description": f"{plugin.metadata.description or plugin.metadata.name}; no configuration required", "additionalProperties": True, "properties": plugin_meta_properties}  # noqa: E501
        else:
            schema = {"type": "object", "description": "No configuration required", "additionalProperties": True, "properties": plugin_meta_properties}  # noqa: E501
    return JSONResponse({
        "success": True,
        "section": section,
        "schema": schema
    })
