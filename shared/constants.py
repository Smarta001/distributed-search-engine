"""
Central place for names that must match exactly across services.
If the crawler and indexer disagree on a queue name, messages silently
vanish into a queue nobody is listening to — so it all lives here once.
"""

# RabbitMQ
CRAWL_QUEUE = "crawl_results_queue"          # crawler -> indexer
CRAWL_EXCHANGE = "crawl_exchange"
CRAWL_ROUTING_KEY = "crawl.page.crawled"

DEAD_LETTER_QUEUE = "crawl_results_dlq"      # failed indexing attempts land here
DEAD_LETTER_EXCHANGE = "crawl_dlx"

# Elasticsearch
PAGES_INDEX = "pages"

# Redis
SEARCH_CACHE_PREFIX = "search:"
SEARCH_CACHE_TTL_SECONDS = 300  # 5 minutes

# Misc
MAX_RETRY_ATTEMPTS = 3
