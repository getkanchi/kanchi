This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanchi is a Celery task monitoring system with a Python FastAPI backend and Nuxt.js frontend. The backend monitors Celery events via message broker and provides real-time WebSocket updates to the frontend.

## Development Commands

### Quick Start (from root directory)
```bash
# Start both backend and frontend in development mode
make dev

# View unified logs (backend and frontend)
make logs

# Start backend only
make backend

# Start frontend only
make frontend
```

### Backend (from `agent/` directory)
```bash
# Run the backend server (recommended)
poetry run python app.py

# Alternative legacy entry point
poetry run python main.py

# Run with custom broker
poetry run python app.py --broker amqp://guest:guest@localhost:5672//

# Development with auto-reload
poetry run python main.py --reload

# Linting and formatting
poetry run black .
poetry run ruff check .
poetry run mypy .

# Database migrations (Alembic)
poetry run alembic current              # Check current migration version
poetry run alembic upgrade head         # Apply all pending migrations
poetry run alembic revision --autogenerate -m "Description"  # Create new migration
```

### Frontend (from `frontend/` directory)
```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Generate static site
npm run generate

# Regenerate types from backend OpenAPI
npx swagger-typescript-api generate -p http://localhost:8765/openapi.json -o app/src/types -n api.ts --modular
```

### Testing Environment (from `scripts/test-celery-app/`)
```bash
# Start test environment (RabbitMQ, Redis, Workers)
make start

# Generate test tasks
make test-simple    # Simple tasks
make test-mixed     # Mixed load for 60 seconds  
make test-stress    # 1000 tasks stress test
make test-failing   # Failing tasks

# Monitor services
make monitor        # Open RabbitMQ and Flower UIs
make logs           # Show all service logs
make status         # Check service health
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t kanchi .
docker run -p 8765:8765 -p 3000:3000 kanchi

# Or use Docker Compose (from root)
docker-compose up

# With custom broker URL
docker run -p 8765:8765 -p 3000:3000 -e CELERY_BROKER_URL=amqp://user:pass@host:5672// kanchi
```

## Architecture

### Backend Structure (`agent/`)
- **`app.py`**: Main FastAPI application with WebSocket support and integrated frontend serving
- **`main.py`**: Legacy entry point (redirects to FastAPI app)
- **`monitor.py`**: Core Celery event monitoring via `CeleryEventMonitor`
- **`database.py`**: SQLite database manager with SQLAlchemy async support
- **`models.py`**: Pydantic data models for tasks, workers, events
- **`database_models.py`**: SQLAlchemy database models
- **`api/`**: REST API routes organized by resource (tasks, workers, websockets)
- **`services/`**: Business logic services for task and worker management
- **`connection_manager.py`**: WebSocket connection management
- **`event_handler.py`**: Celery event processing and broadcasting
- **`config.py`**: Configuration management

### Frontend Structure (`frontend/`)
- **Framework**: Nuxt 4 (Vue 3) with TypeScript
- **UI**: TailwindCSS + Radix UI components (reka-ui)
- **State**: Pinia stores for centralized state management
- **Types**: Auto-generated from backend OpenAPI schema in `app/src/types/`
- **Services**: Centralized API service layer using generated types

### Key Patterns
- **Type Safety**: All API interactions use auto-generated TypeScript types
- **Real-time Updates**: WebSocket broadcasts for live task monitoring
- **Persistence**: SQLite database for task history and worker state
- **Background Jobs**: Async tasks for orphan detection and cleanup
- **Integrated Serving**: FastAPI serves both API and built frontend

## Database

Uses SQLAlchemy with Alembic migrations for schema management. Supports:
- **SQLite** (default, for development)
- **PostgreSQL** (recommended for production)

### Features
- Task persistence and history
- Worker status tracking
- Orphan task detection and retry batches
- Comprehensive indexing for performance

### Migration System
- **Tool**: Alembic for database migrations
- **Auto-run**: Migrations execute automatically on app startup
- **BYOD**: Bring-Your-Own-Database via `DATABASE_URL` environment variable

Database models defined in `agent/database.py`.

## Logging

