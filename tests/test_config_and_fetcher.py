import base64

import pytest
import requests

from visualping_crawler.config import CrawlConfig
from visualping_crawler.fetcher import HttpFetcher


def test_fetcher_prepares_basic_auth_for_every_request() -> None:
    try:
        config = CrawlConfig.from_env()
    except ValueError as error:
        pytest.skip(str(error))

    request = HttpFetcher(config).session.prepare_request(
        requests.Request("GET", config.start_url)
    )

    expected = base64.b64encode(
        f"{config.username}:{config.password}".encode()
    ).decode()
    assert request.headers["Authorization"] == f"Basic {expected}"


def test_config_from_env_requires_all_runtime_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("visualping_crawler.config.load_dotenv", lambda: None)
    monkeypatch.setenv("VISUALPING_START_URL", "https://configured.invalid/")
    monkeypatch.setenv("VISUALPING_USERNAME", "user")
    monkeypatch.delenv("VISUALPING_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="VISUALPING_PASSWORD"):
        CrawlConfig.from_env()