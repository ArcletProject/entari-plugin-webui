from __future__ import annotations

from loguru import logger


def audit(event: str, **fields: object) -> None:
    parts = " ".join(f"{k}={v}" for k, v in fields.items())
    logger.info(f"[audit] {event} {parts}".strip())
