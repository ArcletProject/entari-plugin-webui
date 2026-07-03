from __future__ import annotations

from entari_plugin_database import Base, Mapped, mapped_column
from sqlalchemy import Integer, String


class MessageStat(Base):
    __tablename__ = "webui_message_stat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False, comment="YYYY-MM-DD")
    count: Mapped[int] = mapped_column(Integer, default=0)
