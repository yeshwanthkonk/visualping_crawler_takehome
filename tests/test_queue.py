from visualping_crawler.queue import CrawlQueue


def test_queue_enqueues_unique_values() -> None:
    q = CrawlQueue()
    q.enqueue("https://example.com")
    q.enqueue("https://example.com")

    assert q.dequeue() == "https://example.com"
    assert q.empty() is True
