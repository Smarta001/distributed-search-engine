"""
config.py
Centralized configuration for the crawler module.

All values can be overridden via environment variables, which lets the
same code run both on your local machine and inside Docker/Kubernetes
without editing this file.
"""

import os


# ---------------------------------------------------------------------------
# PostgreSQL configuration
# ---------------------------------------------------------------------------
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DB = os.getenv("POSTGRES_DB", "search_engine")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

POSTGRES_DSN = (
    f"dbname={POSTGRES_DB} user={POSTGRES_USER} "
    f"password={POSTGRES_PASSWORD} host={POSTGRES_HOST} port={POSTGRES_PORT}"
)


# ---------------------------------------------------------------------------
# RabbitMQ configuration
# ---------------------------------------------------------------------------
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "crawled_pages")


# ---------------------------------------------------------------------------
# Crawler behavior
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 10))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
NUM_WORKER_THREADS = int(os.getenv("NUM_WORKER_THREADS", 5))
MAX_PAGES = int(os.getenv("MAX_PAGES", 500))
CRAWL_DELAY = float(os.getenv("CRAWL_DELAY", 1.0))

USER_AGENT = os.getenv(
    "USER_AGENT", "DistributedSearchEngineBot/1.0 (+https://example.com/bot)"
)


# ---------------------------------------------------------------------------
# Seed URLs — where the crawl starts (Updated with broad default seeds)
# ---------------------------------------------------------------------------
_default_seeds = (
    "https://en.wikipedia.org/wiki/Main_Page,"
    "https://news.ycombinator.com/,"
    "https://www.bbc.com/news,"
    "https://github.com/trending,"
    "https://www.geeksforgeeks.org/,"
    "https://stackoverflow.com/,"
    "https://techcrunch.com/"
)
SEED_URLS = [
    url.strip()
    for url in os.getenv("SEED_URLS", _default_seeds).split(",")
    if url.strip()
]


if __name__ == "__main__":
    print("Postgres DSN:", POSTGRES_DSN)
    print("RabbitMQ:", f"{RABBITMQ_HOST}:{RABBITMQ_PORT}", "queue:", RABBITMQ_QUEUE)
    print("Seed URLs:", SEED_URLS)
    print("Worker threads:", NUM_WORKER_THREADS, "| Max pages:", MAX_PAGES)