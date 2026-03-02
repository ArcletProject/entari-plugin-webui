"""认证相关 API"""

from typing import Optional
from pydantic import BaseModel
from fastapi import Request
from fastapi.responses import JSONResponse

from entari_plugin_server import add_route

from ..core.auth import (
    create_tokens,
    verify_token,
    verify_password,
    hash_password,
    require_auth,
    generate_random_password,
)
from ..core.security import is_local_deployment
from ..config import webui_config


class LoginRequest(BaseModel):
    password: str = ""


class RefreshTokenRequest(BaseModel):
    refresh_token: str = ""


class ChangePasswordRequest(BaseModel):
    old_password: str = ""
    new_password: str = ""


def register_auth_routes():
    """注册认证相关路由"""
    pass  # 路由通过装饰器注册


@add_route("/api/auth/check", methods=["GET"])
async def check_auth_mode(request: Request) -> JSONResponse:
    """
    检查认证模式
    
    Returns:
        {
            "local_mode": true/false,  # 是否本地模式（无需认证）
            "initialized": true/false  # 是否已初始化管理员密码
        }
    """
    from entari_plugin_server import server
    
    # 检查请求来源是否为本地
    client_host = request.client.host if request.client else None
    local_mode = is_local_deployment(server.host) and (
        client_host in ("127.0.0.1", "localhost", "::1", None)
    )
    
    # 检查是否已初始化密码
    initialized = bool(webui_config.password)
    
    return JSONResponse({
        "success": True,
        "local_mode": local_mode,
        "initialized": initialized
    })


@add_route("/api/auth/login", methods=["POST"])
async def login(request: Request, body: LoginRequest) -> JSONResponse:
    """
    登录接口
    
    Request:
        {"password": "xxx"}
    
    Returns:
        {
            "success": true,
            "access_token": "...",
            "refresh_token": "...",
            "expires_in": 900
        }
    """
    from entari_plugin_server import server
    
    # 检查是否本地访问
    client_host = request.client.host if request.client else None
    is_local = is_local_deployment(server.host) and (
        client_host in ("127.0.0.1", "localhost", "::1", None)
    )
    
    # 本地模式直接返回 token
    if is_local:
        tokens = create_tokens()
        return JSONResponse({
            "success": True,
            **tokens
        })
    
    # 验证密码
    password = body.password
    
    if not password:
        return JSONResponse({
            "success": False,
            "message": "请输入密码"
        }, status_code=400)
    
    # 获取存储的密码哈希
    stored_hash = webui_config.password
    
    if not stored_hash:
        return JSONResponse({
            "success": False,
            "message": "管理员密码未初始化"
        }, status_code=500)
    
    if not verify_password(password, stored_hash):
        return JSONResponse({
            "success": False,
            "message": "密码错误"
        }, status_code=401)
    
    # 生成 token
    tokens = create_tokens()
    return JSONResponse({
        "success": True,
        **tokens
    })


@add_route("/api/auth/refresh", methods=["POST"])
async def refresh_token(body: RefreshTokenRequest) -> JSONResponse:
    """
    刷新访问令牌
    
    Request:
        {"refresh_token": "xxx"}
    
    Returns:
        {
            "success": true,
            "access_token": "...",
            "refresh_token": "...",
            "expires_in": 900
        }
    """
    refresh = body.refresh_token
    
    if not refresh:
        return JSONResponse({
            "success": False,
            "message": "未提供刷新令牌"
        }, status_code=400)
    
    # 验证 refresh token
    payload = verify_token(refresh, "refresh")
    if payload is None:
        return JSONResponse({
            "success": False,
            "message": "刷新令牌无效或已过期"
        }, status_code=401)
    
    # 生成新 token
    tokens = create_tokens()
    return JSONResponse({
        "success": True,
        **tokens
    })


@add_route("/api/auth/password", methods=["PUT"])
@require_auth
async def change_password(body: ChangePasswordRequest) -> JSONResponse:
    """
    修改管理员密码
    
    Request:
        {"old_password": "xxx", "new_password": "xxx"}
    """
    from entari_plugin_server import server
    
    old_password = body.old_password
    new_password = body.new_password
    
    if not new_password:
        return JSONResponse({
            "success": False,
            "message": "新密码不能为空"
        }, status_code=400)
    
    if len(new_password) < 6:
        return JSONResponse({
            "success": False,
            "message": "密码长度至少 6 位"
        }, status_code=400)
    
    
    # 非本地模式需要验证旧密码
    if not is_local_deployment(server.host):
        stored_hash = webui_config.password
        
        if stored_hash and not verify_password(old_password, stored_hash):
            return JSONResponse({
                "success": False,
                "message": "原密码错误"
            }, status_code=401)
    
    # 更新密码
    new_hash = hash_password(new_password)
    
    webui_config.password = new_hash
    # config_manager.save_config()
    
    if webui_config.password != new_hash:
        return JSONResponse({
            "success": False,
            "message": "配置写入失败"
        }, status_code=500)

    return JSONResponse({
        "success": True,
        "message": "密码修改成功"
    })


@add_route("/api/auth/logout", methods=["POST"])
async def logout() -> JSONResponse:
    """登出（前端清除 token 即可）"""
    return JSONResponse({"success": True})
