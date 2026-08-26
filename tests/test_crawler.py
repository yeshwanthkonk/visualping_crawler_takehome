from types import SimpleNamespace

from visualping_crawler.config import CrawlConfig
from visualping_crawler.crawler import Crawler
from visualping_crawler.extractors import extract_html_urls, extract_urls_from_content
from visualping_crawler.scanner import find_passwords, find_passwords_in_response


def test_crawler_follows_same_origin_resource_and_finds_password() -> None:
    config = CrawlConfig(
        start_url="https://example.com/",
        username="user",
        password="password",
    )
    crawler = Crawler(config)
    responses = {
        "https://example.com/": SimpleNamespace(
            url="https://example.com/",
            status_code=200,
            headers={"Content-Type": "text/html"},
            text='<a href="/resource.json">resource</a>',
            history=[],
        ),
        "https://example.com/resource.json": SimpleNamespace(
            url="https://example.com/resource.json",
            status_code=200,
            headers={"Content-Type": "application/json"},
            text='{"value":"VISUALPING{0123456789abcdef}"}',
            history=[],
        ),
    }
    crawler.fetcher.get = responses.__getitem__

    assert crawler.run() == {"VISUALPING{0123456789abcdef}"}
    assert set(responses) == {result.url for result in crawler.results}
    assert crawler.max_depth_reached == 1
    assert crawler.frontier_exhausted is True
    assert crawler.reached_depth_limit is False
    assert crawler.reached_page_limit is False


def test_crawler_does_not_enumerate_unbounded_pagination_by_default() -> None:
    config = CrawlConfig(
        start_url="https://example.com/report/?page=1",
        username="user",
        password="password",
        max_pages=10,
    )
    crawler = Crawler(config)
    crawler.fetcher.get = lambda url: SimpleNamespace(
        url=url,
        status_code=200,
        headers={"Content-Type": "text/html"},
        text='<a href="/report/?page=2">next</a>',
        history=[],
    )

    crawler.run()

    assert [result.url for result in crawler.results] == [
        "https://example.com/report/?page=1"
    ]


def test_crawler_starts_with_normalized_url() -> None:
    config = CrawlConfig(
        start_url="https://example.com:443/",
        username="user",
        password="password",
    )
    crawler = Crawler(config)

    assert crawler.queue.dequeue() == "https://example.com/"


def test_html_extractor_finds_inline_css_and_javascript_urls() -> None:
    html = """
    <style>@import '/styles.css';</style>
    <script>fetch('/api/data.json')</script>
    <meta http-equiv="refresh" content="0; url='/refresh.html'">
    <button onclick="window.location='/clicked.html'" style="background: url('/image.png')">go</button>
    <a href='/page.html'>page</a>
    """
    assert set(extract_html_urls(html)) >= {
        "/styles.css",
        "/api/data.json",
        "/refresh.html",
        "/clicked.html",
        "/image.png",
        "/page.html",
    }


def test_html_extractor_finds_extended_resource_attributes() -> None:
    html = """
    <img srcset="/small.png 1x, /large.png 2x">
    <video poster="/poster.jpg"></video>
    <link rel="manifest" href="/manifest.json">
    <div data-route="/dynamic-route"></div>
    """
    assert set(extract_html_urls(html)) >= {
        "/small.png",
        "/large.png",
        "/poster.jpg",
        "/manifest.json",
        "/dynamic-route",
    }


def test_json_extractor_finds_nested_resource_urls() -> None:
    raw = '{"nested": {"asset": "/assets/data.txt"}}'
    assert extract_urls_from_content("application/json", raw) == ["/assets/data.txt"]


def test_scanner_excludes_documented_example_password() -> None:
    content = "VISUALPING{0000deadbeef0000} VISUALPING{0123456789abcdef}"
    assert find_passwords(content) == {"VISUALPING{0123456789abcdef}"}


def test_scanner_checks_response_url_headers_and_bytes() -> None:
    password = "VISUALPING{fedcba9876543210}"
    assert find_passwords_in_response(
        f"https://example.com/{password}",
        {"X-Password": password},
        b"binary prefix " + password.encode("ascii"),
    ) == {password}