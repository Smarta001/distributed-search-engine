# Setup

## Prerequisites

- Docker Desktop
- Python 3.10+
- The `en_core_web_sm` spaCy model (see step 4 below)

## 1. Start the backing services

From the `docker/` folder:

```powershell
docker compose up -d
```

This brings up:

| Service | Container | Port(s) |
|---|---|---|
| PostgreSQL | `search-postgres` | 5432 |
| RabbitMQ | `rabbitmq` | 5672 (AMQP), 15672 (management UI) |
| Elasticsearch | `elasticsearch` | 9200 |
| Redis | `redis` | 6379 |
| Crawler | `crawler` | — |
| Indexer | `indexer` | — |

Check everything's up in Docker Desktop, or:
```powershell
docker compose ps
```

## 2. Confirm the pipeline actually produced data

The crawler runs once and populates PostgreSQL + publishes to RabbitMQ;
the indexer consumes those messages and populates Elasticsearch. Check
the indexer's logs for `Indexed document ... [status:201]` lines to
confirm documents are landing in Elasticsearch.

## 3. Set up search-api

search-api runs **outside** Docker for now (not yet containerized).

```powershell
cd search-api
pip install -r requirements.txt
```

Create a `.env` file inside `search-api/` (same folder as `main.py`):

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=search
POSTGRES_PASSWORD=search123
POSTGRES_DB=distributed_search

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6379/0
```

> These are the credentials set in `docker/docker-compose.yml`'s
> `postgres` service. If that file changes, update this `.env` to match.

## 4. Install the spaCy model (for the indexer)

If you're running the indexer outside Docker (e.g. for local development
or debugging), you'll also need:

```powershell
python -m spacy download en_core_web_sm
```

If that fails, install it directly instead:
```powershell
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```

If you're only running the indexer inside its Docker container, confirm
the model install step is actually present in `indexer/Dockerfile` — the
container needs it too, for the same reason.

## 5. Run search-api

```powershell
cd search-api
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for interactive Swagger docs, or check
`http://localhost:8000/health` — it should report:

```json
{"status": "ok", "elasticsearch": true, "redis": true}
```

## 6. Try a real search

```
http://localhost:8000/search?q=example
```

should return results from whatever the crawler actually fetched.
