.PHONY: help install start stop restart logs clean test-simple test-mixed test-stress monitor

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install

start: ## Start all services with Docker Compose
	docker-compose up -d
	@echo "Services started!"
	@echo "RabbitMQ Management: http://localhost:15672 (guest/guest)"
	@echo "Flower: http://localhost:5555"
	@echo "Redis: localhost:6379"

stop: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-workers: ## Show logs from workers only
	docker-compose logs -f worker1 worker2 worker3

clean: ## Stop services and remove volumes
	docker-compose down -v

build: ## Build Docker images
	docker-compose build

shell: ## Open shell in worker container
	docker-compose run --rm worker1 /bin/bash

test-simple: ## Generate simple test tasks
	docker-compose run --rm worker1 python test_producer.py --mode simple --count 1

test-mixed: ## Generate mixed load for 60 seconds
	docker-compose run --rm worker1 python test_producer.py --mode mixed --duration 60

test-stress: ## Run stress test with 1000 tasks
	docker-compose run --rm worker1 python test_producer.py --mode stress --count 1000 --burst

test-failing: ## Generate failing tasks
	docker-compose run --rm worker1 python test_producer.py --mode failing --count 10

test-priority: ## Generate priority tasks
	docker-compose run --rm worker1 python test_producer.py --mode priority --count 20

test-resource: ## Generate resource intensive tasks
	docker-compose run --rm worker1 python test_producer.py --mode resource --count 10

test-workflow: ## Generate workflow tasks
	docker-compose run --rm worker1 python test_producer.py --mode workflow --count 5

monitor: ## Open monitoring UIs
	@echo "Opening monitoring UIs..."
	@open http://localhost:15672 2>/dev/null || xdg-open http://localhost:15672 2>/dev/null || echo "RabbitMQ: http://localhost:15672"
	@open http://localhost:5555 2>/dev/null || xdg-open http://localhost:5555 2>/dev/null || echo "Flower: http://localhost:5555"

worker-local: ## Run a local worker (requires local RabbitMQ/Redis)
	poetry run python run_worker.py --queues default,high_priority --events --hostname local-worker@%h

producer-local: ## Run local producer (requires local RabbitMQ/Redis)
	poetry run python test_producer.py --mode mixed --duration 30

status: ## Check service status
	@docker-compose ps
	@echo "\nService Health:"
	@docker-compose exec -T rabbitmq rabbitmq-diagnostics ping 2>/dev/null && echo "✓ RabbitMQ is healthy" || echo "✗ RabbitMQ is not responding"
	@docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG && echo "✓ Redis is healthy" || echo "✗ Redis is not responding"

scale-workers: ## Scale workers up
	docker-compose up -d --scale worker1=3 --scale worker2=2

inspect-queue: ## Inspect RabbitMQ queues
	@docker-compose exec rabbitmq rabbitmqctl list_queues name messages messages_ready messages_unacknowledged
