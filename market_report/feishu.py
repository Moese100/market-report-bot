from __future__ import annotations

import base64
import hashlib
import hmac
import time

from market_report.http import HttpClient


class FeishuSender:
    def __init__(
        self,
        http: HttpClient,
        webhook_url: str,
        secret: str | None = None,
        max_chars: int = 12000,
    ) -> None:
        if not webhook_url.startswith("https://open.feishu.cn/"):
            raise ValueError("FEISHU_WEBHOOK_URL 必须是 open.feishu.cn 的 HTTPS 地址")
        self.http = http
        self.webhook_url = webhook_url
        self.secret = secret or None
        self.max_chars = max_chars

    def _sign(self, payload: dict) -> dict:
        """飞书签名校验：timestamp + "\\n" + secret 作为 HMAC key，对空串做 SHA256。"""
        if not self.secret:
            return payload
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self.secret}"
        digest = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        signed = dict(payload)
        signed["timestamp"] = timestamp
        signed["sign"] = base64.b64encode(digest).decode("utf-8")
        return signed

    def send(self, title: str, markdown: str) -> None:
        chunks = split_markdown(markdown, self.max_chars)
        for index, chunk in enumerate(chunks, 1):
            suffix = f"（{index}/{len(chunks)}）" if len(chunks) > 1 else ""
            payload = {
                "msg_type": "interactive",
                "card": {
                    "config": {"wide_screen_mode": True},
                    "header": {
                        "template": "blue",
                        "title": {"tag": "plain_text", "content": title + suffix},
                    },
                    "elements": [{"tag": "markdown", "content": chunk}],
                },
            }
            response = self.http.post(self.webhook_url, json=self._sign(payload), timeout=30)
            result = response.json()
            code = result.get("code", result.get("StatusCode", 0))
            if code not in (0, "0", None):
                raise RuntimeError(f"飞书返回失败: {result}")


def split_markdown(text: str, max_chars: int) -> list[str]:
    if max_chars < 100:
        raise ValueError("max_chars 过小")
    remaining = text.strip()
    chunks: list[str] = []
    while len(remaining) > max_chars:
        split_at = remaining.rfind("\n\n", 0, max_chars)
        if split_at < max_chars // 2:
            split_at = remaining.rfind("\n", 0, max_chars)
        if split_at <= 0:
            split_at = max_chars
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks
