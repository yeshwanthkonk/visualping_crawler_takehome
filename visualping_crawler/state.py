"""State tracking for crawl progress."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class CrawlState:
    """Minimal state store for deduplication and final completion checks."""

    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.failed: set[str] = set()
        self.skipped: set[str] = set()
        self.metadata: dict[str, dict[str, Any]] = defaultdict(dict)

    def mark_seen(self, url: str) -> bool:
        if url in self.seen:
            return False
        self.seen.add(url)
        return True

    def mark_failed(self, url: str) -> None:
        self.failed.add(url)

    def mark_skipped(self, url: str) -> None:
        self.skipped.add(url)

    def record(self, url: str, **kwargs: Any) -> None:
        self.metadata[url].update(kwargs)
