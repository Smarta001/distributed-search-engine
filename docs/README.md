# Documentation

Start here, then jump to whichever page you need.

| Page | What's in it |
|---|---|
| [architecture.md](./architecture.md) | How the services fit together, and why |
| [setup.md](./setup.md) | Getting the whole stack running locally |
| [api-reference.md](./api-reference.md) | search-api endpoints, request/response shapes |
| [testing.md](./testing.md) | Running the test suite |
| [troubleshooting.md](./troubleshooting.md) | Fixes for problems we've actually hit |

## Project status

| Component | Status | Owner |
|---|---|---|
| Crawler | ✅ Working | Friend |
| RabbitMQ | ✅ Working | (shared infra) |
| Indexer | ✅ Working | Smarta |
| Elasticsearch | ✅ Working | (shared infra) |
| Redis | ✅ Working | Smarta |
| search-api | ✅ Working | Smarta |
| PostgreSQL | ✅ Working | Friend (pages table) + Smarta (search_logs table) |
| Docker Compose | ✅ Working | Friend |
| Tests | ✅ Working (43 tests: 31 unit, 12 integration) | Smarta |
| Kubernetes | ⏳ Not started | — |
| Frontend | ⏳ Not started | — |

## Known open item

`shared/schemas.py`'s `CrawledPage` model still describes a heavier message
shape (`html`, `content_hash` inline) than what the crawler actually
publishes to RabbitMQ (`{url, title, status}` — see
[architecture.md](./architecture.md#message-contract-mismatch) for details).
The real system works because the indexer's deployed code has already
diverged from this model to match the crawler. This should get reconciled
so the code in the repo matches what's actually running — see the
"Message contract mismatch" section in architecture.md before touching
`indexer/consumer.py` or `shared/schemas.py`.
