from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HttpClient:
    def __init__(self, timeout: int = 15, retries: int = 3) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update(
            {
                "User-Agent": "market-report-bot/2.0 (+https://github.com/PPPatY/market-report-bot)",
                "Accept": "application/json,text/plain,application/rss+xml,*/*",
            }
        )

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.post(url, **kwargs)
        response.raise_for_status()
        return response
