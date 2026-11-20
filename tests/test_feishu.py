import base64
import hashlib
import hmac
from unittest.mock import patch

from market_report.feishu import FeishuSender, split_markdown


class DummyHttp:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def post(self, url: str, json: dict, timeout: int = 30) -> "DummyResponse":
        self.calls.append(json)
        return DummyResponse()


class DummyResponse:
    def json(self) -> dict:
        return {"code": 0}


def test_split_markdown_keeps_all_text() -> None:
    original = ("第一段内容\n\n第二段内容很长\n" * 20).strip()
    chunks = split_markdown(original, 120)
    assert len(chunks) > 1
    assert "".join(chunks).replace("\n", "") == original.replace("\n", "")
    assert all(len(chunk) <= 120 for chunk in chunks)


def test_sign_matches_feishu_algorithm() -> None:
    sender = FeishuSender(
        DummyHttp(),
        "https://open.feishu.cn/open-apis/bot/v2/hook/test",
        secret="s3cret",
    )
    with patch("market_report.feishu.time.time", return_value=1700000000):
        signed = sender._sign({"msg_type": "text", "content": {"text": "hi"}})
    expected = base64.b64encode(
        hmac.new(b"1700000000\ns3cret", digestmod=hashlib.sha256).digest()
    ).decode("utf-8")
    assert signed["timestamp"] == "1700000000"
    assert signed["sign"] == expected


def test_send_attaches_signature_when_secret_configured() -> None:
    http = DummyHttp()
    sender = FeishuSender(
        http,
        "https://open.feishu.cn/open-apis/bot/v2/hook/test",
        secret="s3cret",
    )
    sender.send("标题", "正文")
    assert len(http.calls) == 1
    payload = http.calls[0]
    assert "sign" in payload and "timestamp" in payload


def test_send_omits_signature_without_secret() -> None:
    http = DummyHttp()
    sender = FeishuSender(http, "https://open.feishu.cn/open-apis/bot/v2/hook/test")
    sender.send("标题", "正文")
    payload = http.calls[0]
    assert "sign" not in payload and "timestamp" not in payload
