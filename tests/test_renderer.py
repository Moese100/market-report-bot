from datetime import datetime
from zoneinfo import ZoneInfo

from market_report.models import MarketSnapshot, NewsItem, Quote
from market_report.renderer import render_data_report


def test_missing_price_is_not_rendered_as_zero() -> None:
    now = datetime(2026, 9, 19, 7, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    snapshot = MarketSnapshot(
        generated_at=now,
        mode="full",
        quotes=[
            Quote("BTC", "比特币", "crypto", None, None, "USD", "不可用", now, error="timeout")
        ],
    )
    report = render_data_report(snapshot, "测试晨报")
    assert "数据暂不可用" in report
    assert "$0" not in report


def test_news_link_is_preserved() -> None:
    now = datetime(2026, 9, 19, 7, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    snapshot = MarketSnapshot(
        generated_at=now,
        mode="crypto",
        news=[NewsItem("Example", "https://example.com/story", "Example Feed")],
    )
    report = render_data_report(snapshot, "测试晨报")
    assert "[Example](https://example.com/story)" in report
