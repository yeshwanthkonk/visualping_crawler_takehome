"""Core data models used by the crawler."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CrawlStatus(str, Enum):
    QUEUED = "queued"
    FETCHING = "fetching"
    FETCHED = "fetched"
    PARSED = "parsed"
    FAILED = "failed"
    SKIPPED = "skipped"
    REDIRECTED = "redirected"


@dataclass
class CrawlResult:
    url: str
    status: CrawlStatus
    final_url: str | None = None
    status_code: int | None = None
    content_type: str | None = None
    depth: int = 0
    redirects: list[str] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveredUrl:
    url: str
    source_url: str | None = None
    depth: int = 0
    discovered_via: str | None = None
