from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Settings:
    raw: dict[str, Any]
    timezone: str
    report_title: str
    timeout: int
    retries: int
    max_news: int


def load_settings(path: str | Path) -> Settings:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    required = ("timezone", "report", "assets", "news")
    missing = [key for key in required if key not in raw]
    if missing:
        raise ValueError(f"配置缺少字段: {', '.join(missing)}")
    http = raw.get("http", {})
    return Settings(
        raw=raw,
        timezone=str(raw["timezone"]),
        report_title=str(raw["report"].get("title", "跨资产市场晨报")),
        timeout=int(http.get("timeout_seconds", 15)),
        retries=int(http.get("retries", 3)),
        max_news=int(raw["news"].get("max_items", 12)),
    )


def env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None
