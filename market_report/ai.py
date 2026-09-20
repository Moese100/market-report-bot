from __future__ import annotations

import logging
from dataclasses import dataclass

from market_report.config import env
from market_report.http import HttpClient

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AiResult:
    content: str | None
    provider: str | None
    warnings: list[str]


class AiAnalyzer:
    def __init__(self, http: HttpClient, providers: list[dict[str, str]]) -> None:
        self.http = http
        self.providers = providers

    def analyze(self, prompt: str) -> AiResult:
        warnings: list[str] = []
        configured = 0
        for provider in self.providers:
            key = env(provider["api_key_env"])
            if not key:
                continue
            configured += 1
            try:
                payload = {
                    "model": provider["model"],
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是严谨的跨资产市场编辑。只使用用户给出的数字和链接；"
                                "缺乏证据时明确写未知，绝不编造。"
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2600,
                    "stream": False,
                }
                response = self.http.post(
                    provider["base_url"].rstrip("/") + "/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=120,
                )
                content = response.json()["choices"][0]["message"]["content"].strip()
                if not content:
                    raise ValueError("模型返回空内容")
                return AiResult(content=content, provider=provider["name"], warnings=warnings)
            except Exception as exc:
                LOGGER.exception("AI provider %s failed", provider["name"])
                warnings.append(f"AI {provider['name']} 失败，已尝试下一个模型：{_short(exc)}")
        if configured == 0:
            warnings.append("未配置 AI API Key，已生成纯数据版报告")
        else:
            warnings.append("所有 AI 服务均不可用，已生成纯数据版报告")
        return AiResult(content=None, provider=None, warnings=warnings)


def _short(exc: Exception) -> str:
    return (str(exc).replace("\n", " ")[:160] or exc.__class__.__name__)
