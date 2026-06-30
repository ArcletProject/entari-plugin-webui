from __future__ import annotations


def _headers():
    return {"X-Requested-With": "XMLHttpRequest"}


def _login(client, password):
    return client.post("/api/auth/login", json={"password": password}, headers=_headers())


def test_local_mode_no_password(client):
    from entari_plugin_webui.core.security import set_local_mode

    set_local_mode(True)
    r = client.get("/api/auth/check")
    assert r.json()["local_mode"] is True
    r = _login(client, "anything")
    assert r.status_code == 200
    assert r.json()["local_mode"] is True


def test_remote_mode_login_flow(client):
    from entari_plugin_webui import webui_config
    from entari_plugin_webui.core.security import hash_password, set_local_mode

    set_local_mode(False)
    webui_config.password = hash_password("secret123")
    r = client.get("/api/auth/check")
    assert r.json() == {"local_mode": False, "initialized": True}

    assert _login(client, "wrong").status_code == 401

    r = _login(client, "secret123")
    assert r.status_code == 200
    assert r.json()["local_mode"] is False
    assert "webui_sid" in r.cookies

    client.cookies.set("webui_sid", r.cookies["webui_sid"])
    assert client.get("/api/health").status_code == 200


def test_remote_require_auth_without_cookie(client):
    from entari_plugin_webui.core.security import set_local_mode

    set_local_mode(False)
    assert client.post("/api/auth/logout", headers=_headers()).status_code == 200


def test_change_password(client):
    from entari_plugin_webui import webui_config
    from entari_plugin_webui.core.security import hash_password, set_local_mode

    set_local_mode(False)
    webui_config.password = hash_password("secret123")
    r = _login(client, "secret123")
    client.cookies.set("webui_sid", r.cookies["webui_sid"])
    body = {"old_password": "secret123", "new_password": "newpass123"}
    assert client.put("/api/auth/password", json=body, headers=_headers()).status_code == 200
    assert _login(client, "secret123").status_code == 401
