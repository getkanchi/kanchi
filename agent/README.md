# Celery Event Monitor with FastAPI & WebSocket Broadcasting

A FastAPI application that monitors Celery task events and provides both REST API endpoints and real-time WebSocket broadcasting to connected clients.

## Features

- **FastAPI Web Interface**: Built-in web dashboard for monitoring tasks
- **REST API**: RESTful endpoints for task statistics and event history
- **Real-time WebSocket**: Live streaming of Celery task events
- **Task Statistics**: Track success/failure rates, active tasks, and more
- **Event Filtering**: Subscribe to specific event types or task names
- **Typed Models**: Full Pydantic models for all API responses
- **Support for all Celery event types**:
  - task-sent
  - task-received  
  - task-started
  - task-succeeded
  - task-failed
  - task-retried
  - task-revoked

## Installation

### Using Poetry (recommended)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
cd agent
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
# Install from pyproject.toml
pip install .
```

## Usage

### Start the server

```bash
# Start FastAPI server (recommended)
poetry run python app.py

# Or using the FastAPI script entry point
poetry run celery-monitor-server

# Legacy CLI interface (redirects to FastAPI)
poetry run python main.py

# Custom options
poetry run python main.py --broker amqp://guest@localhost// --host 0.0.0.0 --port 8080

# Development mode with auto-reload
poetry run python main.py --reload --log-level DEBUG

# Using uvicorn directly
poetry run uvicorn app:app --host 0.0.0.0 --port 8765 --reload
```

### Environment Variables

You can also configure via environment variables:

```bash
export CELERY_BROKER_URL=amqp://guest@localhost//
export WS_HOST=0.0.0.0
export WS_PORT=8765
export LOG_LEVEL=INFO
poetry run python app.py
```

## API Endpoints

### Web Interface

Visit `http://localhost:8765` for a built-in web dashboard that shows real-time task events.

### REST API

- `GET /api/stats` - Current task statistics (total, succeeded, failed, active, etc.)
- `GET /api/events/recent?limit=100` - Recent task events
- `GET /api/events/{task_id}` - Events for a specific task
- `GET /api/tasks/active` - Currently active tasks
- `GET /api/health` - Health check and service status
- `GET /docs` - Interactive Swagger API documentation
- `GET /redoc` - Alternative API documentation

### WebSocket API

Connect to `ws://localhost:8765/ws` (or your configured host/port)

### Event Format

Events are broadcast as JSON with the following structure:

```json
{
  "task_id": "9b31f2ce-5ea8-4bc9-8cd1-f8950f7a2c44",
  "task_name": "tasks.io_intensive_task",
  "event_type": "task-succeeded",
  "timestamp": "2025-09-16T04:45:52.013214",
  "args": "()",
  "kwargs": "{'file_operations': 15}",
  "retries": 0,
  "result": "{'operations': 15, 'results': [...]}",
  "runtime": 1.5499710419680923,
  "exchange": "",
  "routing_key": "io_intensive",
  "root_id": "9b31f2ce-5ea8-4bc9-8cd1-f8950f7a2c44"
}
```

### Client Messages

Clients can send:

- **Ping**: `{"type": "ping"}` - Receives pong response
- **Subscribe**: `{"type": "subscribe", "filters": {"event_types": ["task-failed"], "task_names": ["my_task"]}}` - Filter events by type or task name

## Testing

Use the provided test client to connect and view events:

```bash
# With Poetry
poetry run python test_client.py

# Or from outside the agent directory
cd agent && poetry run python test_client.py
```

## Quick Start

1. **Install dependencies**:
   ```bash
   cd agent && poetry install
   ```

2. **Start the server**:
   ```bash
   poetry run python app.py
   ```

3. **Open your browser** to `http://localhost:8765` to see the web interface

4. **Start some Celery tasks** in your application and watch them appear in real-time!

5. **Explore the API** at `http://localhost:8765/docs`

## Architecture

- `app.py` - FastAPI application with REST API and WebSocket endpoints
- `models.py` - Pydantic models and dataclasses for task events
- `monitor.py` - Celery event monitoring logic
- `main.py` - Legacy CLI interface (now redirects to FastAPI)
- `config.py` - Configuration management
- `test_client.py` - WebSocket test client