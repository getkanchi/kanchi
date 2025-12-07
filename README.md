# Kanchi

Kanchi is a real-time Celery task monitoring (and management) system with an enjoyable user interface. It provides insights into task execution, worker health, and task statistics.

## Features

- Real-time task monitoring via WebSocket
- Task filtering and searching (date range, status, name, worker, full-text)
- Task retry tracking and orphan detection
- Daily task statistics and history
- Worker health monitoring
- Auto-migrations with Alembic

## Backend-hosted UI

- Backend can serve the built frontend at `/ui`.
- Point `FRONTEND_DIST_DIR` to the directory containing the built assets (defaults to `agent/ui`).
- The requested `index.html` is transformed to inject all `NUXT_PUBLIC_*` variables at runtime (cached when `FRONTEND_CACHE_INDEX=true`).
- Build static assets for backend hosting with `./scripts/build-frontend-ui.sh` or `make build-ui` (output to `agent/ui`).
- Docker builds bake the generated UI into the backend image and run only the FastAPI process (UI at `/ui`).
- Customize the base path during Docker builds with `--build-arg UI_BASE_PATH=/custom/`.

## Screenshots

### Dashboard
![Dashboard](.github/images/dashboard.png)

### Task Registry
![Task Registry](.github/images/task_registry.png)

## Quick Start (Docker Compose)

Run Kanchi using pre-built images from Docker Hub. No repository cloning required—just set a few environment variables and start the container. The container runs a single FastAPI process and serves the UI from `/ui` on port 8765 (no separate frontend port).

### Prerequisites

