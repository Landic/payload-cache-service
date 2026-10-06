# Payload Cache Service

Small FastAPI microservice for generating interleaved payloads while caching individual string transformations and reusing payload IDs for identical requests.

## Design

The service has two persistence concepts:

- `transformation_cache`: one row per unique source string. This prevents repeated calls to the simulated external transformer.
- `payloads`: one row per unique `(list_1, list_2)` request fingerprint. This makes repeated POSTs idempotent from the caller's point of view and reuses the same UUID.

A SHA-256 fingerprint is built from canonical JSON rather than from the generated output. That preserves the distinction between different input orders even when a future transformer could produce equal output for different inputs.

For cache misses, a per-key in-process lock closes the classic check-then-act race: a second request waiting for the same value re-checks the database before calling the transformer. The database also has a unique constraint on `source_text` as the final persistence guard.

This locking scope is intentionally explicit: it protects duplicate calls inside one service process. For a multi-worker or multi-instance deployment, I would replace it with a distributed lock/single-flight mechanism (for example Redis) or a database-backed lease. The cache table and unique constraints remain useful in either model.

SQLite is used because it is sufficient for the coding task and makes the repository self-contained. The database URL is configurable, so PostgreSQL can be used without changing service code; install the optional `postgres` extra to get the PostgreSQL driver. For production with multiple writers, I would use PostgreSQL.

The task says “payloads files”, but the API contract exposes payloads through IDs and a database is explicitly required for cached outcomes, so I treat a payload as a persisted database record rather than a filesystem artifact.

The transformer is deliberately deterministic (`str.upper`) because the task describes it as a simulation of an external service. The service layer depends on the transformer interface, so a real integration can replace it without changing API or persistence code.

## API

### Create / reuse a payload

`POST /payload`

```json
{
  "list_1": ["first string", "second string", "third string"],
  "list_2": ["other string", "another string", "last string"]
}
```

Response:

```json
{
  "id": "0e2f8f14-1e7c-4d5e-a220-8ed16ad8d5f9",
  "message": "Payload created"
}
```

### Read a payload

`GET /payload/{id}`

```json
{
  "output": "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
}
```

## CLI

The executable is `cache-cli` and supports:

```bash
cache-cli [-h|--help] [--host URL|-h URL] [-r|--repeat N] [-i|--input FILE|-] [-j|--json JSON] [-o|--output FILE|-]
```

The assignment uses `-h` for both `--host` and `--help`. The implementation resolves that ambiguity contextually: `cache-cli -h` shows help, while `cache-cli -h http://localhost:8000` treats `-h` as the host flag. All actual parsing and validation is still handled by Pydantic Settings.

Input JSON must contain `list_1` and `list_2`, each an array of strings with equal lengths. `--input -` and `--json` are mutually exclusive.

Example:

```bash
echo '{"list_1":["first","second"],"list_2":["other","another"]}' | cache-cli --host http://localhost:8000
```

For repeated calls:

```bash
cache-cli -r 3 -j '{"list_1":["first"],"list_2":["other"]}'
```

The CLI performs POST + GET for every iteration and prints the resulting IDs and outputs. Repeated identical requests should return the same payload ID.

## Local development

Python 3.13 is expected.

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn app.main:app --reload
```

## Docker

```bash
docker compose up --build
```

The SQLite database is persisted in `./data/cache.db`.

## Testing strategy

The application uses `Base.metadata.create_all()` at startup instead of migrations because the assessment has a very small fixed schema. In a production project with schema evolution, I would use Alembic.

The tests cover:

- end-to-end POST/GET behavior;
- exact generated output;
- payload ID reuse;
- transformer call minimization;
- cache reuse across different payloads;
- validation and 404 behavior;
- CLI parsing and CLI source validation.

## What I would discuss in the review

1. The single-process lock vs. a distributed lock for multiple workers.
2. SQLite suitability and the switch to PostgreSQL before horizontal scaling.
3. Whether transformed values need TTL/versioning if the external transformer changes over time.
4. Payload retention/cleanup if generated payloads can grow without bound.
5. Timeouts, retries, and observability once the transformer becomes a real remote dependency.
