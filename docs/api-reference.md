# API Reference — search-api

Base URL (local dev): `http://localhost:8000`

Interactive Swagger docs are also available at `/docs` while the service
is running.

---

## `GET /search`

Full-text search over indexed pages, using BM25 ranking via Elasticsearch,
with a Redis cache-aside layer in front.

**Query parameters**

| Param | Type | Required | Default | Notes |
|---|---|---|---|---|
| `q` | string | yes | — | Search query, min length 1 |
| `page` | int | no | 1 | 1-indexed |
| `size` | int | no | 10 | 1–50 |

**Example**
```
GET /search?q=distributed+systems&page=1&size=10
```

**Response**
```json
{
  "query": "distributed systems",
  "total_hits": 3,
  "took_ms": 12,
  "from_cache": false,
  "results": [
    {
      "url": "https://example.com/page",
      "title": "Distributed Systems 101",
      "snippet": "...a highlighted fragment around the matched term...",
      "score": 4.82
    }
  ]
}
```

- `title` and `body` are matched, with `title` weighted 3x higher.
- `snippet` is a highlighted ~160-character fragment from `body`, or a
  plain truncation if Elasticsearch didn't return a highlight.
- `from_cache: true` means this exact query/page/size combo was served
  straight from Redis without hitting Elasticsearch.
- Every call to `/search` (cache hit or miss) logs the query, latency, and
  result count to the `search_logs` Postgres table.

**Errors**
- `422` — missing `q`, or `size` outside 1–50
- `502` — Elasticsearch unreachable

---

## `GET /suggest`

Lightweight autocomplete — prefix match against indexed page titles only.

**Query parameters**

| Param | Type | Required |
|---|---|---|
| `q` | string | yes |

**Example**
```
GET /suggest?q=distri
```

**Response**
```json
{
  "query": "distri",
  "suggestions": ["Distributed Systems 101", "Distributed Search Engine"]
}
```

**Errors**
- `502` — Elasticsearch unreachable

---

## `GET /popular`

Most frequent search queries over the last 7 days, from the `search_logs`
table.

**Query parameters**

| Param | Type | Required | Default | Notes |
|---|---|---|---|---|
| `limit` | int | no | 10 | 1–50 |

**Response**
```json
{
  "popular_queries": [
    {"query": "distributed systems", "search_count": 14},
    {"query": "bm25", "search_count": 9}
  ]
}
```

**Errors**
- `502` — Postgres unreachable

---

## `GET /health`

Reports real connectivity to Elasticsearch and Redis (not just "the app
process is alive").

**Response**
```json
{"status": "ok", "elasticsearch": true, "redis": true}
```

`status` is `"degraded"` if either backend is unreachable. Note this
endpoint does **not** currently check Postgres connectivity.
