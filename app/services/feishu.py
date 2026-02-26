"""
@NEW: 飞书机器人服务类 - 简化版
只支持文本消息发送
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Optional

import httpx


class FeishuBot:
    """
    @NEW: 飞书自定义机器人服务类（简化版）
    只支持文本消息发送
    """

    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        """
        初始化飞书机器人

        Args:
            webhook_url: 飞书机器人的webhook地址（必填）
            secret: 签名密钥（如果启用了签名验证，可选）
        """
        self.webhook_url = webhook_url
        self.secret = secret

    def _gen_sign(self, timestamp: int) -> str:
        """
        生成签名（和钉钉完全一致）

        Args:
            timestamp: 时间戳（秒）

        Returns:
            base64编码的签名
        """
        if not self.secret:
            return ""

        # 签名算法：timestamp + "\n" + secret 进行 HMAC-SHA256
        string_to_sign = f'{timestamp}\n{self.secret}'
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    def _build_text_payload(self, text: str) -> dict:
        """
        构建文本消息的请求payload

        Args:
            text: 文本内容
        """
        timestamp = int(time.time())
        payload = {
            "timestamp": str(timestamp),
            "msg_type": "text",
            "content": {
                "text": text
            }
        }

        # 如果配置了secret，添加签名
        if self.secret:
            payload["sign"] = self._gen_sign(timestamp)

        return payload

    async def _post(self, payload: dict) -> dict:
        """
        发送POST请求到飞书

        Args:
            payload: 请求数据
        """
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self.webhook_url, json=payload)
            data = resp.json()

            # 飞书返回码：0表示成功
            if data.get("code") != 0:
                error_msg = data.get('msg', '未知错误')
                raise Exception(f"飞书发送失败: {error_msg}")
            return data

    async def send_text(self, text: str) -> dict:
        """
        发送文本消息

        Args:
            text: 文本内容

        Example:
            await bot.send_text("你好，这是一条测试消息")
        """
        payload = self._build_text_payload(text)
        return await self._post(payload)