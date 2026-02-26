import random
import string
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, BigInteger, DateTime, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _random_id(prefix: str, length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    return prefix + "".join(random.choices(chars, k=length))


# ── 用户表 ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(200), nullable=False)
    created_on = Column(DateTime, default=datetime.utcnow)
    modified_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── 发送渠道（仅钉钉） ─────────────────────────────────
class SendWay(Base):
    __tablename__ = "send_ways"

    id = Column(String(12), primary_key=True)
    name = Column(String(100), nullable=False, default="")
    type = Column(String(100), nullable=False, default="dtalk", index=True)
    auth = Column(String(2048), nullable=False, default="")
    created_by = Column(String(100), default="")
    modified_by = Column(String(100), default="")
    created_on = Column(DateTime, default=datetime.utcnow)
    modified_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_id() -> str:
        return _random_id("WY")


# ── 发送任务 ────────────────────────────────────────────
class SendTask(Base):
    __tablename__ = "send_tasks"

    id = Column(String(12), primary_key=True)
    name = Column(String(100), nullable=False, default="")
    created_by = Column(String(100), default="")
    modified_by = Column(String(100), default="")
    created_on = Column(DateTime, default=datetime.utcnow)
    modified_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_id() -> str:
        return _random_id("TK")


# ── 任务实例（任务 ↔ 渠道的关联） ─────────────────────
class SendTaskIns(Base):
    __tablename__ = "send_tasks_ins"

    id = Column(String(12), primary_key=True)
    task_id = Column(String(12), nullable=False, default="", index=True)
    way_id = Column(String(12), nullable=False, default="", index=True)
    way_type = Column(String(100), nullable=False, default="")
    content_type = Column(String(100), nullable=False, default="text")
    # 去掉 config 和 extra 字段
    enable = Column(Integer, default=1)
    created_by = Column(String(100), default="")
    modified_by = Column(String(100), default="")
    created_on = Column(DateTime, default=datetime.utcnow)
    modified_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_id() -> str:
        return _random_id("IN")


# ── 发送日志 ────────────────────────────────────────────
class SendLog(Base):
    __tablename__ = "send_tasks_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(12), nullable=False, default="", index=True)
    name = Column(String(256), nullable=False, default="")
    log = Column(Text)
    status = Column(Integer, default=0)
    caller_ip = Column(String(256), default="")
    created_on = Column(DateTime, default=datetime.utcnow)
    modified_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── 发送统计 ────────────────────────────────────────────
class SendStat(Base):
    __tablename__ = "send_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(12), nullable=False, default="")
    day = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)
    num = Column(BigInteger, default=0)

    __table_args__ = (
        UniqueConstraint("task_id", "day", "status", name="idx_task_day_status"),
    )
