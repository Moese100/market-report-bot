from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from market_report.ai import AiAnalyzer
from market_report.config import Settings, env
from market_report.feishu import FeishuSender
from market_report.http import HttpClient
from market_report.models import MarketSnapshot
from market_report.providers.market import MarketDataProvider
from market_report.providers.news import RssNewsProvider
from market_report.renderer import build_ai_prompt, combine_report, render_data_report

LOGGER = logging.getLogger(__name__)


def resolve_mode(requested: str, now: datetime) -> str:
    if requested in {"full", "crypto"}:
        return requested
    return "crypto" if now.weekday() >= 5 else "full"


def generate_report(settings: Settings, requested_mode: str = "auto") -> tuple[str, MarketSnapshot]:
    now = datetime.now(ZoneInfo(settings.timezone))
    mode = resolve_mode(requested_mode, now)
    http = HttpClient(timeout=settings.timeout, retries=settings.retries)
    market = MarketDataProvider(http, now)
    snapshot = MarketSnapshot(generated_at=now, mode=mode)

    crypto, warnings = market.fetch_crypto(settings.raw["assets"].get("crypto", []))
    snapshot.quotes.extend(crypto)
    snapshot.warnings.extend(warnings)
    snapshot.fear_greed = market.fetch_fear_greed()

    if mode == "full":
        equities, warnings = market.fetch_traditional(
            settings.raw["assets"].get("equities", []), "equity"
        )
        snapshot.quotes.extend(equities)
        snapshot.warnings.extend(warnings)
        commodities, warnings = market.fetch_traditional(
            settings.raw["assets"].get("commodities", []), "commodity"
        )
        snapshot.quotes.extend(commodities)
        snapshot.warnings.extend(warnings)

    news, warnings = RssNewsProvider(http).fetch(
        settings.raw["news"].get("feeds", []), settings.max_news
    )
    snapshot.news = news
    snapshot.warnings.extend(warnings)

    base_report = render_data_report(snapshot, settings.report_title)
    providers = settings.raw.get("ai", {}).get("providers", [])
    ai_result = AiAnalyzer(http, providers).analyze(build_ai_prompt(snapshot, base_report))
    snapshot.warnings.extend(ai_result.warnings)
    base_report = render_data_report(snapshot, settings.report_title)
    if ai_result.content and ai_result.provider:
        report = combine_report(base_report, ai_result.content, ai_result.provider)
    else:
        report = base_report
    LOGGER.info(
        "report_generated mode=%s quotes=%d news=%d ai=%s warnings=%d",
        mode,
        len(snapshot.quotes),
        len(snapshot.news),
        ai_result.provider or "none",
        len(snapshot.warnings),
    )
    return report, snapshot


def deliver_report(settings: Settings, report: str) -> None:
    webhook = env("FEISHU_WEBHOOK_URL")
    if not webhook:
        raise RuntimeError("未配置 FEISHU_WEBHOOK_URL；请使用 --dry-run 预览或添加 GitHub Secret")
    http = HttpClient(timeout=settings.timeout, retries=settings.retries)
    FeishuSender(http, webhook).send(settings.report_title, report)
    LOGGER.info("report_sent channel=feishu")
