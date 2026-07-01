from __future__ import annotations

from datetime import datetime, timedelta

from arclet.entari.plugin import get_plugins
from entari_plugin_database import get_session
from sqlalchemy import func, select

from ..models.stats import MessageStat

_START = datetime.now()


def _today() -> str:
    return datetime.now().date().isoformat()


async def increment(platform: str) -> None:
    today = _today()
    async with get_session() as session:
        result = await session.execute(
            select(MessageStat).where(MessageStat.platform == platform, MessageStat.date == today)
        )
        row = result.scalar_one_or_none()
        if row:
            row.count += 1
        else:
            session.add(MessageStat(platform=platform, date=today, count=1))
        await session.commit()


async def _sum(conditions) -> int:
    async with get_session() as session:
        result = await session.execute(select(func.coalesce(func.sum(MessageStat.count), 0)).where(*conditions))
        return int(result.scalar() or 0)


async def today_messages() -> int:
    return await _sum((MessageStat.date == _today(),))


async def week_messages() -> list[int]:
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    days = [(monday + timedelta(days=i)).isoformat() for i in range(7)]

    out = [0] * 7
    async with get_session() as session:
        for i, d in enumerate(days):
            result = await session.execute(
                select(func.coalesce(func.sum(MessageStat.count), 0)).where(MessageStat.date == d)
            )
            out[i] = int(result.scalar() or 0)
    return out


async def total_messages() -> int:
    async with get_session() as session:
        result = await session.execute(select(func.coalesce(func.sum(MessageStat.count), 0)))
        return int(result.scalar() or 0)


async def get_stats() -> dict:
    plugins = list(get_plugins())
    enabled = sum(1 for p in plugins if p.is_available)
    try:
        today = await today_messages()
        week = await week_messages()
        total = await total_messages()
    except Exception:  # noqa: BLE001
        today, week, total = 0, [0] * 7, 0
    return {
        "today_messages": today,
        "week_messages": week,
        "total_messages": total,
        "plugins_enabled": enabled,
        "plugins_total": len(plugins),
        "runtime_minutes": int((datetime.now() - _START).total_seconds() // 60),
        "start_time": _START.isoformat(),
    }
