"""URL normalization helpers."""

from __future__ import annotations

from urllib.parse import parse_qsl, urljoin, urlparse, urlunparse


def normalize_url(base_url: str, url: str) -> str:
    """Resolve a URL relative to a base and canonicalize it for dedupe."""
    resolved = urljoin(base_url, url)
    parsed = urlparse(resolved)

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        return ""
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    netloc = hostname
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{netloc}:{port}"
    path = parsed.path or "/"
    query = parsed.query

    # Normalize a few common path variants without over-normalizing application semantics.
    if "//" in path:
        path = "/".join(part for part in path.split("/") if part)
        path = "/" + path

    normalized = urlunparse((scheme, netloc, path, "", query, ""))
    return normalized


def is_same_origin(base_url: str, candidate_url: str) -> bool:
    """Return True when candidate is same-origin as the base URL."""
    base = urlparse(base_url)
    candidate = urlparse(candidate_url)

    return (
        base.scheme.lower() == candidate.scheme.lower()
        and base.hostname is not None
        and candidate.hostname is not None
        and base.hostname.lower() == candidate.hostname.lower()
        and (base.port or (443 if base.scheme.lower() == "https" else 80))
        == (candidate.port or (443 if candidate.scheme.lower() == "https" else 80))
    )


def is_pagination_variant(current_url: str, candidate_url: str) -> bool:
    """Return True when two URLs differ only by a numeric page query value."""
    current = urlparse(current_url)
    candidate = urlparse(candidate_url)
    if (current.scheme, current.netloc, current.path) != (
        candidate.scheme,
        candidate.netloc,
        candidate.path,
    ):
        return False

    current_query = parse_qsl(current.query, keep_blank_values=True)
    candidate_query = parse_qsl(candidate.query, keep_blank_values=True)
    current_pages = [value for key, value in current_query if key.lower() == "page"]
    candidate_pages = [value for key, value in candidate_query if key.lower() == "page"]
    if len(current_pages) != 1 or len(candidate_pages) != 1:
        return False
    if not current_pages[0].isdigit() or not candidate_pages[0].isdigit():
        return False
    without_page = lambda query: [(key, value) for key, value in query if key.lower() != "page"]
    return without_page(current_query) == without_page(candidate_query)
