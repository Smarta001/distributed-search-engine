"""
Thin wrapper around pika (RabbitMQ client) so the crawler and indexer don't
each reinvent connection handling, retries, and dead-lettering.

Usage (publisher, e.g. crawler):
    from shared.messaging import RabbitMQClient
    mq = RabbitMQClient()
    mq.publish(CRAWL_EXCHANGE, CRAWL_ROUTING_KEY, crawled_page.model_dump_json())

Usage (consumer, e.g. indexer):
    mq = RabbitMQClient()
    mq.consume(CRAWL_QUEUE, on_message=handle_message)
"""

from __future__ import annotations

import time
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError

from shared.config import get_settings
from shared.constants import (
    CRAWL_EXCHANGE,
    CRAWL_QUEUE,
    CRAWL_ROUTING_KEY,
    DEAD_LETTER_EXCHANGE,
    DEAD_LETTER_QUEUE,
)
from shared.logger import get_logger

logger = get_logger(__name__)


class RabbitMQClient:
    def __init__(self, max_retries: int = 5, retry_delay_seconds: float = 3.0):
        self._settings = get_settings()
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def _connect(self) -> None:
        params = pika.URLParameters(self._settings.rabbitmq_url)
        attempt = 0
        while True:
            try:
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                self._declare_topology()
                logger.info("Connected to RabbitMQ at %s", self._settings.rabbitmq_host)
                return
            except AMQPConnectionError:
                attempt += 1
                if attempt > self._max_retries:
                    logger.error("Could not connect to RabbitMQ after %d attempts", attempt)
                    raise
                logger.warning(
                    "RabbitMQ connection failed (attempt %d/%d), retrying in %.1fs",
                    attempt, self._max_retries, self._retry_delay_seconds,
                )
                time.sleep(self._retry_delay_seconds)

    def _declare_topology(self) -> None:
        """Declare exchanges/queues/bindings idempotently, including a dead-letter path."""
        assert self._channel is not None
        ch = self._channel

        ch.exchange_declare(exchange=DEAD_LETTER_EXCHANGE, exchange_type="direct", durable=True)
        ch.queue_declare(queue=DEAD_LETTER_QUEUE, durable=True)
        ch.queue_bind(exchange=DEAD_LETTER_EXCHANGE, queue=DEAD_LETTER_QUEUE, routing_key=DEAD_LETTER_QUEUE)

        ch.exchange_declare(exchange=CRAWL_EXCHANGE, exchange_type="direct", durable=True)
        ch.queue_declare(
            queue=CRAWL_QUEUE,
            durable=True,
            arguments={
                "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
                "x-dead-letter-routing-key": DEAD_LETTER_QUEUE,
            },
        )
        ch.queue_bind(exchange=CRAWL_EXCHANGE, queue=CRAWL_QUEUE, routing_key=CRAWL_ROUTING_KEY)

    def _ensure_connected(self) -> BlockingChannel:
        if self._channel is None or self._channel.is_closed:
            self._connect()
        assert self._channel is not None
        return self._channel

    def publish(self, exchange: str, routing_key: str, body: str) -> None:
        channel = self._ensure_connected()
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=body.encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistent
            ),
        )

    def consume(self, queue: str, on_message: Callable[[str], bool], prefetch: int = 10) -> None:
        """
        Blocking consumer. `on_message` receives the message body as a string
        and returns True to ack, False to nack (message goes to the DLQ instead
        of being requeued, to avoid poison-message infinite loops).
        """
        channel = self._ensure_connected()
        channel.basic_qos(prefetch_count=prefetch)

        def _callback(ch, method, _properties, body: bytes):
            try:
                success = on_message(body.decode("utf-8"))
            except Exception:
                logger.exception("Unhandled error processing message, sending to DLQ")
                success = False

            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_consume(queue=queue, on_message_callback=_callback)
        logger.info("Waiting for messages on queue '%s'", queue)
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()

    def close(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()
