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
- Running Celery broker (RabbitMQ or Redis) instance (and optionally PostgreSQL) reachable from the host.

1. **Create a directory and download the compose file**

   ```bash
   mkdir kanchi && cd kanchi
   curl -O https://raw.githubusercontent.com/<YOUR_ORG_OR_USER>/kanchi/main/docker-compose.yaml
   ```

   Replace `<YOUR_ORG_OR_USER>` with the GitHub namespace that hosts your Kanchi fork (for example, `kanchi-project`). The downloaded `docker-compose.yaml` contains sensible defaults and expects you to provide a Celery broker connection string—Kanchi does not manage your broker or database.

2. **Set required environment values**

   At minimum, export `CELERY_BROKER_URL` or place it in a `.env` file alongside `docker-compose.yaml`. Example:

   ```bash
   # For RabbitMQ:
   export CELERY_BROKER_URL=amqp://user:pass@rabbitmq-host:5672//

   # For Redis:
   export CELERY_BROKER_URL=redis://localhost:6379/0
   ```

   Optional overrides (fallback defaults shown in `docker-compose.yaml`):

   ```bash
   export DATABASE_URL=sqlite:////data/kanchi.db
   export LOG_LEVEL=INFO
   export DEVELOPMENT_MODE=false
   export NUXT_PUBLIC_API_URL=http://your-kanchi-host:8765
   export NUXT_PUBLIC_WS_URL=ws://your-kanchi-host:8765/ws
   # Authentication / security (all optional)
    
    # Toggle authentication globally (defaults to false for backward compatibility)
    export AUTH_ENABLED=true

    # Basic HTTP auth (PBKDF2 hash recommended)
    export AUTH_BASIC_ENABLED=true
    export BASIC_AUTH_USERNAME=kanchi-admin
    export BASIC_AUTH_PASSWORD_HASH=pbkdf2_sha256$260000$mysalt$N8Dk...  # see below

    # OAuth (set redirect base URL to the public address of the backend)
    export AUTH_GOOGLE_ENABLED=true
    export GOOGLE_CLIENT_ID=...
    export GOOGLE_CLIENT_SECRET=...
    export AUTH_GITHUB_ENABLED=true
    export GITHUB_CLIENT_ID=...
    export GITHUB_CLIENT_SECRET=...
    export OAUTH_REDIRECT_BASE_URL=https://your-kanchi-host

    # Allowed email addresses for OAuth logins (wildcards supported)
    export ALLOWED_EMAIL_PATTERNS='*@example.com,*@example.org'

    # CORS and host controls
    export ALLOWED_ORIGINS=https://your-kanchi-host,http://localhost:3000
    export ALLOWED_HOSTS=your-kanchi-host,localhost,127.0.0.1
    
    # Token secrets (must be non-default in production)
    export SESSION_SECRET_KEY=$(openssl rand -hex 32)
    export TOKEN_SECRET_KEY=$(openssl rand -hex 32)
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

Kanchi expects a Celery broker (RabbitMQ or Redis) and (if desired) PostgreSQL to be managed separately—point `CELERY_BROKER_URL` and `DATABASE_URL` to the infrastructure you already run.

Migrations run automatically on startup.

### Authentication

Authentication is opt-in. When `AUTH_ENABLED=false` (the default) Kanchi behaves exactly as before—anyone who can reach the backend may read metrics and connect over WebSockets. Enable authentication to require access tokens for all API routes and WebSocket connections.

#### Basic HTTP authentication

1. Generate a PBKDF2 hash for the password (for example using Python):

   ```bash
   python - <<'PY'
   import os, base64, hashlib

   password = os.environ.get('KANCHI_BASIC_PASSWORD', 'change-me').encode('utf-8')
   salt = base64.b64encode(os.urandom(16)).decode('ascii').strip('=')
   iterations = 260000
   dk = hashlib.pbkdf2_hmac('sha256', password, salt.encode('utf-8'), iterations)
   print(f"pbkdf2_sha256${iterations}${salt}${base64.b64encode(dk).decode('ascii')}")
   PY
   ```

2. Set `AUTH_ENABLED=true`, `AUTH_BASIC_ENABLED=true`, `BASIC_AUTH_USERNAME`, and `BASIC_AUTH_PASSWORD_HASH` (or `BASIC_AUTH_PASSWORD` for local testing only).

#### OAuth (Google, GitHub)

1. Configure `AUTH_GOOGLE_ENABLED` and/or `AUTH_GITHUB_ENABLED` with the provider credentials.
2. Set `OAUTH_REDIRECT_BASE_URL` to the publicly reachable backend URL (e.g., `https://kanchi.example.com`).
3. Add allowed email patterns via `ALLOWED_EMAIL_PATTERNS` to restrict who can sign in.
4. The frontend exposes convenient buttons for OAuth providers once enabled.

Every login issues short-lived access tokens plus refresh tokens. You can adjust lifetimes through `ACCESS_TOKEN_LIFETIME_MINUTES` and `REFRESH_TOKEN_LIFETIME_HOURS` if required.

## Local Development

### Prerequisites

- Python 3.8+
- Poetry
- Node.js 20+
- Celery broker (RabbitMQ or Redis)

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
