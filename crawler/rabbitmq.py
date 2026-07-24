"""
rabbitmq.py
RabbitMQ Producer for the crawler.

Responsibilities:
- Connect to RabbitMQ (with retry logic)
- Publish a message for each successfully crawled page
"""

import json
import time
import pika
import hashlib

import config


def _get_connection():
    """
    Open a new blocking connection to RabbitMQ using settings from
    config.py, with a retry loop for startup delays.
    """
    credentials = pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=config.RABBITMQ_HOST,
        port=config.RABBITMQ_PORT,
        credentials=credentials,
    )
    
    max_retries = 10
    for attempt in range(max_retries):
        try:
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            print(f"RabbitMQ not ready. Retrying in 5s (Attempt {attempt + 1}/{max_retries})")
            time.sleep(5)
            
    raise Exception("Could not connect to RabbitMQ after multiple retries.")


class RabbitMQPublisher:
    """
    Wraps a single connection/channel so main.py (or worker threads)
    can publish repeatedly without reconnecting for every page.
    """

    def __init__(self):
        self.connection = _get_connection()
        self.channel = self.connection.channel()
        
        # Fully match the Indexer's Dead-Letter Exchange and Routing Key configuration
        queue_arguments = {
            "x-dead-letter-exchange": "crawl_dlx",
            "x-dead-letter-routing-key": "crawl_results_dlq"
        }
        
        # durable=True so the queue survives a RabbitMQ restart
        self.channel.queue_declare(
            queue=config.RABBITMQ_QUEUE, 
            durable=True,
            arguments=queue_arguments
        )

    def publish_page(self, url, title=None, status_code=None, html=""):
        """
        Publish a message announcing a page has been crawled and saved.
        Includes full HTML and a content hash to satisfy the Indexer's Pydantic schema.
        """
        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest() if html else ""
        
        message = {
            "url": url,
            "final_url": url,
            "title": title,
            "status_code": status_code,
            "html": html,
            "content_hash": content_hash
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
    print("Connecting to RabbitMQ at:", config.RABBITMQ_HOST, config.RABBITMQ_PORT)

    with RabbitMQPublisher() as publisher:
        publisher.publish_page(
            url="https://example.com",
            title="Example Domain",
            status_code=200,
            html="<html><body><h1>Test</h1></body></html>"
        )
        print(f"Published test message to queue '{config.RABBITMQ_QUEUE}'")