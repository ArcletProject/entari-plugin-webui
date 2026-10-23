from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from satori import LoginStatus

if TYPE_CHECKING:
    from entari_plugin_webui.core.accounts import AccountRegistry


def make_account(
    self_id: str = "bot1",
    name: str = "Bot One",
    platform: str = "qq",
    adapter: str = "satori",
    avatar: str | None = "https://example.com/avatar.png",
    status: LoginStatus = LoginStatus.ONLINE,
    connected: bool = True,
):
    user = SimpleNamespace(id=self_id, name=name, nick=None, avatar=avatar)
    self_info = SimpleNamespace(user=user, platform=platform, adapter=adapter, status=status)
    return SimpleNamespace(
        self_info=self_info,
        platform=platform,
        self_id=self_id,
        adapter=adapter,
        connected=SimpleNamespace(is_set=lambda: connected),
    )


@pytest.fixture
def registry():
    # 延迟导入：entari 的插件加载需要先完成 Entari.load
    from entari_plugin_webui.core.accounts import AccountRegistry

    return AccountRegistry()


def test_snapshot_describes_account_display_fields(registry: AccountRegistry):
    account = make_account()

    registry.update(account, LoginStatus.ONLINE)
    snap = registry.snapshot([account], now=1000.0)

    assert snap["accounts"] == [
        {
            "self_id": "bot1",
            "name": "Bot One",
            "avatar": "https://example.com/avatar.png",
            "platform": "qq",
            "adapter": "satori",
            "status": "online",
            "sent_per_min": 0,
            "received_per_min": 0,
        }
    ]
    assert snap["summary"] == {
        "total": 1,
        "online": 1,
        "sent_per_min": 0,
        "received_per_min": 0,
    }


def test_update_changes_account_status(registry: AccountRegistry):
    account = make_account()

    registry.update(account, LoginStatus.ONLINE)
    assert registry.snapshot([account])["accounts"][0]["status"] == "online"

    registry.update(account, LoginStatus.OFFLINE)
    assert registry.snapshot([account])["accounts"][0]["status"] == "offline"


def test_status_falls_back_to_account_connection_state(registry: AccountRegistry):
    online = make_account("a", connected=True)
    offline = make_account("b", connected=False, status=LoginStatus.OFFLINE)

    snap = registry.snapshot([online, offline])

    assert [a["status"] for a in snap["accounts"]] == ["online", "offline"]


def test_rates_count_only_events_in_the_last_minute(registry: AccountRegistry):
    account = make_account()

    registry.record_sent(account, now=1000.0)
    registry.record_sent(account, now=1020.0)
    registry.record_received(account, now=1040.0)

    snap = registry.snapshot([account], now=1050.0)
    assert snap["accounts"][0]["sent_per_min"] == 2
    assert snap["accounts"][0]["received_per_min"] == 1

    later = registry.snapshot([account], now=1100.0)
    assert later["accounts"][0]["sent_per_min"] == 0
    assert later["accounts"][0]["received_per_min"] == 1

    even_later = registry.snapshot([account], now=1101.0)
    assert even_later["accounts"][0]["sent_per_min"] == 0
    assert even_later["accounts"][0]["received_per_min"] == 0


def test_summary_sums_rates_and_counts_online_accounts(registry: AccountRegistry):
    first = make_account("a")
    second = make_account("b")

    registry.update(first, LoginStatus.ONLINE)
    registry.update(second, LoginStatus.OFFLINE)
    registry.record_sent(first, now=1000.0)
    registry.record_sent(second, now=1000.0)
    registry.record_received(second, now=1000.0)

    snap = registry.snapshot([first, second], now=1000.0)

    assert snap["summary"] == {
        "total": 2,
        "online": 1,
        "sent_per_min": 2,
        "received_per_min": 1,
    }


def test_name_falls_back_to_nick_then_id(registry: AccountRegistry):
    account = make_account("bot1", name=None)
    account.self_info.user.nick = "小一"

    assert registry.snapshot([account])["accounts"][0]["name"] == "小一"

    account.self_info.user.nick = None
    assert registry.snapshot([account])["accounts"][0]["name"] == "bot1"


def test_accounts_endpoint(client):
    r = client.get("/api/accounts")

    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["accounts"] == []
    assert body["summary"] == {
        "total": 0,
        "online": 0,
        "sent_per_min": 0,
        "received_per_min": 0,
    }


def test_system_endpoint(client):
    r = client.get("/api/system")

    assert r.status_code == 200
    body = r.json()
    for key in ("entari_version", "webui_version", "python", "system", "cpu", "cpu_count"):
        assert key in body
    assert isinstance(body["cpu_count"], int)
    assert body["python"].startswith("3.")
