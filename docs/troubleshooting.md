# Troubleshooting

Real problems hit while building this, and how they were fixed.

---

## `psycopg2.OperationalError: password authentication failed for user "..."`

**Cause 1 — wrong credentials for the environment you're actually running
against.** search-api's `.env` needs to match whatever's set in
`docker/docker-compose.yml`'s `postgres` service (`POSTGRES_USER` /
`POSTGRES_PASSWORD` / `POSTGRES_DB`), not the code's built-in defaults.

**Cause 2 — a native/local PostgreSQL install competing for port 5432.**
If PostgreSQL is also installed directly on Windows (not just in Docker)
and running as a background service, it can bind port 5432 before or
alongside the Docker container. Your app connects to whichever one
actually answers on `localhost:5432`, which may not be the container.

Check for a native service:
```powershell
Get-Service | Where-Object {$_.Name -like "*postgres*"}
netstat -ano | findstr :5432
```
Stop it if found:
```powershell
Stop-Service <service_name>
```

**Cause 3 — the Postgres data volume was already initialized with
different credentials.** Postgres only runs its user-creation script the
*first* time a fresh data volume is created. Changing `POSTGRES_PASSWORD`
in `docker-compose.yml` after the volume already exists has no effect.
Fix by resetting the password directly inside the running container
(works without knowing the current password, since local Unix-socket
connections are trusted by default):
```powershell
docker exec -it search-postgres psql -U search -d distributed_search -c "ALTER USER search WITH PASSWORD 'search123';"
```

**Verifying the fix actually worked** — test with a real TCP + password
connection (not `docker exec`, which bypasses password auth):
```powershell
docker exec -it search-postgres psql -U search -d distributed_search -h localhost -c "SELECT 1;"
```

---

## `.env` file not being picked up

Windows hides file extensions by default. A file created via right-click →
New Text Document and renamed to `.env` often actually saves as `.env.txt`
without you noticing. Check with:
```powershell
Get-ChildItem -Force
```
and confirm it says exactly `.env`, not `.env.txt`.

To see exactly what your app is reading (catches hidden trailing spaces
or `\r` characters that don't show up in a normal file view):
```powershell
python -c "from shared.config import get_settings; s = get_settings(); print(repr(s.postgres_user), repr(s.postgres_password))"
```

---

## `OSError: [E050] Can't find model 'en_core_web_sm'`

`pip install spacy` installs the library only — the English model is a
separate download.
```powershell
python -m spacy download en_core_web_sm
```
If that fails (network issues), install it directly as a package instead:
```powershell
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```
This also needs to happen inside `indexer/Dockerfile` if the indexer runs
in Docker — check for a model-download step there if the containerized
indexer ever hits this same error.

---

## `/health` shows `"redis": false`

Redis isn't in `docker/docker-compose.yml` by default in earlier versions
of this project — check `docker compose ps` for a `redis` container. If
it's missing, add:
```yaml
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
```
then `docker compose up -d redis`.

This failure mode doesn't crash search-api — by design, `cache.py` catches
`RedisError` and just skips caching, querying Elasticsearch directly every
time instead. So a missing Redis shows up as "search works but is slower
and `/health` looks degraded," not as a crash.

---

## RabbitMQ `PRECONDITION_FAILED` on queue declare

Happens if two services declare the same queue name with **different
arguments** (e.g. one adds dead-letter-exchange arguments, the other
doesn't). RabbitMQ locks in a queue's arguments the first time it's
declared — whichever service connects first "wins," and the second
service's declare call fails.

Fix: make sure every service declaring `crawl_results_queue` uses the
exact same `queue_declare(...)` arguments. See
[architecture.md](./architecture.md#message-contract-mismatch) for the
related (but distinct) message-format mismatch between the crawler and
`shared/schemas.py`.
