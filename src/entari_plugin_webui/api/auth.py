from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from entari_plugin_webui import webui_config

from ..core.audit import audit
from ..core.error import AuthRequired, TooManyRequests
from ..core.security import (
    hash_password,
    is_local_mode,
    verify_password,
)
from ..core.session import SessionStore
from .deps import get_session_store, require_auth

router = APIRouter(prefix="/api/auth", tags=["auth"])

_COOKIE = "webui_sid"


class LoginRequest(BaseModel):
    password: str = Field(min_length=1)


class PasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.get("/check")
async def check_auth():
    return {"local_mode": is_local_mode(), "initialized": bool(webui_config.password)}


@router.post("/login")
async def login(body: LoginRequest, request: Request, store: SessionStore = Depends(get_session_store)):
    ip = _client_ip(request)
    from .. import _login_throttle  # type: ignore  # noqa: PLC0415

    if is_local_mode():
        sid = store.create(ip=ip)
        return _json_with_cookie({"success": True, "local_mode": True}, sid)

    if _login_throttle.is_limited(ip):
        audit("login.failed", ip=ip, reason="rate_limited")
        raise TooManyRequests(retry_after=_login_throttle.retry_after(ip), message="尝试过于频繁，请稍后再试")

    if not webui_config.password:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "管理员密码尚未初始化")

    if not verify_password(body.password, webui_config.password):
        _login_throttle.record_failure(ip)
        audit("login.failed", ip=ip, reason="wrong_password")
        raise AuthRequired(message="密码错误")

    _login_throttle.reset(ip)
    sid = store.create(ip=ip)
    audit("login.success", ip=ip)
    return _json_with_cookie({"success": True, "local_mode": False}, sid)


@router.post("/logout")
async def logout(request: Request, store: SessionStore = Depends(get_session_store)):
    sid = request.cookies.get(_COOKIE)
    if sid:
        store.destroy(sid)
    if not is_local_mode():
        audit("logout", ip=_client_ip(request))
    resp = JSONResponse({"success": True})
    resp.delete_cookie(_COOKIE, path="/")
    return resp


@router.put("/password")
async def change_password(
    body: PasswordRequest,
    request: Request,
    _sess=Depends(require_auth),
):
    if not is_local_mode() and not verify_password(body.old_password, webui_config.password):
        audit("password.change.failed", ip=_client_ip(request), reason="wrong_old")
        raise AuthRequired(message="旧密码错误")
    webui_config.password = hash_password(body.new_password)
    audit("password.change", ip=_client_ip(request))
    return {"success": True}


def _json_with_cookie(payload: dict, sid: str) -> JSONResponse:
    resp = JSONResponse(payload)
    secure = True
    resp.set_cookie(
        _COOKIE,
        sid,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=webui_config.session_ttl,
        path="/",
    )
    return resp
