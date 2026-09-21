from pathlib import Path

from market_report.config import load_settings


def test_default_config_loads() -> None:
    settings = load_settings(Path("config/default.yml"))
    assert settings.timezone == "Asia/Shanghai"
    assert len(settings.raw["assets"]["crypto"]) == 3
    assert settings.raw["ai"]["providers"][0]["name"] == "DeepSeek"
