# Multi-Broker Support Investigation for Kanchi

**Date**: 2025-12-02
**Status**: Investigation Only - No Implementation Yet

## Executive Summary

**Yes, Kanchi could support monitoring multiple Celery brokers**, but it would require significant architectural changes across multiple layers of the application. The current design assumes a single broker connection, and this assumption is deeply embedded in the configuration, monitoring, database schema, and UI layers.

This document outlines the current architecture, identifies what would need to change, and proposes potential implementation approaches.

---

## Current Architecture Analysis

### 1. Single Broker Design

The current architecture is built around a **single Celery broker connection**:

#### Configuration Layer (`agent/config.py`)
```python
# Line 30: Single broker URL
broker_url: str = os.getenv('CELERY_BROKER_URL')
```

- Only one `CELERY_BROKER_URL` environment variable supported
- No concept of broker identification or naming
- Configuration is passed directly to a single monitor instance

#### Monitor Layer (`agent/monitor.py`)
```python
# Lines 18-30: Single Celery instance
class CeleryEventMonitor:
    def __init__(self, broker_url: str = "amqp://guest@localhost//", ...):
        self.broker_url = broker_url
        self.app = Celery(broker=broker_url, task_send_sent_event=True)
```

- One `CeleryEventMonitor` instance per application
- Single Celery app connection
- Single event receiver loop (blocking call on line 158: `recv.capture()`)

#### Application Layer (`agent/app.py`)
```python
# Lines 282-293: Single monitor instance
app_state.monitor_instance = CeleryEventMonitor(
    broker_url=config.broker_url,
    ...
)
```

- Application state holds one monitor instance
- Monitor runs in a single daemon thread
- No broker context in the application state

### 2. Data Flow

Current event flow:
```
Single Celery Broker
    ↓
CeleryEventMonitor (single instance)
    ↓
EventHandler
    ↓
├── Database (no broker_id field)
├── WebSocket Broadcast (no broker context)
├── Metrics Collector
└── Workflow Engine
```

### 3. Database Schema

#### Task Events Table (`agent/database.py`, lines 47-96)
```python
class TaskEventDB(Base):
    __tablename__ = 'task_events'

    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), nullable=False, index=True)
    task_name = Column(String(255), index=True)
    event_type = Column(String(50), nullable=False)
    # ... other fields
    # ❌ NO broker_id or broker_url field
```

**Key Issue**: No broker identification in database schema
- Task events don't track which broker they came from
- Worker events don't track broker association
- Queries cannot filter by broker

#### Worker Events Table (lines 199-225)
```python
class WorkerEventDB(Base):
    __tablename__ = 'worker_events'

    hostname = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    # ❌ NO broker_id field
```

**Impact**: Workers from different brokers with the same hostname would collide

---

## What Would Need to Change

### 1. Configuration Layer Changes

#### Current
```python
# Single broker URL
broker_url: str = os.getenv('CELERY_BROKER_URL')
```

#### Proposed Option A: Multiple Environment Variables
```python
# Multiple broker URLs with identifiers
broker_configs: List[BrokerConfig] = field(default_factory=list)

@dataclass
class BrokerConfig:
    id: str  # Unique identifier (e.g., "prod-broker", "staging-broker")
    name: str  # Human-readable name
    broker_url: str  # Connection string
    enabled: bool = True
    tags: List[str] = field(default_factory=list)  # For filtering/grouping
```

**Environment Variables**:
```bash
CELERY_BROKER_1_ID=prod-rabbitmq
CELERY_BROKER_1_NAME=Production RabbitMQ
CELERY_BROKER_1_URL=amqp://user:pass@prod-rabbitmq:5672//

CELERY_BROKER_2_ID=staging-redis
CELERY_BROKER_2_NAME=Staging Redis
CELERY_BROKER_2_URL=redis://staging-redis:6379/0
```

