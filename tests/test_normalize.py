from visualping_crawler.normalize import is_pagination_variant, is_same_origin, normalize_url


def test_normalize_url_resolves_relative_links() -> None:
    base = "https://example.com/a/page.html"
    result = normalize_url(base, "../b/other.html?x=1")
    assert result == "https://example.com/b/other.html?x=1"


def test_same_origin_rejects_different_hosts() -> None:
    base = "https://example.com/page"
    candidate = "https://other.com/page"
    assert not is_same_origin(base, candidate)


def test_same_origin_accepts_same_host_and_port() -> None:
    base = "https://example.com/page"
    candidate = "https://example.com/other"
    assert is_same_origin(base, candidate)


def test_pagination_variants_do_not_add_logical_depth() -> None:
    assert is_pagination_variant(
        "http://example.com/report/?page=1000",
        "http://example.com/report/?page=1001",
    )
