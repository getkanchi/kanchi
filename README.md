# Kanchi

## Running the Application

### Backend
```bash
cd agent
poetry run python main.py
```

### Frontend
```bash
cd frontend
npm run dev
```

### Using Makefile

```bash
cd scripts/test-celery-app
make test-mixed
etc.
```

### Docker

Build and run with Docker:
```bash
# Build image
docker build -t kanchi .

# Run with RabbitMQ on host machine (macOS/Windows)
docker run -p 8765:8765 -p 3000:3000 \
  -e RABBITMQ_URL=amqp://guest:guest@host.docker.internal:5672// \
  kanchi

# Run with RabbitMQ on another server/EC2
docker run -p 8765:8765 -p 3000:3000 \
  -e RABBITMQ_URL=amqp://user:pass@<rabbitmq-host>:5672// \
  kanchi

# Or use the helper script (auto-detects host networking)
./scripts/docker-run.sh --rabbitmq-host <host>
```

See [DOCKER_NETWORKING.md](./DOCKER_NETWORKING.md) for detailed networking configurations.

### Docker Compose
```bash
docker-compose up
```