#### Proposed Option B: JSON Configuration
```bash
CELERY_BROKERS='[
  {"id": "prod-rabbitmq", "name": "Production", "url": "amqp://..."},
  {"id": "staging-redis", "name": "Staging", "url": "redis://..."}
]'
```

#### Proposed Option C: Configuration File
```yaml
# kanchi-brokers.yaml
brokers:
  - id: prod-rabbitmq
    name: Production RabbitMQ
    url: amqp://user:pass@prod-rabbitmq:5672//
    enabled: true
    tags: [production, rabbitmq]

  - id: staging-redis
    name: Staging Redis
    url: redis://staging-redis:6379/0
    enabled: true
    tags: [staging, redis]
```

**Backward Compatibility**: Support `CELERY_BROKER_URL` as single-broker mode for existing deployments.

---

### 2. Monitor Layer Changes

#### Current Architecture
- Single `CeleryEventMonitor` instance
- Blocking event loop in one thread
- No broker identification

#### Proposed Architecture

**Option A: Multiple Monitor Instances (Recommended)**
```python
class MultiBrokerMonitor:
    def __init__(self, broker_configs: List[BrokerConfig]):
        self.monitors: Dict[str, CeleryEventMonitor] = {}
        self.threads: Dict[str, threading.Thread] = {}

        for config in broker_configs:
            # Create separate monitor per broker
            monitor = CeleryEventMonitor(
                broker_url=config.broker_url,
                broker_id=config.id,  # NEW: Pass broker ID
                broker_name=config.name
            )
            self.monitors[config.id] = monitor

    def start_all(self):
        # Start each monitor in its own thread
        for broker_id, monitor in self.monitors.items():
            thread = threading.Thread(
                target=monitor.start_monitoring,
                name=f"monitor-{broker_id}"
            )
            thread.daemon = True
            thread.start()
            self.threads[broker_id] = thread
```

**Modified CeleryEventMonitor**:
```python
class CeleryEventMonitor:
    def __init__(
        self,
        broker_url: str,
        broker_id: str = "default",  # NEW
        broker_name: str = None,     # NEW
        ...
    ):
        self.broker_url = broker_url
        self.broker_id = broker_id        # NEW
        self.broker_name = broker_name    # NEW
        self.app = Celery(broker=broker_url, ...)

    def _handle_task_event(self, event: Dict[str, Any]):
        # Attach broker context to event
        task_event = TaskEvent.from_celery_event(event, task_name)
        task_event.broker_id = self.broker_id      # NEW
        task_event.broker_name = self.broker_name  # NEW

        if self.task_callback:
            self.task_callback(task_event)
```

**Thread Safety Considerations**:
- Each monitor runs in separate thread with own Celery connection
- Database writes need proper session management (already handled via context managers)
- WebSocket broadcasting is already thread-safe (uses asyncio queue)

---

### 3. Data Model Changes

#### TaskEvent Model (`agent/models.py`)
```python
class TaskEvent(BaseModel):
    task_id: str
    task_name: str
    event_type: str
    timestamp: datetime

    # NEW: Broker identification
    broker_id: str
    broker_name: Optional[str] = None

    # Existing fields...
    hostname: Optional[str] = None
    queue: Optional[str] = None
    # ...
```

#### WorkerEvent Model
```python
class WorkerEvent(BaseModel):
    hostname: str
    event_type: str
    timestamp: datetime

    # NEW: Broker identification
    broker_id: str
    broker_name: Optional[str] = None

    # Existing fields...
```

---

### 4. Database Schema Changes

#### Migration Required: Add broker_id to task_events

```sql
-- Add broker_id column to task_events
ALTER TABLE task_events
ADD COLUMN broker_id VARCHAR(255) NOT NULL DEFAULT 'default';

-- Add index for broker-filtered queries
CREATE INDEX idx_broker_timestamp
ON task_events(broker_id, timestamp);

-- Add composite index for common queries
CREATE INDEX idx_broker_event_type_timestamp
ON task_events(broker_id, event_type, timestamp);

-- Add index for broker + task name queries
CREATE INDEX idx_broker_task_name
ON task_events(broker_id, task_name, timestamp);
```

