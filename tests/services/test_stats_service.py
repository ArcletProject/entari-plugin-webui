from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_today_messages():
    from entari_plugin_webui.services import stats_service as ss

    await ss.increment("qq")
    await ss.increment("qq")
    got = await ss.today_messages()
    assert got == 2
