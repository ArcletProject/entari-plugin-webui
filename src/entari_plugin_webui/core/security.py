from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import time

_PBKDF2_ITERATIONS = 100_000
_SALT_BYTES = 16

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

_is_local_mode = True


def set_local_mode(value: bool) -> None:
    global _is_local_mode
    _is_local_mode = value


def is_local_mode() -> bool:
    return _is_local_mode


def is_local_deployment(host: str | None) -> bool:
    if host is None:
        return True
    return host.lower() in _LOCAL_HOSTS


def generate_random_password(length: int = 16) -> str:
    return secrets.token_urlsafe(length)[:length]


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iter_s, salt_b, hash_b = stored.split("$")
        iterations = int(iter_s)
        salt = base64.b64decode(salt_b)
        expected = base64.b64decode(hash_b)
    except (ValueError, AttributeError):
        return False
    if algo != "pbkdf2_sha256":
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(derived, expected)


def parse_rate_limit(spec: str) -> tuple[int, float]:
    m = re.match(r"^(\d+)\s*\/\s*(\d+)([smhd])$", spec.strip())
    if not m:
        raise ValueError(f"invalid rate limit spec: {spec}")
    count = int(m.group(1))
    unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(3)]
    return count, int(m.group(2)) * unit


class LoginThrottle:
    def __init__(self, limit: int, window: float) -> None:
        self._limit = limit
        self._window = window
        self._failures: dict[str, list[float]] = {}

    def is_limited(self, ip: str) -> bool:
        now = time.time()
        self._failures[ip] = [t for t in self._failures.get(ip, []) if now - t < self._window]
        return len(self._failures[ip]) >= self._limit

    def record_failure(self, ip: str) -> None:
        self._failures.setdefault(ip, []).append(time.time())

    def reset(self, ip: str) -> None:
        self._failures.pop(ip, None)

    def retry_after(self, ip: str) -> int:
        now = time.time()
        recents = [t for t in self._failures.get(ip, []) if now - t < self._window]
        if not recents:
            return 0
        return int(self._window - (now - min(recents))) + 1
