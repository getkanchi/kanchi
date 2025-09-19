# Kanchi - Modern Monitoring Platform MVP Plan

## Project Overview
Kanchi is a next-generation monitoring platform starting with a modern Celery monitoring tool to replace Flower. The platform will support both SaaS and self-hosting deployment models, with initial focus on self-hosting.

## Architecture Overview

### Components
1. **Agent (Go)** - Lightweight CLI agent that connects to Celery broker/backend
2. **Backend API (Go)** - REST API + WebSocket server for real-time updates
3. **Frontend (Vue3/Nuxt3)** - Modern reactive web UI
4. **Database (PostgreSQL)** - Time-series data storage for metrics

### Communication Flow
```
Celery Broker/Backend <- Agent (Go) -> WebSocket/HTTP -> Backend API -> Database
                                                    ^
                                                    |
                                                    v
                                            Frontend (Vue3/Nuxt3)
```

## MVP Features

### Core Functionality
1. **Real-time Task Monitoring**
   - Task status (pending, started, success, failure, retry)
   - Task execution time
   - Task arguments and results
   - Task queue distribution

2. **Worker Monitoring**
   - Active workers list
   - Worker status (online/offline)
   - Worker resource usage (CPU, memory)
   - Tasks per worker

3. **Queue Monitoring**
   - Queue lengths
   - Queue throughput
   - Message rates

4. **Basic Analytics**
   - Task success/failure rates
   - Average execution times
   - Task distribution charts
   - Time-series graphs for metrics

5. **Task Control**
   - View task details
   - Retry failed tasks
   - Revoke pending tasks

## Technology Stack

### Agent
- **Language**: Go
- **Libraries**:
  - github.com/streadway/amqp (RabbitMQ)
  - github.com/go-redis/redis (Redis)
  - github.com/gorilla/websocket (WebSocket client)
  - github.com/spf13/cobra (CLI framework)
  - github.com/spf13/viper (Configuration)

### Backend API
- **Language**: Go
- **Framework**: Fiber or Echo (high-performance web framework)
- **Libraries**:
  - github.com/gorilla/websocket (WebSocket server)
  - github.com/jmoiron/sqlx (Database)
  - github.com/golang-migrate/migrate (DB migrations)

### Frontend
- **Framework**: Nuxt 3
- **UI Library**: Tailwind CSS + shadcn/vue
- **State Management**: Pinia
- **Charts**: Chart.js or ApexCharts
- **WebSocket**: Native WebSocket API or socket.io-client

### Database
- **Primary**: PostgreSQL with TimescaleDB extension
- **Cache**: Redis (optional, for session/cache)

## Directory Structure

```
kanchi/
├── agent/                      # Go CLI Agent
│   ├── cmd/
│   │   └── kanchi-agent/
│   │       └── main.go
│   ├── internal/
│   │   ├── broker/            # Broker connections (RabbitMQ, Redis)
│   │   │   ├── rabbitmq.go
│   │   │   └── redis.go
│   │   ├── collector/         # Metrics collection
│   │   │   ├── tasks.go
│   │   │   ├── workers.go
│   │   │   └── queues.go
│   │   ├── config/
│   │   │   └── config.go
│   │   └── transport/         # WebSocket/HTTP client
│   │       └── client.go
│   ├── go.mod
│   ├── go.sum
│   └── Dockerfile
│
├── backend/                    # Go Backend API
│   ├── cmd/
│   │   └── api/
│   │       └── main.go
│   ├── internal/
│   │   ├── api/
│   │   │   ├── handlers/      # HTTP handlers
│   │   │   │   ├── tasks.go
│   │   │   │   ├── workers.go
│   │   │   │   ├── queues.go
│   │   │   │   └── metrics.go
│   │   │   ├── middleware/
│   │   │   │   └── cors.go
│   │   │   └── router.go
│   │   ├── websocket/         # WebSocket handlers
│   │   │   ├── hub.go
│   │   │   └── client.go
│   │   ├── models/            # Data models
│   │   │   ├── task.go
│   │   │   ├── worker.go
│   │   │   └── metric.go
│   │   ├── database/
│   │   │   ├── postgres.go
│   │   │   └── migrations/
│   │   └── service/           # Business logic
│   │       ├── task_service.go
│   │       ├── worker_service.go
│   │       └── metric_service.go
│   ├── go.mod
│   ├── go.sum
│   └── Dockerfile
│
├── frontend/                   # Nuxt 3 Frontend
│   ├── components/
│   │   ├── charts/
│   │   │   ├── TaskChart.vue
│   │   │   └── MetricChart.vue
│   │   ├── tasks/
│   │   │   ├── TaskList.vue
│   │   │   ├── TaskDetail.vue
│   │   │   └── TaskFilters.vue
│   │   ├── workers/
│   │   │   ├── WorkerList.vue
│   │   │   └── WorkerCard.vue
│   │   ├── queues/
│   │   │   └── QueueStatus.vue
│   │   └── layout/
│   │       ├── AppHeader.vue
│   │       ├── AppSidebar.vue
│   │       └── AppFooter.vue
│   ├── pages/
│   │   ├── index.vue          # Dashboard
│   │   ├── tasks/
│   │   │   ├── index.vue
│   │   │   └── [id].vue
│   │   ├── workers/
│   │   │   └── index.vue
│   │   ├── queues/
│   │   │   └── index.vue
│   │   └── analytics/
│   │       └── index.vue
│   ├── stores/
│   │   ├── tasks.ts
│   │   ├── workers.ts
│   │   └── metrics.ts
│   ├── composables/
│   │   ├── useWebSocket.ts
│   │   └── useApi.ts
│   ├── utils/
│   │   └── formatters.ts
│   ├── assets/
│   │   └── css/
│   │       └── main.css
│   ├── nuxt.config.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker/
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
│
├── scripts/
│   ├── setup.sh
│   └── test-celery-app/       # Sample Celery app for testing
│       ├── tasks.py
│       └── requirements.txt
│
├── docs/
│   ├── API.md
│   ├── AGENT_CONFIG.md
│   └── DEPLOYMENT.md
│
├── .github/
│   └── workflows/
│       ├── agent.yml
│       ├── backend.yml
│       └── frontend.yml
│
├── .gitignore
├── LICENSE
├── README.md
└── Makefile
```

