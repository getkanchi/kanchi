import threading
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional

from prometheus_client import Counter, Gauge, Histogram

from constants import EventType, COMPLETED_EVENT_TYPES
from models import TaskEvent, WorkerEvent


def _timestamp(dt: Optional[datetime]) -> float:
    """Convert datetime to UTC timestamp."""
    if dt is None:
        return datetime.now(timezone.utc).timestamp()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _safe_task_name(task_name: Optional[str]) -> str:
    return task_name or "unknown"


def _safe_worker(worker: Optional[str]) -> str:
    return worker or "unknown"


class MetricsCollector:
    def __init__(self):
        self.task_events_total = Counter(
            "kanchi_task_events_total",
            "Count of task-related events observed by Kanchi from the Celery broker.",
            ["task_name", "event_type", "worker"],
        )
        self.task_queue_wait_seconds = Gauge(
            "kanchi_task_queue_wait_seconds",
            "Time a task spent queued at a worker before execution began.",
            ["task_name", "worker"],
        )
        self.worker_prefetch_count = Gauge(
            "kanchi_worker_prefetch_count",
            "Number of tasks currently prefetched (reserved) by a worker.",
            ["task_name", "worker"],
        )
        self.task_execution_duration_seconds = Histogram(
            "kanchi_task_execution_duration_seconds",
            "Duration of actual task execution.",
            ["task_name", "worker"],
        )
        self.worker_status = Gauge(
            "kanchi_worker_status",
            "Worker availability flag (1 = online, 0 = offline).",
            ["worker"],
        )
        self.worker_active_tasks = Gauge(
            "kanchi_worker_active_tasks",
            "Count of tasks currently being processed by a given worker.",
            ["worker"],
        )

        self._received_at: Dict[str, float] = {}
        self._started_at: Dict[str, float] = {}
        self._prefetched_counts: Dict[Tuple[str, str], int] = {}
        self._active_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    def record_task_event(self, task_event: TaskEvent):
        """Update metrics based on a task event."""
        task_name = _safe_task_name(task_event.task_name)
        worker = _safe_worker(task_event.hostname or task_event.worker_name)
        ts = _timestamp(task_event.timestamp)

        self.task_events_total.labels(
            task_name=task_name,
            event_type=task_event.event_type,
            worker=worker,
        ).inc()

        if task_event.event_type == EventType.TASK_RECEIVED.value:
            self._track_received(task_event.task_id, ts)
            self._update_prefetch(task_name, worker, delta=1)
            return

        if task_event.event_type == EventType.TASK_STARTED.value:
            self._record_queue_wait(task_event.task_id, task_name, worker, ts)
            self._track_started(task_event.task_id, ts)
            self._update_prefetch(task_name, worker, delta=-1)
            self._update_active(worker, delta=1)
            return

        if task_event.event_type in COMPLETED_EVENT_TYPES or (
            task_event.event_type == EventType.TASK_RETRIED.value
        ):
            self._record_execution_duration(task_event, task_name, worker, ts)
            self._update_active(worker, delta=-1)
            self._update_prefetch(task_name, worker, delta=-1)
            self._clear_tracking(task_event.task_id)

    def record_worker_event(self, worker_event: WorkerEvent):
        """Update metrics based on a worker event."""
        worker = _safe_worker(worker_event.hostname)
        is_offline = worker_event.event_type == EventType.WORKER_OFFLINE.value

        self.worker_status.labels(worker=worker).set(0 if is_offline else 1)

        if worker_event.active is not None:
            self._set_active(worker, max(worker_event.active, 0))

        if is_offline:
            self._set_active(worker, 0)
            self._reset_prefetch_for_worker(worker)

    def _record_queue_wait(
        self, task_id: str, task_name: str, worker: str, started_ts: float
    ):
        with self._lock:
            received_ts = self._received_at.pop(task_id, None)

        if received_ts is None:
            return

        wait_seconds = max(0.0, started_ts - received_ts)
        self.task_queue_wait_seconds.labels(
            task_name=task_name,
            worker=worker,
        ).set(wait_seconds)

    def _record_execution_duration(
        self, task_event: TaskEvent, task_name: str, worker: str, ts: float
    ):
        duration = task_event.runtime
        start_ts = None

        with self._lock:
            start_ts = self._started_at.pop(task_event.task_id, None)

        if duration is None and start_ts is not None:
            duration = ts - start_ts

        if duration is None:
            return

        self.task_execution_duration_seconds.labels(
            task_name=task_name,
            worker=worker,
        ).observe(max(0.0, duration))

    def _track_received(self, task_id: str, ts: float):
        with self._lock:
            self._received_at[task_id] = ts

    def _track_started(self, task_id: str, ts: float):
        with self._lock:
            self._started_at[task_id] = ts

    def _clear_tracking(self, task_id: str):
        with self._lock:
            self._received_at.pop(task_id, None)
            self._started_at.pop(task_id, None)

    def _update_prefetch(self, task_name: str, worker: str, delta: int):
        key = (task_name, worker)
        with self._lock:
            current = self._prefetched_counts.get(key, 0)
            new_value = max(0, current + delta)

            if new_value == 0:
                self._prefetched_counts.pop(key, None)
            else:
                self._prefetched_counts[key] = new_value

        self.worker_prefetch_count.labels(
            task_name=task_name,
            worker=worker,
        ).set(new_value)

    def _reset_prefetch_for_worker(self, worker: str):
        with self._lock:
            keys = [key for key in self._prefetched_counts if key[1] == worker]
            for key in keys:
                self._prefetched_counts.pop(key, None)
                self.worker_prefetch_count.labels(
                    task_name=key[0],
                    worker=worker,
                ).set(0)

    def _update_active(self, worker: str, delta: int):
        with self._lock:
            current = self._active_counts.get(worker, 0)
            new_value = max(0, current + delta)

            if new_value == 0:
                self._active_counts.pop(worker, None)
            else:
                self._active_counts[worker] = new_value

        self.worker_active_tasks.labels(worker=worker).set(new_value)

    def _set_active(self, worker: str, value: int):
        with self._lock:
            if value <= 0:
                self._active_counts.pop(worker, None)
            else:
                self._active_counts[worker] = value

        self.worker_active_tasks.labels(worker=worker).set(max(0, value))


metrics_collector = MetricsCollector()
