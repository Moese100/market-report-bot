from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote

from market_report.http import HttpClient
from market_report.models import Quote

LOGGER = logging.getLogger(__name__)


class MarketDataProvider:
    def __init__(self, http: HttpClient, now: datetime) -> None:
        self.http = http
        self.now = now

    def fetch_crypto(self, assets: list[dict[str, Any]]) -> tuple[list[Quote], list[str]]:
        warnings: list[str] = []
        try:
            ids = ",".join(str(item["coingecko_id"]) for item in assets)
            response = self.http.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": ids,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                },
            )
            payload = response.json()
            quotes = []
            for item in assets:
                data = payload.get(item["coingecko_id"], {})
                price = _float_or_none(data.get("usd"))
                if price is None:
                    raise ValueError(f"CoinGecko 缺少 {item['symbol']} 价格")
                quotes.append(
                    Quote(
                        symbol=item["symbol"],
                        name=item["name"],
                        category="crypto",
                        price=price,
                        change_pct=_float_or_none(data.get("usd_24h_change")),
                        market_cap=_float_or_none(data.get("usd_market_cap")),
                        unit="USD",
                        source="CoinGecko",
                        as_of=self.now,
                    )
                )
            return quotes, warnings
        except Exception as exc:
            LOGGER.warning("CoinGecko failed, trying Binance: %s", exc)
            warnings.append(f"CoinGecko 不可用，已切换 Binance：{_short_error(exc)}")
            return self._fetch_crypto_binance(assets, warnings)

    def _fetch_crypto_binance(
        self, assets: list[dict[str, Any]], warnings: list[str]
    ) -> tuple[list[Quote], list[str]]:
        quotes: list[Quote] = []
        for item in assets:
            try:
                response = self.http.get(
                    "https://api.binance.com/api/v3/ticker/24hr",
                    params={"symbol": item["binance_symbol"]},
                )
                data = response.json()
                quotes.append(
                    Quote(
                        symbol=item["symbol"],
                        name=item["name"],
                        category="crypto",
                        price=float(data["lastPrice"]),
                        change_pct=float(data["priceChangePercent"]),
                        market_cap=None,
                        unit="USD",
                        source="Binance",
                        as_of=self.now,
                    )
                )
            except Exception as exc:
                warnings.append(f"{item['symbol']} 两个数据源均失败：{_short_error(exc)}")
                quotes.append(_unavailable(item, "crypto", self.now, exc))
        return quotes, warnings

    def fetch_traditional(
        self, assets: list[dict[str, Any]], category: str
    ) -> tuple[list[Quote], list[str]]:
        quotes: list[Quote] = []
        warnings: list[str] = []
        for item in assets:
            try:
                price, change = self._yahoo(item["yahoo_symbol"])
                source = "Yahoo Finance"
            except Exception as primary_exc:
                LOGGER.warning("Yahoo failed for %s: %s", item["symbol"], primary_exc)
                try:
                    price, change = self._stooq(item["stooq_symbol"])
                    source = "Stooq"
                    warnings.append(f"{item['name']} 已切换到 Stooq")
                except Exception as fallback_exc:
                    warnings.append(
                        f"{item['name']} 两个数据源均失败：{_short_error(fallback_exc)}"
                    )
                    quotes.append(_unavailable(item, category, self.now, fallback_exc))
                    continue
            quotes.append(
                Quote(
                    symbol=item["symbol"],
                    name=item["name"],
                    category=category,
                    price=price,
                    change_pct=change,
                    market_cap=None,
                    unit=item.get("unit", "USD"),
                    source=source,
                    as_of=self.now,
                )
            )
        return quotes, warnings

    def fetch_fear_greed(self) -> tuple[str, str] | None:
        try:
            data = self.http.get("https://api.alternative.me/fng/").json()["data"][0]
            return str(data["value"]), str(data["value_classification"])
        except Exception as exc:
            LOGGER.warning("Fear and Greed fetch failed: %s", exc)
            return None

    def _yahoo(self, symbol: str) -> tuple[float, float | None]:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='')}"
        response = self.http.get(url, params={"interval": "1d", "range": "5d"})
        result = response.json().get("chart", {}).get("result") or []
        if not result:
            raise ValueError("Yahoo 返回空结果")
        meta = result[0].get("meta", {})
        price = _float_or_none(meta.get("regularMarketPrice"))
        previous = _float_or_none(meta.get("chartPreviousClose"))
        if price is None:
            closes = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
            values = [float(value) for value in closes if value is not None]
            price = values[-1] if values else None
            previous = values[-2] if len(values) > 1 else previous
        if price is None:
            raise ValueError("Yahoo 缺少价格")
        change = ((price - previous) / previous * 100) if previous else None
        return price, change

    def _stooq(self, symbol: str) -> tuple[float, float | None]:
        response = self.http.get(
            "https://stooq.com/q/d/l/", params={"s": symbol, "i": "d"}
        )
        if "No data" in response.text:
            raise ValueError("Stooq 无数据")
        rows = list(csv.DictReader(io.StringIO(response.text)))
        closes = [float(row["Close"]) for row in rows if row.get("Close") not in (None, "", "N/D")]
        if not closes:
            raise ValueError("Stooq 缺少收盘价")
        price = closes[-1]
        change = ((price - closes[-2]) / closes[-2] * 100) if len(closes) > 1 else None
        return price, change


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _short_error(exc: Exception) -> str:
    text = str(exc).replace("\n", " ").strip()
    return text[:160] or exc.__class__.__name__


def _unavailable(
    item: dict[str, Any], category: str, now: datetime, exc: Exception
) -> Quote:
    return Quote(
        symbol=item["symbol"],
        name=item["name"],
        category=category,
        price=None,
        change_pct=None,
        market_cap=None,
        unit=item.get("unit", "USD"),
        source="不可用",
        as_of=now,
        error=_short_error(exc),
    )
