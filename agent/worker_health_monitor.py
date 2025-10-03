"""Worker health monitoring for detecting offline workers."""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from database import DatabaseManager, TaskEventDB
from event_handler import EventHandler

logger = logging.getLogger(__name__)


class WorkerHealthMonitor:
    """Monitors worker health by checking heartbeat timestamps."""
    
    def __init__(self, monitor_instance, db_manager: DatabaseManager, event_handler: EventHandler):
        self.monitor_instance = monitor_instance
        self.db_manager = db_manager
        self.event_handler = event_handler
        self.running = False
        self.thread = None
        
        # Configuration
        self.check_interval = 15  # Check every 15 seconds
        self.worker_timeout = 30  # Mark worker offline after 30 seconds of no heartbeat
        
    def start(self):
        """Start the health monitor in a background thread."""
        if self.running:
            logger.warning("Worker health monitor already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_monitor, daemon=True)
        self.thread.start()
        logger.info(f"Worker health monitor started (timeout: {self.worker_timeout}s, interval: {self.check_interval}s)")
        
    def stop(self):
        """Stop the health monitor."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Worker health monitor stopped")
        
    def _run_monitor(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._check_worker_health()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in worker health monitor: {e}", exc_info=True)
                time.sleep(self.check_interval)
                
    def _check_worker_health(self):
        """Check all workers for staleness and mark offline workers."""
        current_time = datetime.utcnow()
        timeout_threshold = current_time - timedelta(seconds=self.worker_timeout)
        
        # Get current worker states from monitor
        workers = self.monitor_instance.get_workers_info()
        
        offline_workers = []
        
        for hostname, worker_data in workers.items():
            last_seen = worker_data.get('timestamp')
            current_status = worker_data.get('status', 'unknown')
            
            if last_seen and isinstance(last_seen, datetime):
                # Check if worker hasn't been seen for too long
                if last_seen < timeout_threshold and current_status == 'online':
                    logger.warning(f"Worker {hostname} appears offline (last seen: {last_seen})")
                    
                    # Mark worker as offline in monitor state
                    workers[hostname]['status'] = 'offline'
                    offline_workers.append(hostname)
                    
                    # Mark tasks as orphaned
                    self._mark_worker_tasks_as_orphaned(hostname, current_time)
                    
        if offline_workers:
            logger.info(f"Marked {len(offline_workers)} workers as offline: {offline_workers}")
            
    def _mark_worker_tasks_as_orphaned(self, hostname: str, orphaned_at: datetime):
        """Mark all running tasks on a worker as orphaned."""
        try:
            with self.db_manager.get_session() as session:
                # Find tasks that are currently running on this worker
                running_tasks = session.query(TaskEventDB).filter(
                    TaskEventDB.hostname == hostname,
                    TaskEventDB.event_type == 'task-started',
                    TaskEventDB.is_orphan.is_(False)  # Don't re-orphan already orphaned tasks
                ).all()
                
                orphaned_tasks = []
                
                # Check which tasks haven't been completed yet
                for task in running_tasks:
                    # Check if this task has any completion events
                    completed = session.query(TaskEventDB).filter(
                        TaskEventDB.task_id == task.task_id,
                        TaskEventDB.event_type.in_(['task-succeeded', 'task-failed', 'task-revoked'])
                    ).first()
                    
                    if not completed:
                        # Mark as orphaned
                        session.query(TaskEventDB).filter(
                            TaskEventDB.task_id == task.task_id
                        ).update({
                            'is_orphan': True,
                            'orphaned_at': orphaned_at
                        })
                        orphaned_tasks.append(task)
                
                session.commit()
                
                # Broadcast orphan events via WebSocket
                from models import TaskEvent
                for task in orphaned_tasks:
                    orphan_event = TaskEvent(
                        task_id=task.task_id,
                        task_name=task.task_name,
                        event_type='task-orphaned',
                        hostname=task.hostname,
                        timestamp=orphaned_at,
                        routing_key=task.routing_key,
                        args=task.args,
                        kwargs=task.kwargs
                    )
                    logger.info(f"Broadcasting orphan event for task {task.task_id}")
                    self.event_handler.connection_manager.queue_broadcast(orphan_event)
                
                if orphaned_tasks:
                    logger.info(f"Marked {len(orphaned_tasks)} tasks as orphaned for offline worker {hostname}")
                    
        except Exception as e:
            logger.error(f"Error marking tasks as orphaned for worker {hostname}: {e}", exc_info=True)