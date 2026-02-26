"""
钉钉机器人服务类 - 简化版
只支持文本消息发送
"""

import hashlib
import hmac
import base64
import json
import time
import urllib.parse
from typing import List, Optional

import httpx


class DingTalkBot:
    """
    钉钉自定义机器人服务类（简化版）
    只支持文本消息发送
    """

    def __init__(self, access_token: str, secret: Optional[str] = None):
        """
        初始化钉钉机器人

        Args:
            access_token: 钉钉机器人的access_token（必填）
            secret: 签名密钥（如果启用了签名验证，可选）
        """
        self.access_token = access_token
        self.secret = secret

    def _sign(self) -> tuple[str, str]:
        """
        生成签名

        Returns:
            (timestamp, sign) 时间戳和签名
        """
        timestamp = str(int(time.time() * 1000))

        # 如果没有secret，不需要签名
        if not self.secret:
            return timestamp, ""

        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))
        return timestamp, sign

    def _build_url(self) -> str:
        """
        构建请求URL

        Returns:
            完整的请求URL，包含access_token和签名（如果有）
        """
        ts, sign = self._sign()
        base_url = f"https://oapi.dingtalk.com/robot/send?access_token={self.access_token}"

        # 如果有签名，添加到URL
        if sign:
            base_url += f"&timestamp={ts}&sign={sign}"

        return base_url

    def _build_at(self, at_mobiles: List[str] = None, at_user_ids: List[str] = None, is_at_all: bool = False) -> dict:
        """
        构建 @ 人的数据

        Args:
            at_mobiles: 被@人的手机号列表
            at_user_ids: 被@人的用户ID列表
            is_at_all: 是否@所有人
        """
        at = {}
        if at_mobiles:
            at["atMobiles"] = at_mobiles
        if at_user_ids:
            at["atUserIds"] = at_user_ids
        if is_at_all:
            at["isAtAll"] = True
        return at

    async def send_text(self, content: str, at_mobiles: List[str] = None,
                        at_user_ids: List[str] = None, is_at_all: bool = False) -> dict:
        """
        发送文本消息

        Args:
            content: 文本内容
            at_mobiles: 被@人的手机号列表（可选）
            at_user_ids: 被@人的用户ID列表（可选）
            is_at_all: 是否@所有人（可选）

        Example:
            # 发送普通文本
            await bot.send_text("你好，这是一条测试消息")

            # 发送文本并@所有人
            await bot.send_text("@所有人 开会啦", is_at_all=True)

            # 发送文本并@指定手机号
            await bot.send_text("@张三 请查收", at_mobiles=["13800138000"])
        """
        payload = {
            "msgtype": "text",
            "text": {"content": content},
            "at": self._build_at(at_mobiles, at_user_ids, is_at_all)
        }
        return await self._post(payload)

    async def _post(self, payload: dict) -> dict:
        """
        发送POST请求到钉钉

        Args:
            payload: 请求数据
        """
        url = self._build_url()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()

            # 钉钉返回码：0表示成功
            if data.get("errcode", 0) != 0:
                errmsg = data.get("errmsg", "未知错误")
                raise Exception(f"钉钉发送失败: {errmsg}")
            return data