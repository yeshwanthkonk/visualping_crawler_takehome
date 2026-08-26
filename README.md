# VisualPing Crawler

This repository is intended for a browser-aware crawl implementation that discovers reachable pages and resources from a homepage, with the goal of finding password-bearing resources without assuming HTML-only links.

## Project structure

- `visualping_crawler/` contains the crawl engine and supporting modules.
- `tests/` contains unit and integration tests for URL handling, extraction logic, and crawl behavior.

## Planned responsibilities

- fetch and normalize URLs
- extract references from HTML, CSS, JS, JSON, and SVG
- track crawl state and deduplicate work
- optionally use a browser for dynamic-content navigation
- evaluate crawl completion and report results

This is intentionally a minimal scaffold for the design review stage.

## Local development

Create and activate the virtual environment on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . pytest
python -m pytest -q
```

Keep the challenge homepage and credentials outside the repository. The implementation should receive them through environment variables or protected command-line input; do not commit them to source files or fixtures.

To use a local `.env` file, copy `.env.example` to `.env` and replace the placeholder values. The configuration loader reads it automatically, and `.env` is excluded by `.gitignore`:

```powershell
Copy-Item .env.example .env
```

Never commit `.env` or print its contents. Explicit environment variables already set in PowerShell take precedence over values from the file.

For a PowerShell session, set the challenge values before starting the crawler:

```powershell
$env:VISUALPING_START_URL = "https://example.invalid/"
$env:VISUALPING_USERNAME = "your-username"
$env:VISUALPING_PASSWORD = "your-password"
```

Load them with `CrawlConfig.from_env()`. `HttpFetcher` uses one authenticated `requests.Session`, so every HTTP request made through the crawler carries the configured Basic Auth credentials. Do not print the environment values or include them in logs.

Numeric pagination endpoints are not followed by default because an endpoint such as `/report/?page=100000000000000` may accept arbitrary values and create an unbounded crawl. Enable `config.follow_pagination = True` only with a deliberate `max_pages` bound when pagination itself is required.

For browser-backed crawling, install Playwright and its Chromium browser:

```powershell
python -m pip install -e ".[browser]"
python -m playwright install chromium
```

Then enable it before creating the crawler:

```python
config.use_browser = True
```

The browser context sends the configured HTTP Basic Auth credentials on its requests and captures same-origin network responses in addition to rendered page content.
