# Test Celery Application for Kanchi

This is a comprehensive Celery application designed for testing the Kanchi monitoring platform. It includes various task types and scenarios to thoroughly test monitoring capabilities.

## Features

- **Multiple task types**: Simple, long-running, failing, priority-based, resource-intensive
- **Workflow patterns**: Chains, groups, chords
- **Error scenarios**: Timeouts, exceptions, retries
- **Queue routing**: Multiple queues with different priorities
- **Periodic tasks**: Scheduled tasks via Celery Beat
- **Resource monitoring**: CPU, memory, and IO intensive tasks

## Setup

### Using Docker Compose (Recommended)

1. Start all services:
```bash
docker-compose up -d
```

This will start:
- RabbitMQ (broker) on port 5672, Management UI on port 15672
- Redis (result backend) on port 6379
- Flower (monitoring UI) on port 5555
- 3 Celery workers with different configurations
- Celery Beat scheduler

2. Generate test tasks:
```bash
docker-compose run --rm worker1 python test_producer.py --mode mixed --duration 60
```

### Using Poetry (Local Development)

1. Install dependencies:
```bash
poetry install
```

2. Start RabbitMQ and Redis:
```bash
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management-alpine
docker run -d -p 6379:6379 redis:7-alpine
```

3. Start a worker:
```bash
poetry run python run_worker.py --queues default,high_priority --events
```

4. Generate tasks:
```bash
poetry run python test_producer.py --mode mixed
```

## Task Producer Usage

The `test_producer.py` script can generate various types of tasks:

```bash
# Generate simple tasks
python test_producer.py --mode simple --count 20

# Generate long-running tasks
python test_producer.py --mode long --count 5

# Generate failing tasks (with retries)
python test_producer.py --mode failing --count 10

# Generate priority-based tasks
python test_producer.py --mode priority --count 15

# Generate resource-intensive tasks
python test_producer.py --mode resource --count 5

# Generate workflow tasks (chains, groups, chords)
python test_producer.py --mode workflow --count 3

# Generate error tasks
python test_producer.py --mode error --count 5

# Generate mixed load for 60 seconds
python test_producer.py --mode mixed --duration 60

# Stress test with 1000 tasks
python test_producer.py --mode stress --count 1000 --burst
```

Options:
- `--rate`: Task generation rate (tasks per second)
- `--burst`: Generate all tasks immediately without delays
- `--count`: Number of tasks to generate
- `--duration`: Duration for mixed mode (seconds)

## Worker Configuration

Start workers with different configurations:

```bash
# Default worker
python run_worker.py

# High concurrency worker
python run_worker.py --concurrency 10 --queues default,high_priority

# Autoscaling worker
python run_worker.py --autoscale 10,2 --queues default

# Thread pool for IO tasks
python run_worker.py --pool threads --concurrency 20 --queues io_intensive

# Solo pool for debugging
python run_worker.py --pool solo --loglevel debug
```

## Monitoring

### RabbitMQ Management
- URL: http://localhost:15672
- Username: guest
- Password: guest

### Flower
- URL: http://localhost:5555

### Kanchi Agent
When testing Kanchi, set CELERY_BROKER_URL to point to your broker:
- RabbitMQ: amqp://guest:guest@localhost:5672//
- Redis: redis://localhost:6379/0
- Result Backend: redis://localhost:6379/0

## Task Types

### Simple Tasks
- `simple_task`: Basic arithmetic operations
- `random_delay_task`: Tasks with random execution times

### Long Running Tasks
- `long_running_task`: Tasks with progress updates
- Duration configurable from 5-20 seconds

### Failing Tasks
- `failing_task`: Tasks that fail and retry (max 3 retries)
- `error_types_task`: Different error scenarios (timeout, exception, division by zero)

### Priority Tasks
- `high_priority_task`: Routed to high_priority queue
- `low_priority_task`: Routed to low_priority queue

### Resource Intensive Tasks
- `cpu_intensive_task`: Prime number calculations
- `io_intensive_task`: Simulated file operations
- `memory_intensive_task`: Memory allocation tests

### Workflow Tasks
- Chain: Sequential task execution
- Group: Parallel task execution
- Chord: Group with callback

### Periodic Tasks
- `periodic_task`: Runs every 30 seconds
- `health_check`: Runs every minute

## Testing Scenarios

### 1. Normal Load
```bash
python test_producer.py --mode simple --count 50 --rate 2
```

### 2. High Load
```bash
python test_producer.py --mode stress --count 5000 --burst
```

### 3. Mixed Workload
```bash
python test_producer.py --mode mixed --duration 300 --rate 5
```

### 4. Failure Testing
```bash
python test_producer.py --mode failing --count 20
python test_producer.py --mode error --count 10
```

### 5. Queue Distribution
```bash
# Start multiple producers for different queues
python test_producer.py --mode priority --count 100 &
python test_producer.py --mode resource --count 50 &
```

## Cleanup

Stop all services:
```bash
docker-compose down -v
```