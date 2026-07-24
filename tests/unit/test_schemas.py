"""
Unit tests for shared/schemas.py.

NOTE: as of writing, CrawledPage here still expects the *original* heavy
message shape (html, content_hash) rather than the crawler's actual
lightweight {url, title, status} format — that reconciliation is still
pending. These tests verify the code as it currently stands; update them
alongside schemas.py once that's resolved.
"""

import pytest
from pydantic import ValidationError

from shared.schemas import CrawledPage, IndexDocument, SearchLog, SearchResponse, SearchResultItem


class TestCrawledPage:
    def test_valid_page_parses(self):
        page = CrawledPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            html="<html><body>hi</body></html>",
            content_hash="abc123",
        )
        assert page.status_code == 200
        assert page.depth == 0  # default

    @pytest.mark.parametrize("bad_status", [0, 99, 600, -1])
    def test_invalid_status_code_rejected(self, bad_status):
        with pytest.raises(ValidationError):
            CrawledPage(
                url="https://example.com",
                final_url="https://example.com",
                status_code=bad_status,
                html="<html></html>",
                content_hash="abc123",
            )

    def test_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            CrawledPage(url="https://example.com", status_code=200)  # missing final_url, html, content_hash


class TestIndexDocument:
    def test_defaults(self):
        doc = IndexDocument(url="https://example.com", content_hash="xyz")
        assert doc.title == ""
        assert doc.keywords == []
        assert doc.page_rank == 0.0

    def test_es_doc_id_uses_content_hash(self):
        doc = IndexDocument(url="https://example.com", content_hash="deadbeef")
        assert doc.es_doc_id() == "deadbeef"

    @pytest.mark.parametrize("bad_rank", [-0.1, 1.1])
    def test_page_rank_out_of_bounds_rejected(self, bad_rank):
        with pytest.raises(ValidationError):
            IndexDocument(url="https://example.com", content_hash="x", page_rank=bad_rank)


class TestSearchResponse:
    def test_round_trip_serialization(self):
        response = SearchResponse(
            query="java",
            total_hits=1,
            took_ms=12,
            results=[
                SearchResultItem(
                    url="https://example.com", title="Java Tutorial", snippet="Learn Java...", score=4.2
                )
            ],
        )
        as_json = response.model_dump_json()
        rebuilt = SearchResponse.model_validate_json(as_json)
        assert rebuilt.results[0].title == "Java Tutorial"
        assert rebuilt.from_cache is False


class TestSearchLog:
    def test_defaults_logged_at(self):
        log = SearchLog(query="python", latency_ms=42, result_count=5)
        assert log.logged_at is not None