#### Migration Required: Add broker_id to task_latest

```sql
-- Modify primary key to include broker_id
-- This is complex - might need to recreate table
ALTER TABLE task_latest
ADD COLUMN broker_id VARCHAR(255);

-- New primary key: (task_id, broker_id)
-- This allows same task_id across different brokers
```

**Critical Design Decision**: Should `task_id` be unique globally or per-broker?

**Option A**: Globally Unique (Current Behavior)
- Assumes task_id is UUID and globally unique
- Same task_id cannot appear on multiple brokers
- Simpler for tracking task lineage

**Option B**: Per-Broker Unique (More Flexible)
- Allows same task_id on different brokers (rare but possible)
- Primary key becomes `(broker_id, task_id)`
- More complex queries and API responses

**Recommendation**: Option A (Globally Unique) - Celery UUIDs are globally unique, so this is safe.

#### Migration Required: Add broker_id to worker_events

```sql
ALTER TABLE worker_events
ADD COLUMN broker_id VARCHAR(255) NOT NULL DEFAULT 'default';

CREATE INDEX idx_worker_broker
ON worker_events(broker_id, hostname, timestamp);
```

#### Migration Required: Add brokers table

```sql
CREATE TABLE brokers (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    broker_url_masked VARCHAR(500),  -- Masked for security
    enabled BOOLEAN DEFAULT TRUE,
    tags JSON,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),  -- 'connected', 'disconnected', 'error'
    error_message TEXT
);

CREATE INDEX idx_broker_status ON brokers(status, last_seen);
```

---

### 5. API Changes

#### New Endpoints Required

**GET /api/brokers**
- List all configured brokers
- Return status, last seen, event counts

**GET /api/brokers/{broker_id}/tasks**
- Filter tasks by broker

**GET /api/brokers/{broker_id}/workers**
- Filter workers by broker

**GET /api/brokers/{broker_id}/health**
- Broker-specific health check

#### Modified Existing Endpoints

**GET /api/tasks**
- Add `broker_id` query parameter
- Add `broker_id` to response objects
- Support multi-broker filtering: `?broker_id=prod,staging`

**GET /api/tasks/recent**
- Include broker information in response
- Support broker filtering

**GET /api/workers**
- Add `broker_id` to worker objects
- Filter by broker

**WebSocket /ws**
- Add broker filtering to subscription:
  ```json
  {
    "type": "subscribe",
    "filters": {
      "broker_id": ["prod-rabbitmq", "staging-redis"],
      "event_type": ["task-failed", "task-succeeded"]
    }
  }
  ```

---

### 6. Frontend / UI Changes

#### Dashboard Changes
- **Broker Selector**: Dropdown or tabs to filter by broker
- **Multi-Broker View**: Option to show all brokers or specific ones
- **Broker Status Indicators**: Visual indicators for broker health
- **Broker Tags**: Color-coding or badges per broker

#### Task List Changes
- **Broker Column**: Add broker name/ID to task table
- **Broker Filter**: Filter tasks by broker in sidebar
- **Broker Badge**: Visual badge showing which broker task came from

#### Worker View Changes
- **Group by Broker**: Organize workers by broker
- **Broker Association**: Show which broker each worker is connected to
- **Cross-Broker Workers**: Handle workers connected to multiple brokers (if applicable)

#### New Broker Management Page
- List all brokers with status
- Connection statistics per broker
- Enable/disable broker monitoring
- View broker-specific metrics

---

### 7. Metrics and Monitoring Changes

#### Prometheus Metrics (`agent/metrics.py`)

Add broker labels to all metrics:

