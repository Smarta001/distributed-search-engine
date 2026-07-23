"""
rabbitmq.py
RabbitMQ Producer for the crawler.

Responsibilities:
- Connect to RabbitMQ
- Publish a message for each successfully crawled page

The indexer service (a separate component, not part of your crawler
module) will later consume these messages from the queue and build
the search index.
"""

import json
import pika

import config


def _get_connection():
    """
    Open a new blocking connection to RabbitMQ using settings from
    config.py.
    """
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        credentials=credentials,
    )
    return pika.BlockingConnection(parameters)


class RabbitMQPublisher:
    """
    Wraps a single connection/channel so main.py (or worker threads)
    can publish repeatedly without reconnecting for every page.

    Note: a single pika BlockingConnection is NOT thread-safe. If you
    use multiple worker threads (Milestone 2), create one
    RabbitMQPublisher per thread rather than sharing one instance.
    """

    def __init__(self):
        self.connection = _get_connection()
        self.channel = self.connection.channel()
        # durable=True so the queue survives a RabbitMQ restart
        self.channel.queue_declare(queue=config.RABBITMQ_QUEUE, durable=True)

    def publish_page(self, url, title=None, status_code=None):
        """
        Publish a message announcing a page has been crawled and saved.
        Kept intentionally small (url/title/status) — the indexer can
        fetch the full record from PostgreSQL via the URL if it needs
        the full HTML/metadata.
        """
        message = {
            "url": url,
            "title": title,
            "status": status_code,
        }

        self.channel.basic_publish(
            exchange="",
            routing_key=config.RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type="application/json",
            ),
        )

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

    # Support "with RabbitMQPublisher() as pub:" usage
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Quick manual test: python rabbitmq.py
    # Requires RabbitMQ to actually be running and reachable using the
    # settings in config.py (RABBITMQ_HOST, etc.)
    print("Connecting to RabbitMQ at:", config.RABBITMQ_HOST, config.RABBITMQ_PORT)

    with RabbitMQPublisher() as publisher:
        publisher.publish_page(
            url="https://example.com",
            title="Example Domain",
            status_code=200,
        )
        print(f"Published test message to queue '{config.RABBITMQ_QUEUE}'")

      #Notes:RabbitMQPublisher wraps the connection so you don't reconnect for every single page — create one instance and reuse it across the crawl.
#Supports with RabbitMQPublisher() as pub: for automatic cleanup.
#Messages are kept small (url/title/status) since the indexer can pull full page data from PostgreSQL via the URL — no need to duplicate the whole HTML into the queue.
#delivery_mode=2 + durable=True on the queue means messages survive a RabbitMQ restart, so you don't lose crawled pages if the broker restarts mid-run.
# Note in the docstring: a single connection isn't thread-safe — once you get to Milestone 2 (multithreading), give each worker thread its own RabbitMQPublisher instance rather than sharing one.