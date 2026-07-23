"""
database.py
PostgreSQL integration for the crawler.

Responsibilities:
- Connect to PostgreSQL
- Create the pages table if it doesn't exist
- Save a crawled page's data
- Retrieve a page by URL

Uses config.py for connection details (POSTGRES_HOST, POSTGRES_DB, etc.)
so the same code works locally and inside Docker/Kubernetes.
"""

import psycopg2
import psycopg2.extras

import config


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pages (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    meta_description TEXT,
    html TEXT,
    status_code INTEGER,
    crawled_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

UPSERT_PAGE_SQL = """
INSERT INTO pages (url, title, meta_description, html, status_code, crawled_at)
VALUES (%(url)s, %(title)s, %(meta_description)s, %(html)s, %(status_code)s, NOW())
ON CONFLICT (url) DO UPDATE SET
    title = EXCLUDED.title,
    meta_description = EXCLUDED.meta_description,
    html = EXCLUDED.html,
    status_code = EXCLUDED.status_code,
    crawled_at = NOW()
RETURNING id;
"""

SELECT_PAGE_SQL = "SELECT * FROM pages WHERE url = %s;"


def connect():
    """
    Open a new connection to PostgreSQL using settings from config.py.
    Caller is responsible for closing it (or use it as a context manager).
    """
    return psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


def init_db(conn=None):
    """
    Create the pages table if it doesn't already exist.
    Call this once at crawler startup (e.g. from main.py).
    """
    own_conn = conn is None
    if own_conn:
        conn = connect()

    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        if own_conn:
            conn.close()


def save_page(url, title=None, meta_description=None, html=None, status_code=None, conn=None):
    """
    Insert a crawled page, or update it if the URL already exists
    (so re-crawling a page refreshes its data instead of erroring out).

    Returns the row's id.
    """
    own_conn = conn is None
    if own_conn:
        conn = connect()

    try:
        with conn.cursor() as cur:
            cur.execute(
                UPSERT_PAGE_SQL,
                {
                    "url": url,
                    "title": title,
                    "meta_description": meta_description,
                    "html": html,
                    "status_code": status_code,
                },
            )
            page_id = cur.fetchone()[0]
        conn.commit()
        return page_id
    finally:
        if own_conn:
            conn.close()


def get_page(url, conn=None):
    """
    Retrieve a single page by URL. Returns a dict-like row, or None
    if not found.
    """
    own_conn = conn is None
    if own_conn:
        conn = connect()

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(SELECT_PAGE_SQL, (url,))
            return cur.fetchone()
    finally:
        if own_conn:
            conn.close()


if __name__ == "__main__":
    # Quick manual test: python database.py
    # Requires PostgreSQL to actually be running and reachable
    # using the settings in config.py (POSTGRES_HOST, etc.)
    print("Connecting to:", config.POSTGRES_HOST, config.POSTGRES_PORT, config.POSTGRES_DB)

    init_db()
    print("Table ensured.")

    page_id = save_page(
        url="https://example.com",
        title="Example Domain",
        meta_description="This domain is for use in examples.",
        html="<html>...</html>",
        status_code=200,
    )
    print("Saved page id:", page_id)

    row = get_page("https://example.com")
    print("Fetched row:", row)