```python
# Current
task_events_total = Counter('celery_task_events_total',
    'Total task events',
    ['event_type', 'task_name'])

# Updated
task_events_total = Counter('celery_task_events_total',
    'Total task events',
    ['broker_id', 'event_type', 'task_name'])  # Added broker_id

# Example metrics
kanchi_broker_connection_status{broker_id="prod-rabbitmq"} 1
kanchi_broker_tasks_total{broker_id="prod-rabbitmq",status="succeeded"} 12345
kanchi_broker_workers_count{broker_id="prod-rabbitmq"} 5
```

#### Health Monitoring

**Per-Broker Health Checks**:
- Connection status per broker
- Last event received timestamp per broker
- Active workers per broker
- Error rates per broker

---

### 8. Worker Health Monitor Changes

#### Current Behavior (`agent/worker_health_monitor.py`)
- Monitors all workers globally
- Detects offline workers by heartbeat timeout
- Marks tasks as orphaned when workers go offline

#### Required Changes
```python
class WorkerHealthMonitor:
    def _run_monitor(self):
        while self.running:
            now = datetime.now(timezone.utc)

            # Get workers grouped by broker
            for broker_id, workers in self.get_workers_by_broker():
                for hostname, worker_info in workers.items():
                    last_heartbeat = worker_info.get('timestamp')

                    if (now - last_heartbeat).total_seconds() > 30:
                        # Mark tasks as orphaned for this worker on this broker
                        self.mark_tasks_orphaned(
                            hostname=hostname,
                            broker_id=broker_id  # NEW
                        )
```

**Key Change**: Orphan detection must be broker-aware to avoid false positives across brokers.

---

### 9. Workflow Engine Changes

#### Current Behavior (`agent/services/workflow_engine.py`)
- Processes events without broker context
- Triggers workflows based on task/worker events

#### Required Changes
- Add `broker_id` to workflow trigger conditions
- Support broker-specific workflow rules:
  ```json
  {
    "name": "Alert on Production Failures",
    "trigger": {"type": "task_event"},
    "conditions": {
      "operator": "AND",
      "conditions": [
        {"field": "broker_id", "operator": "equals", "value": "prod-rabbitmq"},
        {"field": "event_type", "operator": "equals", "value": "task-failed"}
      ]
    },
    "actions": [{"type": "slack_notification", "params": {...}}]
  }
  ```

---

## Implementation Approach

### Phase 1: Foundation (No Breaking Changes)
1. **Add broker_id to models with default value**
   - Update `TaskEvent`, `WorkerEvent` with optional `broker_id`
   - Default to `"default"` for backward compatibility

2. **Database migration**
   - Add `broker_id` columns with default value `'default'`
   - Add new indexes for broker-filtered queries
   - Create `brokers` table

3. **Update monitor to accept optional broker_id**
   - Modify `CeleryEventMonitor.__init__` to accept `broker_id` and `broker_name`
   - Attach broker context to all events

4. **Backward compatibility layer**
   - Support single `CELERY_BROKER_URL` (maps to broker_id="default")
   - All existing queries work with default broker

### Phase 2: Multi-Broker Support
1. **Configuration parser**
   - Support multiple broker configurations
   - Parse from environment variables or config file

2. **Multi-broker monitor manager**
   - Create `MultiBrokerMonitor` class
   - Manage multiple monitor instances and threads
   - Handle broker lifecycle (start/stop/restart)

3. **Update application startup**
   - Detect single vs multi-broker configuration
   - Initialize appropriate monitor type

### Phase 3: API and UI
1. **API endpoints**
   - Add broker filtering to all task/worker endpoints
   - Create broker management endpoints
   - Update WebSocket subscription to support broker filters

2. **Frontend updates**
   - Add broker selector to dashboard
   - Display broker information in task lists
   - Create broker management page

### Phase 4: Advanced Features
1. **Cross-broker analytics**
   - Compare metrics across brokers
   - Aggregate statistics by broker
   - Broker health dashboard

2. **Broker-specific workflows**
   - Add broker filtering to workflow engine
   - Support broker-specific alerting

