"""
Verifies the indexer's actual output in Elasticsearch — i.e. that the
crawler -> RabbitMQ -> indexer pipeline really did produce searchable
documents, not just that the service didn't crash.
"""

import pytest
from elasticsearch import Elasticsearch

from shared.constants import PAGES_INDEX

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def es_client():
    return Elasticsearch("http://localhost:9200")


class TestIndexedData:
    def test_pages_index_exists(self, es_client):
        assert es_client.indices.exists(index=PAGES_INDEX)

    def test_index_has_at_least_one_document(self, es_client):
        count = es_client.count(index=PAGES_INDEX)["count"]
        assert count > 0, (
            "No documents found in the pages index — run the crawler first "
            "so the indexer has something to process."
        )

    def test_indexed_documents_have_required_fields(self, es_client):
        result = es_client.search(index=PAGES_INDEX, body={"query": {"match_all": {}}, "size": 1})
        hits = result["hits"]["hits"]
        assert len(hits) == 1
        source = hits[0]["_source"]
        assert "url" in source
        assert "body" in source
