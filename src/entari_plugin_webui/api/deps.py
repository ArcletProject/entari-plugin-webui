from __future__ import annotations

from fastapi import Depends, Request

from ..core.error import AuthRequired
from ..core.security import is_local_mode
from ..core.session import Session, SessionStore


def get_session_store() -> SessionStore:
    from .. import _session_store  # type: ignore  # noqa: PLC0415

    return _session_store


def require_auth(request: Request, store: SessionStore = Depends(get_session_store)) -> Session | None:
    if is_local_mode():
        return None
    sid = request.cookies.get("webui_sid")
    sess = store.get(sid)
    if sess is None:
        raise AuthRequired("未登录或会话已过期")
    store.refresh_if_needed(sess)
    return sess
