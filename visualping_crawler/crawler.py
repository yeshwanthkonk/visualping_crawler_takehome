"""Primary crawler orchestration entrypoint."""

from __future__ import annotations

from .config import CrawlConfig
from .extractors import extract_urls_from_content
from .fetcher import HttpFetcher
from .models import CrawlResult, CrawlStatus
from .normalize import is_pagination_variant, is_same_origin, normalize_url
from .queue import CrawlQueue
from .scanner import find_passwords_in_response
from .state import CrawlState


class Crawler:
    def __init__(self, config: CrawlConfig) -> None:
        self.config = config
        self.fetcher = HttpFetcher(config)
        self.queue = CrawlQueue()
        self.state = CrawlState()
        self.passwords: set[str] = set()
        self.results: list[CrawlResult] = []
        self.max_depth_reached = 0
        self.reached_depth_limit = False
        self.reached_page_limit = False
        self.frontier_exhausted = False
        self.start_url = normalize_url(config.start_url, config.start_url)
        self.queue.enqueue(self.start_url)

    def run(self) -> set[str]:
        """Crawl queued resources and return all discovered passwords."""
        if self.config.use_browser:
            from .browser_runner import BrowserCrawler

            browser_crawler = BrowserCrawler(self.config)
            self.passwords = browser_crawler.run()
            self.results = browser_crawler.results
            self.max_depth_reached = browser_crawler.max_depth_reached
            self.frontier_exhausted = True
            return self.passwords

        processed = 0
        depths = {self.start_url: 0}
        while not self.queue.empty() and processed < self.config.max_pages:
            url = self.queue.dequeue()
            if url is None:
                break
            if not self.state.mark_seen(url):
                continue
            depth = depths.get(url, 0)
            self.max_depth_reached = max(self.max_depth_reached, depth)
            self.reached_depth_limit = self.max_depth_reached >= self.config.max_depth
            try:
                response = self.fetcher.get(url)
                content_type = response.headers.get("Content-Type", "").lower()
                body = response.text
                response_passwords = find_passwords_in_response(
                    response.url,
                    dict(response.headers),
                    body,
                )
                self.passwords.update(response_passwords)
                self.results.append(
                    CrawlResult(
                        url=url,
                        status=CrawlStatus.PARSED,
                        final_url=response.url,
                        status_code=response.status_code,
                        content_type=content_type,
                        depth=depth,
                        redirects=[item.url for item in response.history],
                        metadata={"passwords": sorted(response_passwords)},
                    )
                )
                if depth >= self.config.max_depth:
                    processed += 1
                    continue
                for discovered in extract_urls_from_content(content_type, body):
                    candidate = normalize_url(response.url, discovered)
                    if not candidate:
                        continue
                    if not is_same_origin(self.config.start_url, candidate):
                        continue
                    if (
                        not self.config.follow_pagination
                        and is_pagination_variant(response.url, candidate)
                    ):
                        continue
                    if candidate not in depths:
                        next_depth = depth if is_pagination_variant(response.url, candidate) else depth + 1
                        depths[candidate] = next_depth
                        self.queue.enqueue(candidate)
            except Exception as error:
                self.state.mark_failed(url)
                self.results.append(
                    CrawlResult(url=url, status=CrawlStatus.FAILED, depth=depth, error=str(error))
                )
            processed += 1
        self.reached_page_limit = processed >= self.config.max_pages and not self.queue.empty()
        self.frontier_exhausted = self.queue.empty()
        return self.passwords
