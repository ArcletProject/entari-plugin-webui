import time


def test_create_and_get():
    from entari_plugin_webui.core.session import SessionStore

    s = SessionStore(ttl=60)
    sid = s.create(ip="1.2.3.4")
    sess = s.get(sid)
    assert sess is not None
    assert sess.ip == "1.2.3.4"


def test_expired_returns_none():
    from entari_plugin_webui.core.session import SessionStore

    s = SessionStore(ttl=0)
    sid = s.create(ip="x")
    time.sleep(0.01)
    assert s.get(sid) is None


def test_refresh_extends_when_low():
    from entari_plugin_webui.core.session import SessionStore

    s = SessionStore(ttl=100)
    sid = s.create(ip="x")
    sess = s.get(sid)
    assert sess is not None
    old_exp = sess.expires_at
    sess.expires_at = sess.expires_at - 90
    s.refresh_if_needed(sess)
    assert sess.expires_at > old_exp - 50


def test_destroy():
    from entari_plugin_webui.core.session import SessionStore

    s = SessionStore(ttl=60)
    sid = s.create(ip="x")
    assert s.destroy(sid) is True
    assert s.get(sid) is None