---

## Design Considerations and Challenges

### 1. Task ID Uniqueness
**Question**: Can the same task_id appear on multiple brokers?

**Analysis**:
- Celery generates task IDs using UUID4 (globally unique)
- Collision probability is astronomically low
- However, if brokers are in different environments with different Celery versions or custom task ID generators, collisions are theoretically possible

**Recommendation**:
- Treat task_id as globally unique (current behavior)
- Add broker_id to schema for context, but not to primary key
- If collision detected, log warning and append broker suffix

### 2. Worker Hostname Collisions
**Question**: What if workers on different brokers have the same hostname?

**Scenarios**:
- Different environments (dev/staging/prod) with auto-generated hostnames
- Containerized workers with generic names like `worker-1`, `worker-2`

**Recommendation**:
- Worker identity should be `(broker_id, hostname)` tuple
- Update worker health monitor to track per-broker
- UI should display broker context for workers

### 3. Performance Impact
**Concerns**:
- Multiple threads monitoring multiple brokers
- Increased database writes (broker_id in every insert)
- More complex queries with broker filtering

**Mitigations**:
- Each monitor thread is lightweight (mostly I/O waiting)
- Database indexes on broker_id minimize query overhead
- Connection pooling handles concurrent writes
- Consider sharding for very high-volume scenarios

### 4. Connection Management
**Challenges**:
- Each Celery connection holds resources (sockets, memory)
- Need graceful handling of broker disconnections
- Reconnection logic per broker

**Recommendations**:
- Implement per-broker connection health monitoring
- Auto-reconnect on connection loss
- Circuit breaker pattern for failing brokers
- Admin UI to disable problematic brokers

### 5. Backward Compatibility
**Requirements**:
- Existing single-broker deployments must continue working
- Database migration must not break existing data
- API responses remain compatible

**Strategy**:
- Default broker_id to `"default"` for single-broker mode
- Support `CELERY_BROKER_URL` as legacy configuration
- API returns broker_id as optional field (null = default)
- Frontend gracefully handles missing broker information

### 6. Testing Complexity
**New Test Scenarios**:
- Multiple brokers with overlapping task names
- Broker connection failures and recovery
- Cross-broker worker hostname collisions
- Multi-broker WebSocket filtering

**Testing Strategy**:
- Integration tests with multiple test brokers (RabbitMQ + Redis)
- Mock broker disconnections
- Load testing with concurrent broker monitoring

---

## Alternative Approaches

### Alternative 1: Separate Kanchi Instances per Broker
**Description**: Deploy multiple Kanchi instances, one per broker, with separate databases.

**Pros**:
- No code changes required
- Simpler architecture
- Natural isolation

**Cons**:
- No unified view across brokers
- Duplicate infrastructure
- No cross-broker analytics
- More operational overhead

**Use Case**: Works for completely isolated environments (prod vs staging in different networks).

---

### Alternative 2: Broker Proxy/Aggregator
**Description**: Create a proxy service that aggregates events from multiple brokers and presents them to a single Kanchi instance.

**Pros**:
- Minimal changes to Kanchi core
- Broker logic isolated in proxy
- Could support dynamic broker addition

**Cons**:
- Additional component to maintain
- Proxy becomes single point of failure
- Added latency
- Complex proxy logic

**Use Case**: When brokers are in restricted networks or require special connection handling.

---

### Alternative 3: Federated Kanchi Instances
**Description**: Multiple Kanchi instances that can query each other via API federation.

**Pros**:
- Each broker has dedicated Kanchi
- Gradual migration path
- Fault isolation

**Cons**:
- Complex federation protocol
- Network overhead for cross-broker queries
- Eventual consistency challenges

**Use Case**: Large-scale deployments with geographically distributed brokers.

---

## Recommended Approach

**Approach**: **Option A - Native Multi-Broker Support** (Main proposal in this document)

