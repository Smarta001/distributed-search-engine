"""
main.py
Entry point for the crawler — ties every module together into the
actual crawl loop:

    seed URLs -> scheduler -> robots check -> download -> parse
    -> save to database -> publish to RabbitMQ -> queue new links -> repeat
"""

import time

import config
from scheduler import URLScheduler
from robots import RobotsChecker
import downloader
import parser
import database
import rabbitmq


def crawl_url(url, scheduler, robots_checker, publisher):
    """
    Process a single URL end-to-end.
    """
    if not robots_checker.can_fetch(url):
        print(f"[SKIP - robots.txt disallows] {url}")
        return False

    result = downloader.download(url)
    if not result.success:
        print(f"[FAIL - {result.error}] {url}")
        return False

    parsed = parser.parse_html(result.html, base_url=url)

    database.save_page(
        url=url,
        title=parsed["title"],
        meta_description=parsed["meta_description"],
        html=result.html,
        status_code=result.status_code,
    )

    publisher.publish_page(
        url=url,
        title=parsed["title"],
        status_code=result.status_code,
        html=result.html
    )

    print(f"[OK - {result.status_code}] {url} — {parsed['title']}")

    # Queue newly discovered links for future crawling
    for link in parsed["links"]:
        scheduler.add_url(link)

    return True


def run():
    print("Starting crawl...")
    print("Seed URLs:", config.SEED_URLS)
    print("Max pages:", config.MAX_PAGES)

    # Set up shared components
    scheduler = URLScheduler(max_pages=config.MAX_PAGES)
    robots_checker = RobotsChecker()

    database.init_db()
    print("Database ready.")

    for seed in config.SEED_URLS:
        scheduler.add_url(seed)

    pages_crawled = 0

    with rabbitmq.RabbitMQPublisher() as publisher:
        while True:
            url = scheduler.get_next_url()
            if url is None:
                break

            crawl_url(url, scheduler, robots_checker, publisher)
            pages_crawled += 1

            # Be polite — don't hammer servers with back-to-back requests
            time.sleep(config.CRAWL_DELAY)

    print(f"\nCrawl finished. Pages processed: {pages_crawled}")
    print(f"URLs discovered (visited set size): {scheduler.visited_count()}")


if __name__ == "__main__":
    run()