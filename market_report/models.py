from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Quote:
    symbol: str
    name: str
    category: str
    price: float | None
    change_pct: float | None
    unit: str
    source: str
    as_of: datetime
    market_cap: float | None = None
    error: str | None = None

    @property
    def available(self) -> bool:
        return self.price is not None


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    published: str = ""


@dataclass
class MarketSnapshot:
    generated_at: datetime
    mode: str
    quotes: list[Quote] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)
    fear_greed: tuple[str, str] | None = None
    warnings: list[str] = field(default_factory=list)
