def test_write_and_get_all():
    from entari_plugin_webui.core.log_stream import LogRingBuffer

    b = LogRingBuffer(10)
    b.write("line1\n")
    b.write("line2\n")
    assert "line1" in b.get_all()
    assert b.position == 2


def test_get_recent():
    from entari_plugin_webui.core.log_stream import LogRingBuffer

    b = LogRingBuffer(2)
    b.write("a\n")
    b.write("b\n")
    b.write("c\n")
    recent, pos = b.get_recent(2)
    assert recent.strip() in ("b\nc", "b", "c")
    assert pos == 3


def test_get_new_since():
    from entari_plugin_webui.core.log_stream import LogRingBuffer

    b = LogRingBuffer(5)
    b.write("a\n")
    p1 = b.position
    b.write("b\n")
    text, p2 = b.get_new_since(p1)
    assert "b" in text
    assert p2 == 2


def test_overflow_wrap():
    from entari_plugin_webui.core.log_stream import LogRingBuffer

    b = LogRingBuffer(2)
    for i in range(5):
        b.write(f"l{i}\n")
    assert b.position == 5