- Docker Engine + Docker Compose plug-in installed on your host. Follow the [official Docker installation guide](https://docs.docker.com/engine/install/) for your OS.
- Running Celery broker (RabbitMQ or Redis) instance (and optionally PostgreSQL) reachable from the host.

1. **Create a docker-compose.yaml file**

   Create a new directory and save the following as `docker-compose.yaml`:

   ```yaml
   services:
     kanchi:
       image: getkanchi/kanchi:latest
       container_name: kanchi
       ports:
         - "8765:8765"
        environment:
          # Required: Your Celery broker connection string
          CELERY_BROKER_URL: ${CELERY_BROKER_URL}

         # Optional: Database (defaults to SQLite)
         DATABASE_URL: ${DATABASE_URL:-sqlite:////data/kanchi.db}

         # Optional: Logging and development
         LOG_LEVEL: ${LOG_LEVEL:-INFO}
         DEVELOPMENT_MODE: ${DEVELOPMENT_MODE:-false}
         ENABLE_PICKLE_SERIALIZATION: ${ENABLE_PICKLE_SERIALIZATION:-false}

         # Optional: Frontend URLs
         NUXT_PUBLIC_API_URL: ${NUXT_PUBLIC_API_URL:-http://localhost:8765}
         NUXT_PUBLIC_WS_URL: ${NUXT_PUBLIC_WS_URL:-ws://localhost:8765/ws}

         # Optional: Authentication (disabled by default)
         AUTH_ENABLED: ${AUTH_ENABLED:-false}

         # Optional: Basic HTTP authentication
         AUTH_BASIC_ENABLED: ${AUTH_BASIC_ENABLED:-false}
         BASIC_AUTH_USERNAME: ${BASIC_AUTH_USERNAME}
         BASIC_AUTH_PASSWORD_HASH: ${BASIC_AUTH_PASSWORD_HASH}

         # Optional: OAuth providers
         AUTH_GOOGLE_ENABLED: ${AUTH_GOOGLE_ENABLED:-false}
         GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
         GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
         AUTH_GITHUB_ENABLED: ${AUTH_GITHUB_ENABLED:-false}
         GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID}
         GITHUB_CLIENT_SECRET: ${GITHUB_CLIENT_SECRET}
         OAUTH_REDIRECT_BASE_URL: ${OAUTH_REDIRECT_BASE_URL}

         # Optional: Email restrictions for OAuth
         ALLOWED_EMAIL_PATTERNS: ${ALLOWED_EMAIL_PATTERNS}

         # Optional: CORS and host controls
         ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
         ALLOWED_HOSTS: ${ALLOWED_HOSTS}

         # Optional: Security tokens (generate with: openssl rand -hex 32)
         SESSION_SECRET_KEY: ${SESSION_SECRET_KEY}
         TOKEN_SECRET_KEY: ${TOKEN_SECRET_KEY}
       volumes:
         - kanchi-data:/data
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8765/api/health"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 40s

   volumes:
     kanchi-data:
   ```

2. **Set required environment values**

   At minimum, export `CELERY_BROKER_URL` or place it in a `.env` file alongside `docker-compose.yaml`. Example:

   ```bash
   # For RabbitMQ:
   export CELERY_BROKER_URL=amqp://user:pass@rabbitmq-host:5672//

   # For Redis:
   export CELERY_BROKER_URL=redis://localhost:6379/0
   ```

   Optional overrides (see docker-compose.yaml for all available options):

   ```bash
   export DATABASE_URL=postgresql://user:pass@postgres-host:5432/kanchi
   export LOG_LEVEL=INFO
   export DEVELOPMENT_MODE=false
   export ENABLE_PICKLE_SERIALIZATION=false
   export NUXT_PUBLIC_API_URL=http://your-kanchi-host:8765
   export NUXT_PUBLIC_WS_URL=ws://your-kanchi-host:8765/ws

   # Authentication / security (all optional)
   export AUTH_ENABLED=true
   export AUTH_BASIC_ENABLED=true
   export BASIC_AUTH_USERNAME=kanchi-admin
   export BASIC_AUTH_PASSWORD_HASH=pbkdf2_sha256$260000$mysalt$N8Dk...  # see below

   # OAuth
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
   export ALLOWED_ORIGINS=https://your-kanchi-host,http://localhost:8765
   export ALLOWED_HOSTS=your-kanchi-host,localhost,127.0.0.1

   # Token secrets (must be non-default in production)
   export SESSION_SECRET_KEY=$(openssl rand -hex 32)
   export TOKEN_SECRET_KEY=$(openssl rand -hex 32)

# Pickle payloads (advanced; defaults to off)
export ENABLE_PICKLE_SERIALIZATION=false
   ```

3. **Start or update Kanchi in one command**

   ```bash
   docker compose up -d --pull always
   ```

   Re-run the same command to pull the latest image and restart the container.

4. **Visit the app**

   - Frontend: `http://localhost:8765/ui`
   - API / Docs: `http://localhost:8765`

5. **Optional commands**

   ```bash
   docker compose logs -f kanchi      # Tail logs
   docker compose down                # Stop and remove the container
   docker compose restart kanchi      # Restart the container
   docker compose pull                # Pull latest image without restarting
   ```

Kanchi expects a Celery broker (RabbitMQ or Redis) and (if desired) PostgreSQL to be managed separately—point `CELERY_BROKER_URL` and `DATABASE_URL` to the infrastructure you already run.

Migrations run automatically on startup.

### Pickle payloads (opt-in)

Kanchi rejects pickle-serialized messages by default for safety. If your Celery producers emit `application/x-python-serialize`, set `ENABLE_PICKLE_SERIALIZATION=true` only when you fully trust all producers and the broker. See `pickle.md` for a short rundown.

### Authentication

Authentication is opt-in. When `AUTH_ENABLED=false` (the default) anyone who can reach the backend may read metrics and connect over WebSockets. Enable authentication to require access tokens for all API routes and WebSocket connections.

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
npx swagger-typescript-api generate -p http://localhost:8765/openapi.json -o app/src/types -n api.ts --http-client axios
```

## Getting Help

Have questions, feedback, or want to connect with other Kanchi users? Join our community on Discord:

[![Discord](https://img.shields.io/badge/Discord-Join%20us-5865F2?logo=discord&logoColor=white)](https://discord.gg/gSp9wsu3k)

## License

Licensed under [MIT](LICENSE)
