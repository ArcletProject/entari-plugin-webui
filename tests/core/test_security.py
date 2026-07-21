def test_is_hashed_password():
    from entari_plugin_webui.core.security import hash_password, is_hashed_password

    h = hash_password("secret123")
    assert is_hashed_password(h) is True
    assert is_hashed_password("plain_password") is False
    assert is_hashed_password("") is False
    assert is_hashed_password("pbkdf2_sha256$abc$def$ghi") is False
    assert is_hashed_password("too$few$parts") is False
    assert is_hashed_password("too$many$parts$here$now") is False


def test_hash_and_verify():
    from entari_plugin_webui.core.security import hash_password, verify_password

    h = hash_password("secret123")
    assert h.startswith("pbkdf2_sha256$100000$")
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False


def test_is_local_deployment():
    from entari_plugin_webui.core.security import is_local_deployment

    assert is_local_deployment("127.0.0.1") is True
    assert is_local_deployment("localhost") is True
    assert is_local_deployment("::1") is True
    assert is_local_deployment(None) is True
    assert is_local_deployment("0.0.0.0") is False
    assert is_local_deployment("10.0.0.1") is False


def test_login_throttle():
    from entari_plugin_webui.core.security import LoginThrottle

    t = LoginThrottle(limit=3, window=1.0)
    assert not t.is_limited("1.1.1.1")
    for _ in range(3):
        t.record_failure("1.1.1.1")
    assert t.is_limited("1.1.1.1")
    t.reset("1.1.1.1")
    assert not t.is_limited("1.1.1.1")
