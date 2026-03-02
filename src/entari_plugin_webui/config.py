from arclet.entari.config import BasicConfModel
from arclet.entari.plugin import plugin_config


class Config(BasicConfModel):
    """WebUI 插件配置模型"""
    password: str = ""  # 管理员密码（哈希值）


webui_config = plugin_config(Config, bind=True)
