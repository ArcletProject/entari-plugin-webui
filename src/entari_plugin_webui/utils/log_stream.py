"""日志环形缓冲区 - 解决 StringIO 内存泄漏问题"""

from collections import deque
from typing import Optional
from io import StringIO
import threading


class LogRingBuffer:
    """
    日志环形缓冲区
    
    固定容量，超出时自动丢弃最旧的日志行
    线程安全
    """
    
    def __init__(self, max_lines: int = 1000):
        self._buffer: deque[str] = deque(maxlen=max_lines)
        self._lock = threading.Lock()
        self._position = 0  # 用于追踪读取位置
    
    def write(self, text: str):
        """
        写入日志文本
        
        自动按行分割存储
        """
        if not text:
            return
        
        with self._lock:
            # 按行分割，但保留换行符
            lines = text.splitlines(keepends=True)
            for line in lines:
                self._buffer.append(line)
                self._position += 1
    
    def get_all(self) -> str:
        """获取所有日志"""
        with self._lock:
            return ''.join(self._buffer)
    
    def get_recent(self, n: int = 100) -> str:
        """获取最近 n 行日志"""
        with self._lock:
            lines = list(self._buffer)[-n:]
            return ''.join(lines)
    
    def get_new_since(self, last_position: int) -> tuple[str, int]:
        """
        获取指定位置之后的新日志
        
        Args:
            last_position: 上次读取的位置
        
        Returns:
            (新日志内容, 当前位置)
        """
        with self._lock:
            current_position = self._position
            
            if last_position >= current_position:
                return '', current_position
            
            # 计算需要读取的行数
            lines_to_read = current_position - last_position
            
            # 如果请求的行数超过缓冲区大小，只返回缓冲区内的
            buffer_list = list(self._buffer)
            if lines_to_read > len(buffer_list):
                return ''.join(buffer_list), current_position
            
            # 返回最后 lines_to_read 行
            new_lines = buffer_list[-lines_to_read:]
            return ''.join(new_lines), current_position
    
    @property
    def position(self) -> int:
        """当前位置（用于增量读取）"""
        with self._lock:
            return self._position
    
    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self._buffer.clear()
            self._position = 0


class LogWriter:
    """
    日志写入器
    
    兼容 loguru 的 sink 接口，同时写入 LogRingBuffer
    """
    
    def __init__(self, buffer: LogRingBuffer):
        self._buffer = buffer
    
    def write(self, message: str):
        """写入日志"""
        self._buffer.write(message)
    
    def flush(self):
        """刷新（无操作）"""
        pass


# 全局日志缓冲区
_log_buffer: Optional[LogRingBuffer] = None


def get_log_buffer() -> LogRingBuffer:
    """获取全局日志缓冲区"""
    global _log_buffer
    if _log_buffer is None:
        _log_buffer = LogRingBuffer(max_lines=1000)
    return _log_buffer
