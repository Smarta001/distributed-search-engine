"""
Integration tests — these hit your ACTUAL running services over real
HTTP, not mocks. They auto-skip (see conftest.py) if search-api,
elasticsearch, rabbitmq, postgres, or redis aren't reachable on their
default localhost ports.

Run with docker compose up (for the backing services) and
`uvicorn main:app --port 8000` (for search-api) both running first:

    pytest -m integration -v
"""

import requests

pytestmark = __import__("pytest").mark.integration

BASE_URL = "http://localhost:8000"


class TestHealthEndpoint:
    def test_health_returns_200(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200

    def test_health_reports_elasticsearch_and_redis(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        body = resp.json()
        assert "elasticsearch" in body
        assert "redis" in body
        assert "status" in body


class TestSearchEndpoint:
    def test_search_requires_query_param(self):
        resp = requests.get(f"{BASE_URL}/search", timeout=5)
        assert resp.status_code == 422  # FastAPI validation error, missing required `q`

    def test_search_returns_valid_shape(self):
        resp = requests.get(f"{BASE_URL}/search", params={"q": "example"}, timeout=10)
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "example"
        assert isinstance(body["results"], list)
        assert isinstance(body["total_hits"], int)
        assert isinstance(body["took_ms"], int)

    def test_search_respects_size_param(self):
        resp = requests.get(f"{BASE_URL}/search", params={"q": "example", "size": 3}, timeout=10)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 3

    def test_search_rejects_oversized_page_size(self):
        resp = requests.get(f"{BASE_URL}/search", params={"q": "example", "size": 999}, timeout=5)
        assert resp.status_code == 422  # size cap is 50, see main.py Query(..., le=50)

    def test_repeated_identical_search_is_served_from_cache(self):
        # First call may or may not be cached depending on test run order;
        # the second call for the exact same query/page/size should be.
        params = {"q": "example-cache-check", "page": 1, "size": 10}
        requests.get(f"{BASE_URL}/search", params=params, timeout=10)
        second = requests.get(f"{BASE_URL}/search", params=params, timeout=10)
        assert second.json()["from_cache"] is True


class TestSuggestEndpoint:
    def test_suggest_returns_list(self):
        resp = requests.get(f"{BASE_URL}/suggest", params={"q": "ex"}, timeout=5)
        assert resp.status_code == 200
        body = resp.json()
        assert "suggestions" in body
        assert isinstance(body["suggestions"], list)


class TestPopularEndpoint:
    def test_popular_returns_list_after_searches_logged(self):
        # Trigger at least one logged search first.
        requests.get(f"{BASE_URL}/search", params={"q": "popularity-check"}, timeout=10)

        resp = requests.get(f"{BASE_URL}/popular", timeout=5)
        assert resp.status_code == 200
        assert "popular_queries" in resp.json()
