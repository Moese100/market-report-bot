from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

from market_report.http import HttpClient
from market_report.models import NewsItem

LOGGER = logging.getLogger(__name__)


class RssNewsProvider:
    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def fetch(
        self, feeds: list[dict[str, Any]], max_items: int
    ) -> tuple[list[NewsItem], list[str]]:
        by_feed: list[list[NewsItem]] = []
        warnings: list[str] = []
        seen: set[str] = set()
        for feed in feeds:
            feed_items: list[NewsItem] = []
            try:
                response = self.http.get(feed["url"])
                root = ET.fromstring(response.content)
                entries = root.findall(".//item")
                for entry in entries:
                    title = _text(entry, "title")
                    link = _text(entry, "link")
                    published = _text(entry, "pubDate")
                    if title and link and link not in seen:
                        seen.add(link)
                        feed_items.append(
                            NewsItem(
                                title=title.strip(),
                                url=link.strip(),
                                source=str(feed["name"]),
                                published=published.strip(),
                            )
                        )
            except Exception as exc:
                LOGGER.warning("RSS feed failed (%s): %s", feed.get("name"), exc)
                warnings.append(f"新闻源 {feed.get('name', '未知')} 暂不可用")
            by_feed.append(feed_items)
        collected: list[NewsItem] = []
        depth = 0
        while len(collected) < max_items and any(depth < len(items) for items in by_feed):
            for items in by_feed:
                if depth < len(items):
                    collected.append(items[depth])
                    if len(collected) == max_items:
                        break
            depth += 1
        return collected, warnings


def _text(parent: ET.Element, tag: str) -> str:
    child = parent.find(tag)
    return child.text if child is not None and child.text else ""