**Rationale**:
1. **Unified monitoring**: Single pane of glass for all Celery infrastructure
2. **Better analytics**: Cross-broker comparisons and aggregations
3. **User experience**: Simpler for users than managing multiple Kanchi instances
4. **Operational efficiency**: One deployment, one database, one UI
5. **Backward compatible**: Single-broker mode still works

**When NOT to use this approach**:
- Brokers are in completely isolated networks with no connectivity
- Different security domains require physical separation
- Extreme scale (1000s of brokers) - consider federation instead

---

## Effort Estimation

### Development Effort

| Component | Effort | Complexity |
|-----------|--------|------------|
| Configuration parsing | 1-2 days | Low |
| Monitor refactoring | 3-4 days | Medium |
| Database migration | 2-3 days | Medium-High |
| Data model updates | 1-2 days | Low |
| API endpoint changes | 3-5 days | Medium |
| Frontend UI updates | 5-7 days | Medium-High |
| Metrics/monitoring | 2-3 days | Medium |
| Testing | 5-7 days | High |
| Documentation | 2-3 days | Low |

**Total Estimated Effort**: 24-36 days (1-1.5 months for one developer)

### Risk Factors
- Database migration on large datasets (could be slow)
- Backward compatibility edge cases
- Performance testing at scale
- Frontend state management complexity

---

## Migration Path for Existing Users

### Step 1: Upgrade to Multi-Broker Capable Version
1. Run database migrations (adds broker_id columns)
2. Existing data gets `broker_id='default'`
3. Application continues working in single-broker mode

### Step 2: Add Additional Brokers (Optional)
1. Update configuration with new broker URLs
2. Restart application
3. New brokers appear in UI
4. Historical data remains in 'default' broker

### Step 3: Relabel Default Broker (Optional)
1. Use admin API/UI to rename 'default' broker
2. Update broker metadata (name, tags)

**Zero Downtime**: Migration can happen without application downtime (depending on database size).

---

## Conclusion

**Kanchi CAN support multiple brokers**, but it requires thoughtful implementation across the entire stack. The recommended approach is to build native multi-broker support with:

1. ✅ **Backward compatibility** - Single-broker deployments continue working
2. ✅ **Flexible configuration** - Support environment variables or config files
3. ✅ **Broker-aware data model** - Add broker context to events and database
4. ✅ **Unified UI** - Single dashboard showing all brokers with filtering
5. ✅ **Robust monitoring** - Per-broker health checks and metrics

The implementation is **non-trivial but achievable** with an estimated 4-6 weeks of development effort. The architecture proposed maintains Kanchi's simplicity while adding powerful multi-broker capabilities.

---

## Next Steps (If Approved for Implementation)

1. **Design review** - Validate approach with team/community
2. **Prototype** - Build proof-of-concept for core multi-monitor architecture
3. **Database migration strategy** - Plan migration for large datasets
4. **API design** - Finalize API contract changes
5. **Frontend mockups** - Design UI for broker selection and filtering
6. **Implementation phases** - Build incrementally following the phase plan
7. **Testing strategy** - Define comprehensive test scenarios
8. **Documentation** - Update user guides and deployment docs

---

## Questions for Stakeholders

1. **Use case validation**: What's the primary use case for multi-broker support?
   - Monitoring prod + staging from one dashboard?
   - Multi-region brokers?
   - Different teams with separate brokers?

2. **Scale requirements**: How many brokers need to be supported?
   - 2-5 brokers: Current proposal works well
   - 10-50 brokers: May need optimization
   - 100+ brokers: Consider federation approach

3. **Priority features**: Which features are must-have vs nice-to-have?
   - Cross-broker task queries?
   - Broker-specific alerts?
   - Broker comparison analytics?

4. **Migration constraints**: Are there specific requirements for existing deployments?
   - Zero downtime required?
   - Database size concerns?
   - API stability requirements?

---

**End of Investigation Report**
