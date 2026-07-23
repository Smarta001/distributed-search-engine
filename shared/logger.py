"""
One logging config for every service, so log lines look the same whether
they come from crawler, indexer, or search-api — important once you're
reading merged logs from Kubernetes.
"""

import logging
import sys

from shared.config import get_settings

_CONFIGURED = False


def get_logger(name: str) -> logging.Logger:
    global _CONFIGURED

    if not _CONFIGURED:
        settings = get_settings()
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            stream=sys.stdout,
        )
        _CONFIGURED = True

    return logging.getLogger(name)
