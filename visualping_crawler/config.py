"""Configuration values for crawl policy and runtime behavior."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class CrawlConfig:
    """Base crawler configuration."""

    start_url: str
    username: str = ""
    password: str = ""
    max_depth: int = 100
    max_pages: int = 500
    allowed_schemes: tuple[str, ...] = ("http", "https")
    same_origin_only: bool = True
    follow_pagination: bool = False
    follow_redirects: bool = True
    use_browser: bool = False
    allowed_extensions: tuple[str, ...] = (
        ".html",
        ".htm",
        ".css",
        ".js",
        ".json",
        ".svg",
        ".txt",
        ".xml",
    )
    exclude_paths: tuple[str, ...] = field(default_factory=tuple)
    user_agent: str = "visualping-crawler/0.1.0"

    @classmethod
    def from_env(cls) -> "CrawlConfig":
        """Build crawl configuration from protected runtime environment values."""
        load_dotenv()
        start_url = os.environ.get("VISUALPING_START_URL", "").strip()
        username = os.environ.get("VISUALPING_USERNAME", "")
        password = os.environ.get("VISUALPING_PASSWORD", "")
        missing = [
            name
            for name, value in (
                ("VISUALPING_START_URL", start_url),
                ("VISUALPING_USERNAME", username),
                ("VISUALPING_PASSWORD", password),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return cls(start_url=start_url, username=username, password=password)

    def __post_init__(self) -> None:
        if not self.start_url:
            raise ValueError("start_url must not be empty")
