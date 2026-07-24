"""
Elasticsearch wrapper: creates the `pages` index with an explicit BM25
similarity mapping (BM25 is actually ES's default similarity, but we set it
explicitly so it's documented and tunable — e.g. k1/b — rather than implicit),
and provides a simple method to index an IndexDocument.
"""

from __future__ import annotations

import time
from elasticsearch import Elasticsearch, NotFoundError
from elastic_transport import ConnectionError

from shared.config import get_settings
from shared.constants import PAGES_INDEX
from shared.logger import get_logger
from shared.schemas import IndexDocument

logger = get_logger(__name__)


INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "similarity": {
            "custom_bm25": {
                "type": "BM25",
                "k1": 1.2,   # term frequency saturation, ES default
                "b": 0.75,   # length normalization, ES default
            }
        },
        "analysis": {
            "analyzer": {
                "default": {
                    "type": "standard",
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "url": {"type": "keyword"},
            "title": {
                "type": "text",
                "similarity": "custom_bm25",
                "fields": {"raw": {"type": "keyword"}},
            },
            "body": {
                "type": "text",
                "similarity": "custom_bm25",
            },
            "keywords": {"type": "keyword"},
            "content_hash": {"type": "keyword"},
            "indexed_at": {"type": "date"},
            "page_rank": {"type": "float"},
            "lang": {"type": "keyword"},
        }
    },
}


class ESClient:
    def __init__(self):
        settings = get_settings()
        self._client = Elasticsearch(settings.elasticsearch_url)

    def ensure_index(self) -> None:
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self._client.indices.get(index=PAGES_INDEX)
                logger.info("Index '%s' already exists", PAGES_INDEX)
                return
            except NotFoundError:
                logger.info("Creating index '%s'", PAGES_INDEX)
                self._client.indices.create(index=PAGES_INDEX, body=INDEX_SETTINGS)
                return
            except ConnectionError:
                logger.warning("Elasticsearch not ready. Retrying in 5s (Attempt %d/%d)", attempt + 1, max_retries)
                time.sleep(5)
                
        raise Exception("Could not connect to Elasticsearch after multiple retries.")

    def index_document(self, doc: IndexDocument) -> None:
        """Upserts by content_hash, so re-indexing unchanged pages is a no-op-ish overwrite."""
        self._client.index(
            index=PAGES_INDEX,
            id=doc.es_doc_id(),
            document=doc.model_dump(mode="json"),
        )
        logger.info("Indexed document %s (%s)", doc.es_doc_id(), doc.url)

    def health(self) -> dict:
        return dict(self._client.cluster.health())