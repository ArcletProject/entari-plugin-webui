from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field


@dataclass
class Session:
    sid: str
    ip: str
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    expires_at: float = 0.0

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at


class SessionStore:
    def __init__(self, ttl: int):
        self._ttl = ttl
        self._store: dict[str, Session] = {}

    def create(self, *, ip: str) -> str:
        sid = secrets.token_urlsafe(24)
        now = time.time()
        self._store[sid] = Session(sid=sid, ip=ip, created_at=now, last_seen=now, expires_at=now + self._ttl)
        return sid

    def get(self, sid: str | None) -> Session | None:
        if not sid:
            return None
        sess = self._store.get(sid)
        if sess is None:
            return None
        if sess.expired:
            self._store.pop(sid, None)
            return None
        sess.last_seen = time.time()
        return sess

    def refresh_if_needed(self, sess: Session) -> bool:
        remaining = sess.expires_at - time.time()
        if remaining < self._ttl / 3:
            sess.expires_at = time.time() + self._ttl
            return True
        return False

    def destroy(self, sid: str) -> bool:
        return self._store.pop(sid, None) is not None

    def count(self) -> int:
        return len(self._store)
