"""Frontier management for URLs to crawl."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class CrawlQueue:
    """A small queue-based frontier suitable for initial implementation."""

    items: deque[str] = field(default_factory=deque)

    def enqueue(self, url: str) -> None:
        if url and url not in self.items:
            self.items.append(url)

    def dequeue(self) -> str | None:
        if not self.items:
            return None
        return self.items.popleft()

    def empty(self) -> bool:
        return len(self.items) == 0
