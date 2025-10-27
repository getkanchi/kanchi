# Kanchi

Kanchi is a real-time Celery task monitoring (and management) system with an enjoyable user interface. It provides insights into task execution, worker health, and task statistics.

## Features

- Real-time task monitoring via WebSocket
- Task filtering and searching (date range, status, name, worker, full-text)
- Task retry tracking and orphan detection
- Daily task statistics and history
- Worker health monitoring
- Auto-migrations with Alembic

## Screenshots

### Dashboard
![Dashboard](.github/images/dashboard.png)

### Task Registry
![Task Registry](.github/images/task_registry.png)

## Quick Start (Docker Compose)

These steps mirror the Docmost deployment experience—download the compose file, set a few environment variables, and bring the stack up with a single command.

### Prerequisites

- Docker Engine + Docker Compose plug-in installed on your host. Follow the [official Docker installation guide](https://docs.docker.com/engine/install/) for your OS.
- Running RabbitMQ instance (and optionally PostgreSQL) reachable from the host.

1. **Create a directory and download the compose file**

   ```bash
   mkdir kanchi && cd kanchi
   curl -O https://raw.githubusercontent.com/<YOUR_ORG_OR_USER>/kanchi/main/docker-compose.yaml
   ```

   Replace `<YOUR_ORG_OR_USER>` with the GitHub namespace that hosts your Kanchi fork (for example, `kanchi-project`). The downloaded `docker-compose.yaml` contains sensible defaults and expects you to provide a RabbitMQ connection string—Kanchi does not manage your broker or database.

2. **Set required environment values**

   At minimum, export `RABBITMQ_URL` or place it in a `.env` file alongside `docker-compose.yaml`. Example:

   ```bash
   export RABBITMQ_URL=amqp://user:pass@rabbitmq-host:5672//
   ```

   Optional overrides (fallback defaults shown in `docker-compose.yaml`):

   ```bash
   export DATABASE_URL=sqlite:////data/kanchi.db
   export LOG_LEVEL=INFO
   export DEVELOPMENT_MODE=false
   export NUXT_PUBLIC_API_URL=http://your-kanchi-host:8765
   export NUXT_PUBLIC_WS_URL=ws://your-kanchi-host:8765/ws
   ```

3. **Start or update Kanchi in one command**

   ```bash
   docker compose -f docker-compose.yaml up -d --build --pull always --force-recreate
   ```

   Re-run the same command any time after pulling new code to rebuild and restart the container.

4. **Visit the app**

   - Frontend: `http://localhost:3000`
   - API / Docs: `http://localhost:8765`

5. **Optional commands**

   ```bash
   docker compose -f docker-compose.yaml logs -f kanchi   # Tail logs
   docker compose -f docker-compose.yaml down             # Stop and remove the container
   docker compose -f docker-compose.yaml restart kanchi   # Restart without rebuild
   ```

Kanchi expects RabbitMQ and (if desired) PostgreSQL to be managed separately—point `RABBITMQ_URL` and `DATABASE_URL` to the infrastructure you already run.

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
