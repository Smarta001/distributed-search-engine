CREATE TABLE IF NOT EXISTS crawled_pages (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    html TEXT,
    status_code INT,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);