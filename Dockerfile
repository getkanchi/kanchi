FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

ENV NUXT_APP_BASE_URL=/ui/

RUN NUXT_APP_BASE_URL="/ui/" npm run generate

FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY agent/pyproject.toml agent/poetry.lock* ./agent/
RUN pip install poetry && \
    cd agent && \
    poetry config virtualenvs.create false && \
    poetry install --without dev

COPY agent/ ./agent/
COPY --from=frontend-builder /app/frontend/.output/public ./agent/ui

ENV CELERY_BROKER_URL=amqp://guest:guest@localhost:5672// \
    WS_HOST=0.0.0.0 \
    WS_PORT=8765 \
    LOG_LEVEL=INFO \
    FRONTEND_DIST_DIR=/app/agent/ui \
    FRONTEND_CACHE_INDEX=true

EXPOSE 8765

WORKDIR /app/agent

CMD ["python", "app.py"]
