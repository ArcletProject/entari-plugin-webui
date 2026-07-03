from __future__ import annotations

import threading
from collections import deque


class LogRingBuffer:
    def __init__(self, max_lines: int = 5000) -> None:
        self._max = max_lines
        self._lines: deque[str] = deque(maxlen=max_lines)
        self._position = 0
        self._lock = threading.Lock()

    def write(self, text: str) -> None:
        if not text:
            return
        with self._lock:
            for chunk in text.splitlines(keepends=True):
                self._lines.append(chunk)
                self._position += 1

    def get_all(self) -> str:
        with self._lock:
            return "".join(self._lines)

    def get_recent(self, n: int = 100) -> tuple[str, int]:
        with self._lock:
            recent = list(self._lines)[-n:]
            return "".join(recent), self._position

    def get_new_since(self, last_position: int) -> tuple[str, int]:
        with self._lock:
            lines_to_read = self._position - last_position
            if lines_to_read <= 0:
                return "", self._position
            if lines_to_read > len(self._lines):
                lines_to_read = len(self._lines)
            recent = list(self._lines)[-lines_to_read:]
            return "".join(recent), self._position

    @property
    def position(self) -> int:
        return self._position

    def clear(self) -> None:
        with self._lock:
            self._lines.clear()
            self._position = 0


class LogWriter:
    def __init__(self, buffer: LogRingBuffer) -> None:
        self._buffer = buffer

    def write(self, message: str) -> None:
        self._buffer.write(message)

    def flush(self) -> None:
        pass


_singleton: LogRingBuffer | None = None


def get_log_buffer() -> LogRingBuffer:
    global _singleton
    if _singleton is None:
        from .. import webui_config

        _singleton = LogRingBuffer(max_lines=webui_config.log_buffer_lines)
    return _singleton
