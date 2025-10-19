# Kanchi

Kanchi is a real-time Celery task monitoring (and management) system with an enjoyable user interface. It provides insights into task execution, worker health, and task statistics.

## Features

- Real-time task monitoring via WebSocket
- Task filtering and searching (date range, status, name, worker, full-text)
- Task retry tracking and orphan detection
- Daily task statistics and history
- Worker health monitoring
- Auto-migrations with Alembic

## Quick Start with Docker

```bash
docker build -t kanchi .
docker run -p 8765:8765 -p 3000:3000 \
  -e RABBITMQ_URL=amqp://guest:guest@localhost:5672// \
  kanchi
```

Access at `http://localhost:3000`

## Configuration

### Required

```bash
RABBITMQ_URL=amqp://guest:guest@localhost:5672//
```

### Optional

```bash
DATABASE_URL=<postgresql://user:pass@localhost:5432/kanchi>  # Default: SQLite
WS_HOST=localhost
WS_PORT=8765
LOG_LEVEL=INFO
```

Migrations run automatically on startup.

## Local Development

### Prerequisites

- Python 3.8+
- Poetry
- Node.js 20+
- RabbitMQ

### Installation

```bash
cd agent && poetry install
cd ../frontend && npm install
```

### Run

```bash
# Use our makefile:
make dev

# Or manually:

# Terminal 1: Backend
cd agent && poetry run python app.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Testing Environment

```bash
cd scripts/test-celery-app
make start          # Start RabbitMQ, Redis, Workers
make test-mixed     # Generate test tasks
```

## Contributing

### Backend

```bash
cd agent
poetry run black .              # Format
poetry run ruff check .         # Lint
poetry run alembic revision --autogenerate -m "description"  # Migration
```

### Frontend

```bash
cd frontend
npm run build                   # Build
npx swagger-typescript-api generate -p http://localhost:8765/openapi.json -o app/src/types -n api.ts --modular
```

## License

Copyright 2025 Kanchi Project. Licensed for non-commercial use only. This license will automatically convert to Apache License 2.0 after 2 years from first public release. See LICENSE.txt for full details.
