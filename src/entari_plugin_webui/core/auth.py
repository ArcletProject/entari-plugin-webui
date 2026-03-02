"""认证模块 - JWT + bcrypt 实现"""

import secrets
import hashlib
import hmac
import base64
import json
import time
from functools import wraps
from typing import Optional, Callable, Any
from dataclasses import dataclass

from starlette.responses import JSONResponse
from fastapi import Request

from .security import is_local_deployment


# ---------- 配置 ----------
ACCESS_TOKEN_EXPIRE = 15 * 60  # 15 分钟
REFRESH_TOKEN_EXPIRE = 7 * 24 * 60 * 60  # 7 天
JWT_SECRET: Optional[str] = None  # 运行时生成


def _get_jwt_secret() -> str:
    """获取或生成 JWT 密钥"""
    global JWT_SECRET
    if JWT_SECRET is None:
        JWT_SECRET = secrets.token_urlsafe(32)
    return JWT_SECRET


# ---------- 密码哈希 (使用 PBKDF2 替代 bcrypt 以减少依赖) ----------
def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    """
    使用 PBKDF2-SHA256 哈希密码
    返回格式: salt$hash (base64 编码)
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    
    salt_b64 = base64.b64encode(salt).decode()
    hash_b64 = base64.b64encode(dk).decode()
    
    return f"{salt_b64}${hash_b64}"


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt_b64, hash_b64 = hashed.split('$')
        salt = base64.b64decode(salt_b64)
        expected_hash = base64.b64decode(hash_b64)
        
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        
        return hmac.compare_digest(dk, expected_hash)
    except Exception:
        return False


# ---------- JWT 实现 ----------
@dataclass
class TokenPayload:
    """Token 载荷"""
    type: str  # "access" or "refresh"
    exp: int   # 过期时间戳
    iat: int   # 签发时间戳


def _base64url_encode(data: bytes) -> str:
    """Base64URL 编码"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _base64url_decode(data: str) -> bytes:
    """Base64URL 解码"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def create_tokens() -> dict[str, str]:
    """
    创建访问令牌和刷新令牌
    
    Returns:
        {"access_token": "...", "refresh_token": "...", "expires_in": 900}
    """
    now = int(time.time())
    secret = _get_jwt_secret()
    
    # Access Token
    access_payload = {
        "type": "access",
        "exp": now + ACCESS_TOKEN_EXPIRE,
        "iat": now
    }
    access_token = _create_jwt(access_payload, secret)
    
    # Refresh Token
    refresh_payload = {
        "type": "refresh",
        "exp": now + REFRESH_TOKEN_EXPIRE,
        "iat": now
    }
    refresh_token = _create_jwt(refresh_payload, secret)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE
    }


def _create_jwt(payload: dict, secret: str) -> str:
    """创建 JWT"""
    header = {"alg": "HS256", "typ": "JWT"}
    
    header_b64 = _base64url_encode(json.dumps(header).encode())
    payload_b64 = _base64url_encode(json.dumps(payload).encode())
    
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    signature_b64 = _base64url_encode(signature)
    
    return f"{message}.{signature_b64}"


def verify_token(token: str, token_type: str = "access") -> Optional[TokenPayload]:
    """
    验证 JWT
    
    Args:
        token: JWT 字符串
        token_type: 期望的 token 类型 ("access" 或 "refresh")
    
    Returns:
        TokenPayload 或 None（验证失败）
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        secret = _get_jwt_secret()
        
        # 验证签名
        message = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
        actual_sig = _base64url_decode(signature_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        # 解析载荷
        payload = json.loads(_base64url_decode(payload_b64))
        
        # 检查类型
        if payload.get("type") != token_type:
            return None
        
        # 检查过期
        if payload.get("exp", 0) < int(time.time()):
            return None
        
        return TokenPayload(
            type=payload["type"],
            exp=payload["exp"],
            iat=payload["iat"]
        )
    except Exception:
        return None


# ---------- 认证装饰器 ----------
_is_local: Optional[bool] = None


def set_local_mode(is_local: bool):
    """设置本地模式状态"""
    global _is_local
    _is_local = is_local


def require_auth(func: Callable) -> Callable:
    """
    路由认证装饰器
    
    - 本地部署时直接放行
    - 远程部署时验证 JWT
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # 本地模式直接放行
        if _is_local:
            return await func(*args, **kwargs)
        
        # 从参数中获取 request
        request: Optional[Request] = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if request is None:
            request = kwargs.get('request')
        
        if request is None:
            return JSONResponse({"success": False, "message": "Internal error"}, status_code=500)
        
        # 获取 token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.headers.get("token", "")
        
        if not token:
            return JSONResponse({"success": False, "message": "未提供认证令牌"}, status_code=401)
        
        # 验证 token
        payload = verify_token(token, "access")
        if payload is None:
            return JSONResponse({"success": False, "message": "认证令牌无效或已过期"}, status_code=401)
        
        return await func(*args, **kwargs)
    
    return wrapper


def generate_random_password(length: int = 16) -> str:
    """生成随机密码"""
    return secrets.token_urlsafe(length)
