# Architecture

## Overview

```
                    USER
                     │
              React Frontend        (not built yet)
                     │
             Search API (FastAPI)
                     │
          ┌──────────┴──────────┐
          │                     │
      Redis Cache         Elasticsearch
          │                     │
          └──────────┬──────────┘
                     │
                Indexing Service
                     ▲
                RabbitMQ Queue
                     ▲
                Web Crawler
                     │
                PostgreSQL
                     │
                 Internet
```

## Services

### Crawler (`crawler/`)
Downloads pages, respects `robots.txt`, saves the full page (URL, title,
meta description, raw HTML, status code) to PostgreSQL, and publishes a
small "a page was crawled" notification to RabbitMQ.

Key files: `scheduler.py` (what to crawl next), `downloader.py` (HTTP
fetching + retries), `parser.py` (link/metadata extraction), `robots.py`
(robots.txt compliance), `database.py` (Postgres writes), `rabbitmq.py`
(publishes notifications).

### RabbitMQ
Decouples the crawler from the indexer. The crawler publishes to the
**default exchange**, using the queue name directly as the routing key —
this is RabbitMQ's built-in shortcut where messages route straight to a
queue of the same name, no separate exchange declaration needed.

Queue name: `crawl_results_queue` (must match on both the crawler's
`RABBITMQ_QUEUE` env var and the indexer's queue-declare call — see
"Message contract mismatch" below for why this matters).

### Indexer (`indexer/`)
Consumes notifications from RabbitMQ, fetches the full page record from
PostgreSQL by URL, strips HTML down to plain text, runs it through spaCy
for lemmatization and keyword extraction, and indexes the result into
Elasticsearch.

Key files: `consumer.py` (RabbitMQ consumer loop), `text_processor.py`
(HTML → clean text → keywords), `es_client.py` (Elasticsearch index
creation with an explicit BM25 similarity mapping + document indexing).

**Requires the `en_core_web_sm` spaCy model** to be installed separately
from the `spacy` package itself — see
[troubleshooting.md](./troubleshooting.md#spacy-model-not-found).

### Elasticsearch
Stores the searchable `pages` index. The mapping explicitly configures
BM25 similarity (`k1=1.2`, `b=0.75` — Elasticsearch's defaults, set
explicitly rather than implicitly so they're documented and tunable) on
the `title` and `body` fields.

### Redis
Cache-aside layer in front of Elasticsearch. Cache keys are built from the
normalized query + page + size (e.g. `search:java:p1:s10`), with a 5-minute
TTL. If Redis is unreachable, search-api degrades gracefully — it just
skips the cache and queries Elasticsearch directly every time, rather than
crashing.

### search-api (`search-api/`)
FastAPI service exposing `/search`, `/suggest`, `/popular`, `/health`. See
[api-reference.md](./api-reference.md) for full endpoint details. Also
owns a `search_logs` Postgres table (separate from the crawler's `pages`
table) that it creates itself on startup, used to power `/popular`.

### PostgreSQL
Two tables, owned by two different services:
- `pages` (crawler) — `id, url, title, meta_description, html, status_code, crawled_at`
- `search_logs` (search-api) — `id, query, latency_ms, result_count, logged_at`

## Message contract mismatch

This is worth understanding if you touch `indexer/consumer.py` or
`shared/schemas.py`.

The crawler's `rabbitmq.py` publishes a **small** message per page:
```json
{"url": "...", "title": "...", "status": 200}
```
It deliberately does *not* include the raw HTML — the comment in
`rabbitmq.py` explains the indexer is expected to fetch the full record
(including HTML) from PostgreSQL by URL instead of carrying it through the
queue. This keeps queue messages small.

`shared/schemas.py` still defines a `CrawledPage` model matching an
earlier, heavier design (expects `html` and `content_hash` directly in the
message). This was never reconciled after the crawler's real design became
clear. In practice, the deployed indexer works — which means its actual
code has already diverged from what's checked into `shared/` in this repo
to match the crawler's real lightweight format and pull HTML from Postgres.

**Before extending the indexer or `shared/schemas.py` further**, this
should get reconciled properly: either update `CrawledPage` to match the
real `{url, title, status}` shape and add a Postgres-read step to
`indexer/consumer.py`, or pull the actual working indexer code back into
this repo so `shared/` reflects reality. Right now there are effectively
two versions of "what the indexer expects" — the deployed one (working)
and the one described in `shared/schemas.py` (stale).
