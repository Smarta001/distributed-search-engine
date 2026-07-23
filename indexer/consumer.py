"""
Wires the RabbitMQ consumer to the text processor and Elasticsearch client.

Message flow:
    RabbitMQ (CrawledPage JSON)
        -> parse into CrawledPage
        -> text_processor.process_html()
        -> build IndexDocument
        -> es_client.index_document()
"""

from __future__ import annotations

from pydantic import ValidationError

from indexer.es_client import ESClient
from indexer.text_processor import process_html
from shared.constants import CRAWL_QUEUE
from shared.logger import get_logger
from shared.messaging import RabbitMQClient
from shared.schemas import CrawledPage, IndexDocument

logger = get_logger(__name__)


class IndexerConsumer:
    def __init__(self):
        self._mq = RabbitMQClient()
        self._es = ESClient()
        self._es.ensure_index()

    def handle_message(self, body: str) -> bool:
        """Returns True to ack the message, False to send it to the DLQ."""
        try:
            page = CrawledPage.model_validate_json(body)
        except ValidationError:
            logger.exception("Malformed CrawledPage message, dropping to DLQ")
            return False

        if page.status_code >= 400:
            logger.info("Skipping %s (status %d)", page.url, page.status_code)
            return True  # not an error, just nothing to index

        try:
            processed = process_html(page.html)
        except Exception:
            logger.exception("Failed to process HTML for %s", page.url)
            return False

        doc = IndexDocument(
            url=page.final_url,
            title=processed.title,
            body=processed.body,
            keywords=processed.keywords,
            content_hash=page.content_hash,
            lang=processed.lang,
        )

        try:
            self._es.index_document(doc)
        except Exception:
            logger.exception("Failed to index %s", page.url)
            return False

        return True

    def run(self) -> None:
        logger.info("Indexer consumer starting up...")
        self._mq.consume(CRAWL_QUEUE, on_message=self.handle_message)
