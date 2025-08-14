# Olympiad Consumer Service

## Purpose
Consumes messages from RabbitMQ with user identity, fetches olympiad records from `diploma.olimpiada.ru`, and stores them via DB API.

## Inputs
- Queue message JSON fields:
  - `first_name` (str, required)
  - `last_name` (str, required)
  - `middle_name` (str, optional)
  - `date_of_birth` (str, dd-mm-yyyy, required)
  - `user_tg_id` (str, required)

## Outputs
- Creates olympiad records via `POST /olymp/create/` on DB API.
- Logs to console and `app_rmq.log`.

## Environment Variables
- `RMQ_USER`, `RMQ_PASS`, `RMQ_HOST`, `RMQ_PORT`
- `DB_SERVER_HOST`, `DB_SERVER_PORT`
- `DB_API_TOKEN` (optional)
- `LOG_LEVEL` (default `INFO`)

## Setup
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python consumer.py
```

## Tests
```bash
pip install -r requirements.txt
pip install pytest
pytest -q
```

## Error Handling
- Invalid JSON: message is rejected (nack, no requeue).
- Validation errors: message is rejected (nack, no requeue).
- Network/transient errors: message is requeued.
- Conflict (already exists): logged as info.

## Logging
Structured format: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`.
Level configurable via `LOG_LEVEL`.

## Changelog (key modifications)
- Added `config.py` with typed config and env validation.
- Introduced resilient `HttpClient` with retries and timeouts.
- Added `DatabaseApiClient` for DB API operations.
- Refactored `parser.py`: logging, dynamic years window, cleaned parsing.
- Added `processor.py` separating business logic from I/O; input validation; display limit.
- Rewrote `consumer.py` for robust ack/nack, prefetch, and composition.
- Added unit tests for parser, processor, and DB client.
- Added `requirements.txt`.

## Future Optimizations
- Batch POST to reduce round-trips.
- Async I/O (e.g., `aio_pika`, `aiohttp`) for higher throughput.
- Caching HEAD existence per person/year.
- Circuit breaker around DB API.
- Structured logging (JSON) and metrics (Prometheus).