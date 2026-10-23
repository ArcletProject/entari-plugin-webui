from __future__ import annotations

import time
from collections import deque
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from satori import LoginStatus

if TYPE_CHECKING:
    from satori.client import Account

_WINDOW_SECONDS = 60.0


def _current_accounts() -> list[Account]:
    try:
        from arclet.entari import Entari

        return list(Entari.current().accounts.values())
    except Exception:  # noqa: BLE001
        return []


class AccountRegistry:
    """保存账号状态与最近一分钟的消息收发计数。

    ``Entari.accounts`` 是账号列表的权威来源；本类只补充
    ``AccountUpdate`` 事件带来的状态，以及事件监听器统计的速率。
    """

    def __init__(self) -> None:
        self._statuses: dict[int, LoginStatus] = {}
        self._sent: dict[int, deque[float]] = {}
        self._received: dict[int, deque[float]] = {}

    def update(self, account: Account, status: LoginStatus | int) -> None:
        self._statuses[id(account)] = LoginStatus(status)

    def record_sent(self, account: Account, now: float | None = None) -> None:
        self._record(self._sent, account, now)

    def record_received(self, account: Account, now: float | None = None) -> None:
        self._record(self._received, account, now)

    def snapshot(self, accounts: Iterable[Account] | None = None, now: float | None = None) -> dict[str, Any]:
        if accounts is None:
            accounts = _current_accounts()
        timestamp = time.monotonic() if now is None else now

        items: list[dict[str, Any]] = []
        sent_total = 0
        received_total = 0
        online = 0
        for account in accounts:
            status = self._resolve_status(account)
            if status == LoginStatus.ONLINE:
                online += 1
            sent = self._rate(self._sent, account, timestamp)
            received = self._rate(self._received, account, timestamp)
            sent_total += sent
            received_total += received
            items.append(
                {
                    "self_id": account.self_id,
                    "name": self._display_name(account),
                    "avatar": getattr(account.self_info.user, "avatar", None),
                    "platform": account.platform,
                    "adapter": account.adapter,
                    "status": status.name.lower(),
                    "sent_per_min": sent,
                    "received_per_min": received,
                }
            )

        return {
            "accounts": items,
            "summary": {
                "total": len(items),
                "online": online,
                "sent_per_min": sent_total,
                "received_per_min": received_total,
            },
        }

    def reset(self) -> None:
        self._statuses.clear()
        self._sent.clear()
        self._received.clear()

    @staticmethod
    def _record(buckets: dict[int, deque[float]], account: Account, now: float | None) -> None:
        timestamp = time.monotonic() if now is None else now
        bucket = buckets.setdefault(id(account), deque())
        bucket.append(timestamp)
        AccountRegistry._prune(bucket, timestamp)

    @staticmethod
    def _prune(bucket: deque[float], now: float) -> None:
        cutoff = now - _WINDOW_SECONDS
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

    def _rate(self, buckets: dict[int, deque[float]], account: Account, now: float) -> int:
        bucket = buckets.get(id(account))
        if not bucket:
            return 0
        self._prune(bucket, now)
        return len(bucket)

    def _resolve_status(self, account: Account) -> LoginStatus:
        if (status := self._statuses.get(id(account))) is not None:
            return status
        reported = getattr(getattr(account, "self_info", None), "status", None)
        if reported is not None:
            try:
                return LoginStatus(reported)
            except ValueError:
                pass
        connected = getattr(account, "connected", None)
        if connected is not None and connected.is_set():
            return LoginStatus.ONLINE
        return LoginStatus.OFFLINE

    @staticmethod
    def _display_name(account: Account) -> str:
        user = account.self_info.user
        return user.name or user.nick or user.id


account_registry = AccountRegistry()
