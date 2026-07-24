"""
search-api: FastAPI service exposing /search, /suggest, /health, /popular.

Run from the project root so `shared` resolves as a package:
    cd search-api
    uvicorn main:app --reload --port 8000

(The sys.path tweak below adds the project root so this still works even
though `search-api` has a hyphen and can't itself be imported as a package.)
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from cache import SearchCache
from es_search import SearchClient
from search_logs import get_popular_queries, init_search_logs_table, log_search
from shared.logger import get_logger
from shared.schemas import SearchResponse

logger = get_logger(__name__)

app = FastAPI(title="Distributed Search Engine API", version="0.1.0")

# Wide open for local dev; tighten this to your frontend's origin before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_search_client: SearchClient | None = None
_cache: SearchCache | None = None


@app.on_event("startup")
def startup() -> None:
    global _search_client, _cache
    _search_client = SearchClient()
    _cache = SearchCache()
    try:
        init_search_logs_table()
    except Exception:
        logger.exception("Could not initialize search_logs table at startup (Postgres may be down)")


@app.get("/health")
def health():
    es_ok = _search_client.health() if _search_client else False
    redis_ok = _cache.health() if _cache else False
    status = "ok" if (es_ok and redis_ok) else "degraded"
    return {"status": status, "elasticsearch": es_ok, "redis": redis_ok}


@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
):
    if _cache is None or _search_client is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    cached = _cache.get(q, page, size)
    if cached is not None:
        cached.from_cache = True
        return cached

    start = time.perf_counter()
    try:
        response = _search_client.search(q, page=page, size=size)
    except Exception:
        logger.exception("Elasticsearch query failed")
        raise HTTPException(status_code=502, detail="Search backend unavailable")

    _cache.set(q, page, size, response)

    latency_ms = int((time.perf_counter() - start) * 1000)
    log_search(query=q, latency_ms=latency_ms, result_count=response.total_hits)

    return response


@app.get("/suggest")
def suggest(q: str = Query(..., min_length=1)):
    if _search_client is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    try:
        return {"query": q, "suggestions": _search_client.suggest_titles(q)}
    except Exception:
        logger.exception("Suggest query failed")
        raise HTTPException(status_code=502, detail="Search backend unavailable")


@app.get("/popular")
def popular(limit: int = Query(10, ge=1, le=50)):
    try:
        return {"popular_queries": get_popular_queries(limit=limit)}
    except Exception:
        logger.exception("Failed to fetch popular queries")
        raise HTTPException(status_code=502, detail="Database unavailable")
