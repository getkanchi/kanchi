FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

RUN npm run build

FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY agent/pyproject.toml agent/poetry.lock* ./agent/
RUN pip install poetry && \
    cd agent && \
    poetry config virtualenvs.create false && \
    poetry install --without dev

COPY agent/ ./agent/

COPY --from=frontend-builder /app/frontend/.output ./frontend/.output
COPY --from=frontend-builder /app/frontend/package*.json ./frontend/

WORKDIR /app/frontend
RUN npm ci --production

WORKDIR /app

ENV RABBITMQ_URL=amqp://guest:guest@localhost:5672//
ENV WS_HOST=0.0.0.0
ENV WS_PORT=8765
ENV LOG_LEVEL=INFO
ENV NITRO_PORT=3000
ENV NITRO_HOST=0.0.0.0

EXPOSE 8765 3000

RUN echo '#!/bin/bash\n\
cd /app/agent && python main.py &\n\
cd /app/frontend && npm run preview &\n\
wait' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
