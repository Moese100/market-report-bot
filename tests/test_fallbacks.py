from datetime import datetime

from market_report.ai import AiAnalyzer
from market_report.providers.market import MarketDataProvider


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def json(self) -> dict:
        return self.payload


class MarketHttp:
    def get(self, url: str, **_kwargs: object) -> FakeResponse:
        if "coingecko" in url:
            raise RuntimeError("primary unavailable")
        return FakeResponse({"lastPrice": "81000", "priceChangePercent": "2.5"})


class AiHttp:
    def __init__(self) -> None:
        self.calls = 0

    def post(self, _url: str, **_kwargs: object) -> FakeResponse:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("deepseek unavailable")
        return FakeResponse({"choices": [{"message": {"content": "fallback ok"}}]})


def test_crypto_falls_back_to_binance() -> None:
    provider = MarketDataProvider(MarketHttp(), datetime(2026, 9, 19, 7, 30))
    assets = [
        {
            "symbol": "BTC",
            "name": "比特币",
            "coingecko_id": "bitcoin",
            "binance_symbol": "BTCUSDT",
            "unit": "USD",
        }
    ]
    quotes, warnings = provider.fetch_crypto(assets)
    assert quotes[0].source == "Binance"
    assert quotes[0].price == 81000
    assert warnings


def test_ai_falls_back_to_second_provider(monkeypatch) -> None:
    monkeypatch.setenv("FIRST_KEY", "first")
    monkeypatch.setenv("SECOND_KEY", "second")
    providers = [
        {
            "name": "DeepSeek",
            "api_key_env": "FIRST_KEY",
            "base_url": "https://first.example/v1",
            "model": "first",
        },
        {
            "name": "OpenAI",
            "api_key_env": "SECOND_KEY",
            "base_url": "https://second.example/v1",
            "model": "second",
        },
    ]
    result = AiAnalyzer(AiHttp(), providers).analyze("prompt")
    assert result.provider == "OpenAI"
    assert result.content == "fallback ok"
    assert len(result.warnings) == 1