## API Endpoints

### REST API
```
GET    /api/v1/tasks              # List tasks with pagination
GET    /api/v1/tasks/:id          # Get task details
POST   /api/v1/tasks/:id/retry    # Retry a task
DELETE /api/v1/tasks/:id          # Revoke a task

GET    /api/v1/workers            # List workers
GET    /api/v1/workers/:id        # Get worker details

GET    /api/v1/queues             # List queues
GET    /api/v1/queues/:name       # Get queue details

GET    /api/v1/metrics            # Get aggregated metrics
GET    /api/v1/metrics/timeseries # Get time-series data
```

### WebSocket Events
```
// From Agent to Backend
agent:register     # Agent registration
agent:metrics      # Periodic metrics update
agent:task         # Task event
agent:worker       # Worker event

// From Backend to Frontend
task:created       # New task
task:updated       # Task status change
worker:online      # Worker came online
worker:offline     # Worker went offline
metrics:update     # Metrics update
```

## Data Models

### Task
```go
type Task struct {
    ID          string    `json:"id"`
    Name        string    `json:"name"`
    Queue       string    `json:"queue"`
    Args        []any     `json:"args"`
    Kwargs      map[string]any `json:"kwargs"`
    Status      string    `json:"status"` // pending, started, success, failure, retry
    Result      any       `json:"result"`
    Error       string    `json:"error"`
    WorkerID    string    `json:"worker_id"`
    StartedAt   time.Time `json:"started_at"`
    CompletedAt time.Time `json:"completed_at"`
    Runtime     float64   `json:"runtime"`
    Retries     int       `json:"retries"`
}
```

### Worker
```go
type Worker struct {
    ID         string    `json:"id"`
    Hostname   string    `json:"hostname"`
    Status     string    `json:"status"` // online, offline
    Queues     []string  `json:"queues"`
    Concurrency int      `json:"concurrency"`
    CPU        float64   `json:"cpu_percent"`
    Memory     float64   `json:"memory_mb"`
    LastSeen   time.Time `json:"last_seen"`
    StartedAt  time.Time `json:"started_at"`
}
```

## Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up project structure
- [ ] Create basic Go agent that connects to Redis/RabbitMQ
- [ ] Implement WebSocket connection between agent and backend
- [ ] Set up database schema and migrations
- [ ] Create basic API endpoints

### Phase 2: Core Features (Week 3-4)
- [ ] Implement task monitoring in agent
- [ ] Build task list and detail views in frontend
- [ ] Add worker monitoring
- [ ] Implement real-time updates via WebSocket
- [ ] Create dashboard with basic metrics

### Phase 3: Analytics & Control (Week 5-6)
- [ ] Add time-series data collection
- [ ] Implement charts and graphs
- [ ] Add task retry/revoke functionality
- [ ] Queue monitoring and visualization
- [ ] Performance optimizations

### Phase 4: Polish & Testing (Week 7-8)
- [ ] Error handling and edge cases
- [ ] Performance testing with large datasets
- [ ] Documentation
- [ ] Docker packaging
- [ ] Deployment scripts

## Configuration

### Agent Configuration (kanchi-agent.yaml)
```yaml
# Celery broker connection
broker:
  type: redis  # or rabbitmq
  url: redis://localhost:6379/0
  
# Backend API connection
api:
  url: ws://localhost:8080/ws
  token: "" # For future auth
  
# Monitoring settings
monitoring:
  interval: 5s
  batch_size: 100
  
# Logging
log:
  level: info
  format: json
```

### Backend Configuration
```yaml
database:
  host: localhost
  port: 5432
  name: kanchi
  user: kanchi
  password: kanchi
  
server:
  port: 8080
  cors:
    enabled: true
    origins: ["http://localhost:3000"]
    
redis:
  url: redis://localhost:6379/1
  
metrics:
  retention: 30d
  aggregation: 1m
```

## Performance Targets

- Handle 10,000+ tasks/minute
- Support 100+ concurrent workers
- Sub-second UI updates
- < 100ms API response time
- < 50MB memory footprint for agent

## Future Considerations (Post-MVP)

1. **Authentication & Multi-tenancy**
   - User authentication (OAuth, JWT)
   - Organization/workspace support
   - Role-based access control

2. **Advanced Features**
   - Task scheduling/cron monitoring
   - Alert system (email, Slack, webhooks)
   - Task result storage and search
   - Custom dashboards
   - Task dependency visualization

3. **SaaS Features**
   - Billing integration
   - Usage quotas
   - Data retention policies
   - Multi-region support

4. **Integrations**
   - Prometheus/Grafana export
   - Datadog integration
   - Slack notifications
   - PagerDuty alerts

## Success Metrics

- Agent installation in < 1 minute
- Zero-config for common Celery setups
- 90% feature parity with Flower
- 10x better performance than Flower
- Modern, responsive UI

## Development Tools

### Required
- Go 1.21+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Recommended
- Make (for build automation)
- golangci-lint (Go linting)
- ESLint/Prettier (Frontend linting)
- k6 or Gatling (load testing)
