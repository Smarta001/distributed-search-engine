"""
Redis cache-aside layer.

Flow (matches the README diagram):
    search -> redis -> hit? -> return immediately
                     -> else -> elasticsearch -> store in redis -> return
"""

from __future__ import annotations

import json

import redis

from shared.config import get_settings
from shared.constants import SEARCH_CACHE_PREFIX, SEARCH_CACHE_TTL_SECONDS
from shared.logger import get_logger
from shared.schemas import SearchResponse

logger = get_logger(__name__)


class SearchCache:
    def __init__(self):
        settings = get_settings()
        self._client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    @staticmethod
    def _key(query: str, page: int, size: int) -> str:
        # normalize so "Java", "java", " java " all hit the same cache entry
        normalized = query.strip().lower()
        return f"{SEARCH_CACHE_PREFIX}{normalized}:p{page}:s{size}"

    def get(self, query: str, page: int, size: int) -> SearchResponse | None:
        try:
            raw = self._client.get(self._key(query, page, size))
        except redis.RedisError:
            logger.warning("Redis unavailable, skipping cache read")
            return None

        if raw is None:
            return None
        return SearchResponse.model_validate(json.loads(raw))

    def set(self, query: str, page: int, size: int, response: SearchResponse) -> None:
        try:
            self._client.setex(
                self._key(query, page, size),
                SEARCH_CACHE_TTL_SECONDS,
                response.model_dump_json(),
            )
        except redis.RedisError:
            logger.warning("Redis unavailable, skipping cache write")

    def health(self) -> bool:
        try:
            return bool(self._client.ping())
        except Exception:
            return False
