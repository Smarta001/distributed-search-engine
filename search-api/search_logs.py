"""
Search logs table — separate from the crawler's `pages` table, but lives in
the same Postgres database. Owns its own table creation so search-api can
be stood up independently of the crawler/indexer.

Table shape matches the README's "Search Logs" spec:
    id, query, latency, results
"""

from __future__ import annotations

import psycopg2
import psycopg2.extras

from shared.config import get_settings
from shared.logger import get_logger

logger = get_logger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    latency_ms INTEGER NOT NULL,
    result_count INTEGER NOT NULL,
    logged_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

INSERT_LOG_SQL = """
INSERT INTO search_logs (query, latency_ms, result_count)
VALUES (%(query)s, %(latency_ms)s, %(result_count)s);
"""

POPULAR_QUERIES_SQL = """
SELECT query, COUNT(*) AS search_count
FROM search_logs
WHERE logged_at > NOW() - INTERVAL '7 days'
GROUP BY query
ORDER BY search_count DESC
LIMIT %(limit)s;
"""


def _connect():
    settings = get_settings()
    return psycopg2.connect(settings.postgres_dsn)


def init_search_logs_table() -> None:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()


def log_search(query: str, latency_ms: int, result_count: int) -> None:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                INSERT_LOG_SQL,
                {"query": query, "latency_ms": latency_ms, "result_count": result_count},
            )
        conn.commit()
    except Exception:
        logger.exception("Failed to log search query (non-fatal, continuing)")
    finally:
        conn.close()


def get_popular_queries(limit: int = 10) -> list[dict]:
    conn = _connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(POPULAR_QUERIES_SQL, {"limit": limit})
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
