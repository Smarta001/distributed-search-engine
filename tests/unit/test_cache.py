"""
Unit tests for search-api/cache.py.

Uses a fake in-memory Redis stand-in rather than a live server, so these
stay true unit tests — see tests/integration for tests against a real
running stack.
"""

import redis as redis_module

from cache import SearchCache
from shared.schemas import SearchResponse, SearchResultItem


class TestCacheKeyNormalization:
    def test_query_normalized_case_and_whitespace(self):
        assert SearchCache._key("Java", 1, 10) == SearchCache._key(" java ", 1, 10)
        assert SearchCache._key("Java", 1, 10) == SearchCache._key("JAVA", 1, 10)

    def test_different_pages_produce_different_keys(self):
        assert SearchCache._key("java", 1, 10) != SearchCache._key("java", 2, 10)

    def test_different_sizes_produce_different_keys(self):
        assert SearchCache._key("java", 1, 10) != SearchCache._key("java", 1, 20)

    def test_key_has_expected_prefix(self):
        assert SearchCache._key("python", 1, 10).startswith("search:")


class _FakeRedis:
    """Minimal in-memory stand-in for the redis client used by SearchCache."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def ping(self):
        return True


class _BrokenRedis:
    """Simulates Redis being unreachable, to test graceful degradation."""

    def get(self, key):
        raise redis_module.RedisError("connection refused")

    def setex(self, key, ttl, value):
        raise redis_module.RedisError("connection refused")

    def ping(self):
        raise redis_module.RedisError("connection refused")


def _sample_response() -> SearchResponse:
    return SearchResponse(
        query="java",
        total_hits=1,
        took_ms=5,
        results=[SearchResultItem(url="https://example.com", title="Java", snippet="...", score=1.0)],
    )


class TestCacheReadWrite:
    def test_set_then_get_round_trips(self):
        cache = SearchCache.__new__(SearchCache)  # bypass __init__'s real redis connection
        cache._client = _FakeRedis()

        response = _sample_response()
        cache.set("java", 1, 10, response)
        cached = cache.get("java", 1, 10)

        assert cached is not None
        assert cached.query == "java"
        assert cached.results[0].title == "Java"

    def test_get_miss_returns_none(self):
        cache = SearchCache.__new__(SearchCache)
        cache._client = _FakeRedis()
        assert cache.get("nonexistent", 1, 10) is None

    def test_redis_down_on_get_returns_none_not_raises(self):
        cache = SearchCache.__new__(SearchCache)
        cache._client = _BrokenRedis()
        assert cache.get("java", 1, 10) is None  # degrades gracefully

    def test_redis_down_on_set_does_not_raise(self):
        cache = SearchCache.__new__(SearchCache)
        cache._client = _BrokenRedis()
        cache.set("java", 1, 10, _sample_response())  # should not raise

    def test_health_false_when_redis_down(self):
        cache = SearchCache.__new__(SearchCache)
        cache._client = _BrokenRedis()
        assert cache.health() is False

    def test_health_true_when_redis_up(self):
        cache = SearchCache.__new__(SearchCache)
        cache._client = _FakeRedis()
        assert cache.health() is True
