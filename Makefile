.PHONY: dev logs backend frontend help

help:
	@echo "Kanchi Development Commands"
	@echo "==========================="
	@echo "make dev      - Start both backend and frontend in development mode"
	@echo "make logs     - Tail unified log file (last 100 lines and follow)"
	@echo "make backend  - Start backend only"
	@echo "make frontend - Start frontend only"

dev:
	@echo "Starting Kanchi in development mode..."
	@echo "Backend will run on http://localhost:8765"
	@echo "Frontend will run on http://localhost:3000"
	@echo "Unified logging enabled at agent/kanchi.log"
	@echo ""
	@trap 'kill 0' EXIT; \
	(cd agent && DEVELOPMENT_MODE=true poetry run python app.py) & \
	(cd frontend && npm run dev) & \
	wait

backend:
	@echo "Starting backend on http://localhost:8765..."
	@echo "To enable unified logging, set DEVELOPMENT_MODE=true"
	cd agent && poetry run python app.py

frontend:
	@echo "Starting frontend on http://localhost:3000..."
	cd frontend && npm run dev

logs:
	@echo "Tailing unified log file (Ctrl+C to stop)..."
	tail -n 100 -f agent/kanchi.log
