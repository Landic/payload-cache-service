# Video walkthrough script

This is a suggested 10–12 minute walkthrough for the required English video.

## 1. Problem and design (about 1 minute)

“ This service receives two equal-length string lists. Every string goes through a simulated external transformer, the transformed values are interleaved, and the result is stored behind a payload ID. The important optimization is that the transformer result is cached per input string, and identical payload requests reuse the existing payload ID.”

“ I chose SQLite for the assessment because it keeps the repository self-contained. The connection string is configurable, so moving to PostgreSQL does not require changing the service layer.”

## 2. API entry point (about 2 minutes)

Open `app/main.py`, then `app/api.py`.

Explain that `create_app()` builds the engine, session factory, cache service, and FastAPI lifespan. The POST and GET endpoints stay thin: validation and HTTP concerns live here, while caching/deduplication is in the service layer.

Show the sample request and explain that POST returns the ID, while GET returns the stored output.

## 3. Data model (about 1 minute)

Open `app/models.py`.

Explain the two tables:

- `transformation_cache`: unique `source_text` → transformed value.
- `payloads`: unique request fingerprint → UUID + final output.

Point out the database unique constraints. They are the final protection against duplicate persisted entries even if two requests race.

## 4. Core caching logic (about 3 minutes)

Open `app/service.py`. Start with `create_payload()`.

Explain the order:

1. Calculate a canonical SHA-256 request fingerprint.
2. Return an existing payload immediately when that fingerprint exists.
3. Deduplicate values inside the request with `dict.fromkeys()`.
4. Read cached transformation results.
5. For misses, acquire a per-key lock, re-check the database, then call the transformer only when the value is still missing.
6. Build the interleaved result and persist/reuse the payload.

Call out the concurrency decision explicitly: the lock protects duplicate transformer calls inside one Python process. For multiple workers or instances, use a distributed lock/single-flight mechanism or a database-backed lease.

Open `app/transformer.py` and explain that `upper()` is only a deterministic stand-in for the real external service.

## 5. CLI (about 1 minute)

Open `cli/main.py`.

Explain that `CliSettings` is Pydantic Settings and therefore owns parsing and type validation. Input can come from `--input` or `--json`; output can go to a file or stdout.

Show the special handling for `-h`: the task itself assigns that flag to both host and help, which is ambiguous. The implementation resolves it contextually: `-h` alone is help and `-h URL` means host.

Show that the CLI performs POST + GET for each repeat.

## 6. Tests (about 2 minutes)

Open `tests/test_api.py`. Show:

- POST + GET end-to-end.
- Same payload returns the same ID and does not call the transformer again.
- Different payloads still reuse cached strings.
- Validation and 404 behavior.

Open `tests/test_cli.py` and `tests/test_service.py`. Mention that the test suite currently passes all 9 tests.

## 7. Docker and trade-offs (about 1 minute)

Show `Dockerfile`, `docker-compose.yml`, and the final section of `README.md`.

Close with the production follow-ups:

- PostgreSQL for multi-writer production use.
- Distributed locking for multiple application workers/instances.
- Alembic once the schema starts evolving.
- TTL/versioning for transformer cache if the external result can change.
- Retention/cleanup for payload records and metrics around external transformation failures.
