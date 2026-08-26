"""Browser-backed crawling for JavaScript-generated and network-only resources."""

from __future__ import annotations

from dataclasses import dataclass

from .config import CrawlConfig
from .extractors import extract_urls_from_content
from .models import CrawlResult, CrawlStatus
from .normalize import is_pagination_variant, is_same_origin, normalize_url
from .scanner import find_passwords_in_response


@dataclass
class BrowserResponse:
    url: str
    status_code: int
    content_type: str
    body: str
    headers: dict[str, str]


class BrowserCrawler:
    """Crawl pages while observing browser network responses."""

    def __init__(self, config: CrawlConfig) -> None:
        self.config = config
        self.passwords: set[str] = set()
        self.results: list[CrawlResult] = []
        self.max_depth_reached = 0

    def run(self) -> set[str]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise RuntimeError(
                "Browser crawling requires the optional Playwright dependency. "
                "Install it with: pip install -e .[browser]"
            ) from error

        pending = [normalize_url(self.config.start_url, self.config.start_url)]
        seen: set[str] = set()
        depths = {pending[0]: 0}

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(
                http_credentials={
                    "username": self.config.username,
                    "password": self.config.password,
                },
                user_agent=self.config.user_agent,
            )
            page = context.new_page()
            while pending and len(seen) < self.config.max_pages:
                url = pending.pop(0)
                if url in seen:
                    continue
                seen.add(url)
                depth = depths[url]
                self.max_depth_reached = max(self.max_depth_reached, depth)
                responses: list[BrowserResponse] = []

                def capture(response: object) -> None:
                    response_url = normalize_url(url, getattr(response, "url"))
                    if not response_url or not is_same_origin(self.config.start_url, response_url):
                        return
                    headers = getattr(response, "all_headers")()
                    content_type = headers.get("content-type", "").lower()
                    try:
                        body = getattr(response, "body")().decode("utf-8", errors="replace")
                    except Exception:
                        body = ""
                    responses.append(
                        BrowserResponse(
                            url=response_url,
                            status_code=getattr(response, "status"),
                            content_type=content_type,
                            body=body,
                            headers=headers,
                        )
                    )

                page.on("response", capture)
                try:
                    page.goto(url, wait_until="networkidle", timeout=30_000)
                    page_content = page.content()
                    responses.append(BrowserResponse(url, 200, "text/html", page_content, {}))
                finally:
                    page.remove_listener("response", capture)

                for response in responses:
                    response_passwords = find_passwords_in_response(
                        response.url,
                        response.headers,
                        response.body,
                    )
                    self.passwords.update(response_passwords)
                    self.results.append(
                        CrawlResult(
                            url=response.url,
                            status=CrawlStatus.PARSED,
                            final_url=response.url,
                            status_code=response.status_code,
                            content_type=response.content_type,
                            depth=depth,
                            metadata={"passwords": sorted(response_passwords)},
                        )
                    )
                    if depth >= self.config.max_depth:
                        continue
                    for discovered in extract_urls_from_content(response.content_type, response.body):
                        candidate = normalize_url(response.url, discovered)
                        if candidate and is_same_origin(self.config.start_url, candidate):
                            if (
                                not self.config.follow_pagination
                                and is_pagination_variant(response.url, candidate)
                            ):
                                continue
                            if candidate not in depths:
                                depths[candidate] = depth + 1
                                pending.append(candidate)

            context.close()
            browser.close()
        return self.passwords