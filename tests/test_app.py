from datetime import datetime

from market_report.app import resolve_mode


def test_auto_mode_weekday_is_full() -> None:
    assert resolve_mode("auto", datetime(2026, 9, 18, 7, 30)) == "full"


def test_auto_mode_weekend_is_crypto() -> None:
    assert resolve_mode("auto", datetime(2026, 9, 19, 7, 30)) == "crypto"


def test_explicit_mode_wins() -> None:
    assert resolve_mode("full", datetime(2026, 9, 19, 7, 30)) == "full"
