"""Authenticated HTTP fetching for crawl resources."""

from __future__ import annotations

import requests

from .config import CrawlConfig


class HttpFetcher:
    """HTTP client that sends the configured Basic Auth on every request."""

    def __init__(self, config: CrawlConfig) -> None:
        self.session = requests.Session()
        self.session.auth = (config.username, config.password)
        self.session.headers.update({"User-Agent": config.user_agent})
        self.follow_redirects = config.follow_redirects

    def get(self, url: str, *, timeout: float = 30.0) -> requests.Response:
        """Fetch a URL with Basic Auth applied by the session."""
        return self.session.get(
            url,
            allow_redirects=self.follow_redirects,
            timeout=timeout,
        )