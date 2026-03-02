"""统计数据 API"""

from datetime import datetime, timedelta

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, and_

from entari_plugin_server import add_route
from entari_plugin_database import get_session
from arclet.entari.plugin import get_plugins

from ..core.auth import require_auth
from ..models.stats import MessageStat


# 启动时间
START_TIME = datetime.utcnow()


def register_stats_routes():
    """注册统计相关路由"""
    pass  # 路由通过装饰器注册


@add_route("/api/stats", methods=["GET"])
@require_auth
async def get_stats() -> JSONResponse:
    """
    获取统计数据
    
    Returns:
        {
            "today_messages": 0,
            "week_messages": [0, 0, 0, 0, 0, 0, 0],
            "total_messages": 0,
            "plugins_enabled": 5,
            "plugins_total": 10,
            "runtime_minutes": 120
        }
    """
    # 运行时长
    runtime_minutes = int((datetime.utcnow() - START_TIME).total_seconds() // 60)
    
    # 插件统计
    plugins = get_plugins()
    plugins_total = len(plugins)
    plugins_enabled = sum(1 for p in plugins if p.is_available)
    
    # 消息统计
    today_messages = await _get_today_messages()
    week_messages = await _get_week_messages()
    total_messages = await _get_total_messages()
    
    return JSONResponse({
        "success": True,
        "today_messages": today_messages,
        "week_messages": week_messages,
        "total_messages": total_messages,
        "plugins_enabled": plugins_enabled,
        "plugins_total": plugins_total,
        "runtime_minutes": runtime_minutes
    })


@add_route("/api/stats/runtime", methods=["GET"])
@require_auth
async def get_runtime() -> JSONResponse:
    """
    获取运行时状态
    """
    runtime_minutes = int((datetime.utcnow() - START_TIME).total_seconds() // 60)
    
    return JSONResponse({
        "success": True,
        "start_time": START_TIME.isoformat(),
        "runtime_minutes": runtime_minutes
    })


async def _get_today_messages() -> int:
    """今日消息数"""
    today_str = datetime.utcnow().date().isoformat()
    
    try:
        async with get_session() as session:
            stmt = select(func.sum(MessageStat.count)).where(
                MessageStat.date == today_str
            )
            result = await session.execute(stmt)
            total = result.scalar()
            return total or 0
    except Exception:
        return 0


async def _get_week_messages() -> list[int]:
    """本周每日消息数（周一到周日）"""
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    week_days = [monday + timedelta(days=i) for i in range(7)]
    
    try:
        async with get_session() as session:
            stmt = (
                select(MessageStat.date, func.sum(MessageStat.count).label("total"))
                .where(
                    and_(
                        MessageStat.date >= monday.isoformat(),
                        MessageStat.date <= week_days[-1].isoformat()
                    )
                )
                .group_by(MessageStat.date)
            )
            rows = (await session.execute(stmt)).all()
            
            day_map = {row.date: row.total for row in rows}
            return [day_map.get(d.isoformat(), 0) for d in week_days]
    except Exception:
        return [0] * 7


async def _get_total_messages() -> int:
    """总消息数"""
    try:
        async with get_session() as session:
            stmt = select(func.sum(MessageStat.count))
            result = await session.execute(stmt)
            total = result.scalar()
            return total or 0
    except Exception:
        return 0
