from arclet.entari.config.models.default import BasicConfModel


class Config(BasicConfModel):
    password: str = ""
    registry_url: str = ""
    session_ttl: int = 43200
    log_buffer_lines: int = 5000
    login_rate_limit: str = "5/60s"
