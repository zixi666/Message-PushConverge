import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator

_ALNUM_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]+$")


def _check_alnum(v: str, field_name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9]+", v):
        raise ValueError(f"{field_name}只能包含英文字母和数字")
    return v


# ── Auth ────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_rule(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 50:
            raise ValueError("账号长度须在3-50之间")
        if not _ALNUM_RE.match(v):
            raise ValueError("账号只能包含英文字母和数字，且首位必须是字母")
        return v

    @field_validator("password")
    @classmethod
    def password_rule(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 50:
            raise ValueError("密码长度须在6-50之间")
        _check_alnum(v, "密码")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_rule(cls, v: str) -> str:
        if len(v) < 6 or len(v) > 50:
            raise ValueError("新密码长度须在6-50之间")
        _check_alnum(v, "新密码")
        return v

class TokenResponse(BaseModel):
    token: str

# ── SendWay ─────────────────────────────────────────────
# @MODIFIED: 添加飞书渠道支持
class SendWayCreate(BaseModel):
    name: str
    # @NEW: 添加type字段，区分钉钉和飞书
    type: str = "dtalk"  # dtalk 或 feishu

    # 钉钉字段
    access_token: Optional[str] = None
    secret: Optional[str] = None

    # @NOTE: 飞书复用access_token和secret字段，不需要额外字段


class SendWayUpdate(BaseModel):
    name: Optional[str] = None

    # 钉钉/飞书通用字段
    access_token: Optional[str] = None
    secret: Optional[str] = None


class SendWayOut(BaseModel):
    id: str
    name: str
    # @NEW: 添加type字段到输出
    type: str
    auth: str
    created_by: str
    created_on: Optional[datetime] = None
    modified_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── SendTask ────────────────────────────────────────────
class SendTaskCreate(BaseModel):
    name: str


class SendTaskUpdate(BaseModel):
    name: Optional[str] = None


class SendTaskOut(BaseModel):
    id: str
    name: str
    created_by: str
    created_on: Optional[datetime] = None
    modified_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── SendTaskIns ─────────────────────────────────────────
class SendTaskInsCreate(BaseModel):
    task_id: str
    way_id: str
    content_type: str = "text"  # text 或 markdown
    # 去掉 config 和 extra

class SendTaskInsOut(BaseModel):
    id: str
    task_id: str
    way_id: str
    way_type: str
    content_type: str
    enable: int
    created_on: Optional[datetime] = None
    way_name: Optional[str] = None

    model_config = {"from_attributes": True}

class TaskInsDetail(BaseModel):
    id: str
    name: str
    ins_data: List[SendTaskInsOut]


# ── Message Send ────────────────────────────────────────
# 在 SendMessageRequest 中添加更多字段
class SendMessageRequest(BaseModel):
    task_id: str

    # 通用字段
    title: str = ""  # 标题
    text: str = ""  # 文本内容

# ── SendLog ─────────────────────────────────────────────
class SendLogOut(BaseModel):
    id: int
    task_id: str
    name: str
    log: Optional[str] = None
    status: int
    caller_ip: str
    created_on: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Statistics ──────────────────────────────────────────
class DailyStat(BaseModel):
    day: str
    succ_num: int = 0
    failed_num: int = 0
    total_num: int = 0


class StatisticOut(BaseModel):
    today_succ_num: int = 0
    today_failed_num: int = 0
    today_total_num: int = 0
    total_num: int = 0
    daily_stats: List[DailyStat] = []


# ── Common ──────────────────────────────────────────────
class R(BaseModel):
    code: int = 200
    msg: str = "ok"
    data: Optional[object] = None
