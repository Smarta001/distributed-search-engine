"""
robots.py
robots.txt Checker for the crawler.

Responsibilities:
- Fetch and parse a site's robots.txt
- Check whether our crawler is allowed to fetch a given URL
- Cache parsed robots.txt per-domain so we don't re-fetch it on every page

Uses Python's built-in urllib.robotparser, which is sufficient for
this stage (handles Allow/Disallow/User-agent rules).
"""

import urllib.robotparser
from urllib.parse import urlparse

import config


class RobotsChecker:
    def __init__(self, user_agent=None):
        self.user_agent = user_agent or config.USER_AGENT
        self._cache = {}

    def _get_parser(self, url):
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain in self._cache:
            return self._cache[domain]

        robots_url = f"{domain}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)

        try:
            rp.read()
        except Exception:
            rp = urllib.robotparser.RobotFileParser()
            rp.parse([])

        self._cache[domain] = rp
        return rp

    def can_fetch(self, url):
        try:
            rp = self._get_parser(url)
            return rp.can_fetch(self.user_agent, url)
        except Exception:
            return True

    def crawl_delay(self, url):
        rp = self._get_parser(url)
        try:
            return rp.crawl_delay(self.user_agent)
        except Exception:
            return None


if __name__ == "__main__":
    checker = RobotsChecker(user_agent="DistributedSearchEngineBot/1.0")

    test_urls = [
        "https://example.com/",
        "https://example.com/some-page",
    ]

    for url in test_urls:
        allowed = checker.can_fetch(url)
        print(f"can_fetch({url!r}) -> {allowed}")

    print("Crawl delay:", checker.crawl_delay("https://example.com/"))