Kanchi uses a unified logging system that captures logs from both backend and frontend in a single file. **This feature is only available in development mode.**

### Enabling Logging
Set the `DEVELOPMENT_MODE` environment variable to enable unified logging:
```bash
export DEVELOPMENT_MODE=true
```

The `make dev` command automatically enables development mode.

### Log File
- **Location**: `agent/kanchi.log`
- **Format**: Timestamped logs with source prefix `[BACKEND]` or `[FRONTEND]`
- **Behavior**: Cleaned on backend startup (only in development mode)

### Viewing Logs
```bash
# Tail logs (last 100 lines and follow)
make logs

# Or manually
tail -n 100 -f agent/kanchi.log
```

### Frontend Logging
```typescript
// Use the logger service in frontend code
import { useLogger } from '~/services/logger'

const logger = useLogger()

logger.debug('Debug message', { context: 'data' })
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message', { error: 'details' })
logger.critical('Critical message')
```

Frontend logs are sent to the backend via `/api/logs/frontend` and written to the unified log file (only in development mode).

## Configuration

### Environment Variables
```bash
# Backend
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
WS_HOST=localhost
WS_PORT=8765
DATABASE_URL=sqlite:///kanchi.db
DEVELOPMENT_MODE=true  # Enable unified logging (default: false)
LOG_LEVEL=INFO
LOG_FILE=kanchi.log

# Frontend (Nuxt runtime config)
NUXT_PUBLIC_API_URL=http://localhost:8765
NUXT_PUBLIC_WS_URL=ws://localhost:8765/ws

# Docker environment
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
NITRO_PORT=3000
NITRO_HOST=0.0.0.0
```

### Code Standards
- **Python**: Black formatting, Ruff linting, MyPy type checking
- **Line length**: 100 characters for Python
- **Python version**: 3.8+ minimum

## Development Workflow

1. **Backend changes**: Restart FastAPI server (`poetry run python app.py`)
2. **Frontend changes**: Auto-reload via `npm run dev`
3. **API changes**: Regenerate frontend types after schema updates
4. **Database changes**: Use SQLAlchemy async session patterns
5. **Testing**: Use test environment in `scripts/test-celery-app/`

## Key Files and Locations

### Configuration Files
- **`agent/pyproject.toml`**: Python dependencies and tool configuration
- **`frontend/package.json`**: Node.js dependencies and scripts
- **`Dockerfile`**: Multi-stage build for production deployment
- **`scripts/test-celery-app/docker-compose.yml`**: Test environment setup

### Documentation
- **`ARCHITECTURE_ROADMAP.md`**: Detailed system architecture and future plans
- **`FRONTEND_ARCHITECTURE.md`**: Frontend patterns and best practices
- **`KANCHI_DATABASE_SCHEMA.md`**: Complete database schema documentation

### Auto-generated (DO NOT EDIT)
- **`frontend/app/src/types/`**: TypeScript types from backend OpenAPI schema

## FastAPI Integration

The main application (`app.py`) integrates:
- **API endpoints**: RESTful API for task and worker management
- **WebSocket**: Real-time event broadcasting
- **Static files**: Serves built Nuxt.js frontend
- **Background tasks**: Celery event monitoring and database operations

Access points:
- **API**: `http://localhost:8765/api/*`
- **WebSocket**: `ws://localhost:8765/ws`
- **Frontend**: `http://localhost:8765/` (serves Nuxt.js app)
- **OpenAPI docs**: `http://localhost:8765/docs`

## Common Development Tasks

### Adding New API Endpoint
1. Add route in appropriate `api/` module
2. Update OpenAPI schema if needed
3. Regenerate frontend types
4. Add method to appropriate Pinia store
5. Use in components via store

### Database Schema Changes
1. Update SQLAlchemy models in `database_models.py`
2. Create migration script if needed
3. Test with development database
4. Update related Pydantic models in `models.py`

### WebSocket Event Broadcasting
1. Add event type to `event_handler.py`
2. Update WebSocket message handling in `connection_manager.py`
3. Handle in frontend WebSocket store
4. Update UI components to react to new events

When making changes, always consider the real-time nature of the system and ensure WebSocket broadcasts continue working for live monitoring updates.
