"""
Shared fixtures.

Handles two path quirks so imports work the same way pytest does as they
do when the services actually run:
  - project root needs to be importable so `shared` and `indexer` resolve
  - `search-api` has a hyphen and can't be imported as a package, so its
    directory gets added to sys.path directly (same trick main.py uses)
"""

import socket
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEARCH_API_DIR = PROJECT_ROOT / "search-api"

for path in (PROJECT_ROOT, SEARCH_API_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def search_api_base_url() -> str:
    return "http://localhost:8000"


def pytest_collection_modifyitems(config, items):
    """
    Auto-skips any test marked @pytest.mark.integration if the expected
    local services (search-api, elasticsearch, rabbitmq, postgres, redis)
    aren't reachable — so `pytest` doesn't just fail loudly when someone
    runs the suite without docker compose up.
    """
    required_ports = {
        "search-api (localhost:8000)": ("localhost", 8000),
        "elasticsearch (localhost:9200)": ("localhost", 9200),
        "rabbitmq (localhost:5672)": ("localhost", 5672),
        "postgres (localhost:5432)": ("localhost", 5432),
        "redis (localhost:6379)": ("localhost", 6379),
    }
    down = [name for name, (h, p) in required_ports.items() if not _port_open(h, p)]
    if not down:
        return

    skip_marker = pytest.mark.skip(
        reason=f"Skipping integration test — services not reachable: {', '.join(down)}"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)
