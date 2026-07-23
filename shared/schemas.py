"""
Pydantic models shared across services.

Rule of thumb: if two services need to agree on the *shape* of some data
(a RabbitMQ message, an Elasticsearch document, an API response) the model
belongs here. Anything internal to one service stays in that service.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Crawler -> RabbitMQ -> Indexer
# ---------------------------------------------------------------------------

class CrawledPage(BaseModel):
    """
    Exactly what the crawler publishes to RabbitMQ for every page it fetches.
    The indexer consumes this and turns it into an IndexDocument.
    """

    url: HttpUrl
    final_url: HttpUrl = Field(
        description="URL after following redirects; may equal `url`."
    )
    status_code: int
    html: str = Field(description="Raw HTML as fetched, before any cleaning.")
    content_hash: str = Field(
        description="sha256 hex digest of `html`, used for change/duplicate detection."
    )
    crawled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    depth: int = Field(default=0, ge=0, description="Link depth from the seed URL.")

    @field_validator("status_code")
    @classmethod
    def must_be_valid_http_status(cls, v: int) -> int:
        if not (100 <= v <= 599):
            raise ValueError(f"invalid HTTP status code: {v}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/page",
                "final_url": "https://example.com/page",
                "status_code": 200,
                "html": "<html>...</html>",
                "content_hash": "9f86d081884c7d659a2feaa0c55ad015...",
                "crawled_at": "2026-07-23T10:30:00Z",
                "depth": 2,
            }
        }


# ---------------------------------------------------------------------------
# Indexer -> Elasticsearch
# ---------------------------------------------------------------------------

class IndexDocument(BaseModel):
    """
    The document shape actually stored in Elasticsearch. This is what
    search-api reads back and returns to the frontend.
    """

    url: HttpUrl
    title: str = ""
    body: str = Field(default="", description="Cleaned, plain-text page content.")
    keywords: list[str] = Field(default_factory=list)
    content_hash: str
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    page_rank: float = Field(default=0.0, ge=0.0, le=1.0)
    lang: Optional[str] = None

    def es_doc_id(self) -> str:
        """Use content_hash as the ES _id so re-indexing the same content is idempotent."""
        return self.content_hash


# ---------------------------------------------------------------------------
# Search API request/response (shared so indexer & search-api agree on shape)
# ---------------------------------------------------------------------------

class SearchResultItem(BaseModel):
    url: HttpUrl
    title: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    total_hits: int
    took_ms: int
    from_cache: bool = False
    results: list[SearchResultItem]


class SearchLog(BaseModel):
    query: str
    latency_ms: int
    result_count: int
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
