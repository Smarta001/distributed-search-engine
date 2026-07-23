"""
Entrypoint for the indexer service.

Run with:
    python -m indexer.main
(from the project root, so `shared` and `indexer` resolve as packages)
"""

from indexer.consumer import IndexerConsumer
from shared.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    consumer = IndexerConsumer()
    consumer.run()


if __name__ == "__main__":
    main()
