"""URL extraction helpers for HTML, CSS, JS, and related content."""

from __future__ import annotations

import re
import json
from html.parser import HTMLParser


class _HtmlUrlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []
        self.inline_css: list[str] = []
        self.inline_js: list[str] = []
        self._active_text: list[str] | None = None
        self._active_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = {name.lower(): value for name, value in attrs if value}
        for name, value in attrs:
            name = name.lower()
            if name in {"href", "src", "action", "data", "poster", "manifest", "cite", "longdesc", "ping"} and value:
                self.urls.extend(value.split() if name in {"srcset", "ping"} else [value])
            elif name == "srcset" and value:
                self.urls.extend(item.split()[0] for item in value.split(",") if item.split())
            elif name == "style" and value:
                self.inline_css.append(value)
            elif name.startswith("on") and value:
                self.inline_js.append(value)
            elif name.startswith("data-") and value and value.startswith(("/", "./", "../", "http://", "https://")):
                self.urls.append(value)
        if attributes.get("http-equiv", "").lower() == "refresh":
            refresh = attributes.get("content", "")
            match = re.search(r"url\s*=\s*[\"']?([^\"'\s]+)", refresh, re.IGNORECASE)
            if match:
                self.urls.append(match.group(1))
        if tag in {"script", "style"}:
            self._active_tag = tag
            self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_text is not None:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == self._active_tag and self._active_text is not None:
            content = "".join(self._active_text)
            if self._active_tag == "script":
                self.inline_js.append(content)
            else:
                self.inline_css.append(content)
            self._active_tag = None
            self._active_text = None


_CSS_URL_RE = re.compile(r"url\(\s*[\"']?([^\"')\s]+)", re.IGNORECASE)
_CSS_IMPORT_RE = re.compile(r"@import\s*[\"']([^\"']+)", re.IGNORECASE)
_JS_URL_RE = re.compile(
    r"(?:fetch|axios\.(?:get|post|put|delete)|import)\s*\(\s*[\"'`]([^\"'`]+)",
    re.IGNORECASE,
)
_JSON_URL_RE = re.compile(r"[\"'](?:href|src|url|path|endpoint)[\"']\s*:\s*[\"']([^\"']+)", re.IGNORECASE)


def extract_html_urls(html: str) -> list[str]:
    parser = _HtmlUrlParser()
    parser.feed(html)
    urls = list(parser.urls)
    for css in parser.inline_css:
        urls.extend(extract_css_urls(css))
    for js in parser.inline_js:
        urls.extend(extract_js_urls(js))
    return urls


def extract_css_urls(css: str) -> list[str]:
    return _CSS_URL_RE.findall(css) + _CSS_IMPORT_RE.findall(css)


def extract_js_urls(js: str) -> list[str]:
    urls = _JS_URL_RE.findall(js)
    urls.extend(
        value
        for value in re.findall(r"[\"'`]([^\"'`]+)[\"'`]", js)
        if value.startswith(("/", "./", "../", "http://", "https://"))
    )
    return urls


def extract_svg_urls(svg: str) -> list[str]:
    return extract_html_urls(svg)


def extract_urls_from_content(content_type: str | None, raw: str) -> list[str]:
    """Dispatch content extraction based on content type."""
    if not raw:
        return []

    if content_type and "html" in content_type:
        return extract_html_urls(raw)
    if content_type and "css" in content_type:
        return extract_css_urls(raw)
    if content_type and "svg" in content_type:
        return extract_svg_urls(raw)
    if content_type and "json" in content_type:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return _JSON_URL_RE.findall(raw)
        values: list[str] = []

        def collect(value: object) -> None:
            if isinstance(value, dict):
                for item in value.values():
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)
            elif isinstance(value, str) and value.startswith(("/", "./", "../", "http://", "https://")):
                values.append(value)

        collect(parsed)
        return values
    if content_type and ("javascript" in content_type or "ecmascript" in content_type):
        return extract_js_urls(raw)
    return []
