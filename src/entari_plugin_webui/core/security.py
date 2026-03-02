"""安全相关工具函数"""

from typing import Optional


def is_local_deployment(host: Optional[str]) -> bool:
    """
    检测是否为本地部署
    
    本地部署的情况：
    - host 为 None（默认）
    - host 为 127.0.0.1
    - host 为 localhost
    - host 为 ::1 (IPv6 localhost)
    
    非本地部署（需要认证）：
    - host 为 0.0.0.0（监听所有接口）
    - host 为具体 IP 地址
    """
    if host is None:
        return True
    
    local_hosts = {"127.0.0.1", "localhost", "::1"}
    return host.lower() in local_hosts
