"""
scheduler.py
URL Scheduler for the crawler.

Responsibilities:
- Maintain a queue of URLs waiting to be crawled
- Prevent duplicate URLs from being queued/crawled twice
- Track which URLs have already been visited

Thread-safe so it can be shared across multiple worker threads
once you add multithreading (Milestone 2).
"""

import threading
from collections import deque
from urllib.parse import urlparse, urlunparse


class URLScheduler:
    def __init__(self, max_pages=None):
        self._queue = deque()
        self._visited = set()
        self._lock = threading.Lock()
        self._max_pages = max_pages
        self._dispatched_count = 0

    @staticmethod
    def normalize_url(url):
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") or "/"
        normalized = urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
        return normalized

    def add_url(self, url):
        if not url:
            return False

        normalized = self.normalize_url(url)

        with self._lock:
            if normalized in self._visited:
                return False

            if self._max_pages is not None and self._dispatched_count >= self._max_pages:
                return False

            self._visited.add(normalized)
            self._queue.append(normalized)
            return True

    def get_next_url(self):
        with self._lock:
            if self._max_pages is not None and self._dispatched_count >= self._max_pages:
                return None

            if not self._queue:
                return None

            url = self._queue.popleft()
            self._dispatched_count += 1
            return url

    def is_visited(self, url):
        normalized = self.normalize_url(url)
        with self._lock:
            return normalized in self._visited

    def has_pending(self):
        with self._lock:
            return len(self._queue) > 0

    def queue_size(self):
        with self._lock:
            return len(self._queue)

    def visited_count(self):
        with self._lock:
            return len(self._visited)


if __name__ == "__main__":
    scheduler = URLScheduler(max_pages=5)

    urls = [
        "https://Example.com/Page/",
        "https://example.com/page",
        "https://example.com/about",
        "https://example.com/about#team",
        "https://example.com/contact",
    ]

    for u in urls:
        added = scheduler.add_url(u)
        print(f"add_url({u!r}) -> {added}")

    print("Queue size:", scheduler.queue_size())
    print("Visited count:", scheduler.visited_count())

    print("\nDraining queue:")
    while scheduler.has_pending():
        print(" ->", scheduler.get_next_url())

    print("\nis_visited check:", scheduler.is_visited("https://example.com/about"))