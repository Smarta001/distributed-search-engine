# Testing

## Install test dependencies

From the project root:

```powershell
pip install -r tests/requirements.txt -r shared/requirements.txt -r indexer/requirements.txt -r search-api/requirements.txt
python -m spacy download en_core_web_sm
```

## Run everything

```powershell
python -m pytest tests -v
```

Two kinds of tests live here, and they behave differently:

### `tests/unit/` — always run, no services needed

Fast, isolated tests against the actual code:
- `test_schemas.py` — Pydantic model validation (bad status codes,
  out-of-range page rank, round-trip serialization)
- `test_text_processor.py` — HTML stripping (removes `<script>`/`<nav>`
  junk), keyword extraction (lemmatization, e.g. "Running" → "run"),
  full `process_html()` pipeline
- `test_cache.py` — Redis cache key normalization, and confirms search-api
  degrades gracefully (doesn't crash) when Redis is unreachable

### `tests/integration/` — auto-skip unless services are running

Real HTTP/Elasticsearch calls against your actual running stack:
- `test_search_api.py` — hits `/health`, `/search`, `/suggest`, `/popular`
  on a live search-api instance, including a cache-hit check
- `test_indexer_output.py` — queries live Elasticsearch directly to
  confirm the `pages` index actually has documents in it

These are skipped automatically (with a clear reason printed, not a
failure) if `localhost:8000`, `9200`, `5672`, `5432`, or `6379` aren't
reachable — see `tests/conftest.py`.

**To run integration tests too**, bring up the full stack first:
```powershell
cd docker
docker compose up -d
cd ../search-api
uvicorn main:app --port 8000
```
then, in another terminal:
```powershell
python -m pytest tests -m integration -v
```

## Current status

31 unit tests, 12 integration tests. All passing as of the last full run
(unit tests standalone; integration tests against the live Docker stack).
