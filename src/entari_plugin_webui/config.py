from arclet.entari.config.models.default import BasicConfModel


class Config(BasicConfModel):
    password: str = ""
    """WebUI 的登录密码，在本地部署时可以不设置"""
    registry_url: str = "https://arclet.top/entari-registry/registry.json"
    """插件市场网址"""
    package_manager: str = ""
    """安装插件时使用的包管理器，不指定时将自动探测"""
    session_ttl: int = 43200
    """会话过期时间, 单位为秒，默认 12 小时"""
    log_buffer_lines: int = 5000
    """日志缓冲区行数，超过该行数将会丢弃最早的日志，默认 5000 行"""
    login_rate_limit: str = "5/60s"
    """登录请求的速率限制，格式为 <次数>/<时间>，例如 5/60s 表示每分钟最多允许 5 次登录请求，默认 5/60s"""
