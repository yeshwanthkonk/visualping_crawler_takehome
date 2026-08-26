"""Command-line entrypoint for the crawler."""

from .config import CrawlConfig
from .crawler import Crawler


def main() -> None:
    config = CrawlConfig.from_env()
    crawler = Crawler(config)
    passwords = crawler.run()

    print("Passwords found:", sorted(passwords))
    print("Pages/resources fetched:", len(crawler.results))
    print("Maximum depth reached:", crawler.max_depth_reached)
    print("Frontier exhausted:", crawler.frontier_exhausted)
    print("Reached depth limit:", crawler.reached_depth_limit)
    print("Reached page limit:", crawler.reached_page_limit)
    for result in crawler.results:
        print(result.status_code, result.url, result.content_type)


if __name__ == "__main__":
    main()