"""消息统计模型"""

from sqlalchemy import Integer, String, ForeignKey
from entari_plugin_database import Base, mapped_column, Mapped


class MessageStat(Base):
    """每日各平台消息计数"""
    __tablename__ = "webui_message_stat"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    instance_id: Mapped[int] = mapped_column(Integer, default=0)
    date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    count: Mapped[int] = mapped_column(Integer, default=0)
