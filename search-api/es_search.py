"""
Elasticsearch search logic for search-api.

Builds a BM25 multi_match query against the `pages` index that the indexer
service creates and populates (see indexer/es_client.py for the mapping —
this module assumes that index already exists).
"""

from __future__ import annotations

import time

from elasticsearch import Elasticsearch

from shared.config import get_settings
from shared.constants import PAGES_INDEX
from shared.logger import get_logger
from shared.schemas import SearchResponse, SearchResultItem

logger = get_logger(__name__)


class SearchClient:
    def __init__(self):
        settings = get_settings()
        self._client = Elasticsearch(settings.elasticsearch_url)

    def search(self, query: str, page: int = 1, size: int = 10) -> SearchResponse:
        start = time.perf_counter()

        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "body"],  # title matches weighted higher
                    "type": "best_fields",
                }
            },
            "highlight": {
                "fields": {"body": {"fragment_size": 160, "number_of_fragments": 1}}
            },
            "from": max(page - 1, 0) * size,
            "size": size,
        }

        result = self._client.search(index=PAGES_INDEX, body=body)
        took_ms = int((time.perf_counter() - start) * 1000)

        hits = result["hits"]["hits"]
        total_hits = result["hits"]["total"]["value"]

        results = []
        for hit in hits:
            source = hit["_source"]
            snippet = self._extract_snippet(hit, source)
            results.append(
                SearchResultItem(
                    url=source["url"],
                    title=source.get("title") or source["url"],
                    snippet=snippet,
                    score=hit.get("_score") or 0.0,
                )
            )

        return SearchResponse(
            query=query,
            total_hits=total_hits,
            took_ms=took_ms,
            results=results,
        )

    @staticmethod
    def _extract_snippet(hit: dict, source: dict) -> str:
        highlight = hit.get("highlight", {}).get("body")
        if highlight:
            return highlight[0]
        body = source.get("body", "")
        return (body[:160] + "...") if len(body) > 160 else body

    def suggest_titles(self, prefix: str, limit: int = 5) -> list[str]:
        """Simple prefix-based autocomplete over titles (not a dedicated ES suggester)."""
        body = {
            "query": {
                "match_phrase_prefix": {"title": {"query": prefix}}
            },
            "_source": ["title"],
            "size": limit,
        }
        result = self._client.search(index=PAGES_INDEX, body=body)
        titles = []
        for hit in result["hits"]["hits"]:
            title = hit["_source"].get("title")
            if title and title not in titles:
                titles.append(title)
        return titles

    def health(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:
            return False
