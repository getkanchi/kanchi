#!/usr/bin/env python3
"""
Database seeder for Kanchi - Generates marketing/demo data.

This script populates the database with realistic Celery task monitoring data
to showcase the application's capabilities in screenshots, demos, and marketing materials.
"""

import os
import sys
import uuid
import random
from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any

from database import (
    DatabaseManager,
    TaskEventDB,
    WorkerEventDB,
    TaskRegistryDB,
    TaskDailyStatsDB,
    EnvironmentDB,
    WorkflowDB,
    ActionConfigDB,
    RetryRelationshipDB,
)
from config import Config


class DatabaseSeeder:
    """Seeds database with marketing/demo data."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.task_names = [
            "process_payment",
            "send_notification_email",
            "generate_invoice",
            "sync_customer_data",
            "process_refund",
            "export_analytics_report",
            "backup_database",
            "cleanup_old_logs",
            "validate_inventory",
            "send_sms_notification",
            "process_webhook",
            "generate_thumbnail",
            "transcribe_audio",
            "optimize_images",
            "calculate_shipping",
        ]

        self.worker_hostnames = [
            "worker-prod-01.company.com",
            "worker-prod-02.company.com",
            "worker-staging-01.company.com",
            "worker-dev-01.local",
        ]

        self.queues = [
            "default",
            "high-priority",
            "low-priority",
            "payments",
            "notifications",
            "reports",
            "background",
        ]

    def _generate_task_arguments(self, task_name: str) -> tuple[list, dict]:
        """Generate realistic args and kwargs based on task name."""
        args_kwargs_map = {
            "process_payment": (
                [],
                {
                    "payment_id": f"pay_{random.randint(10000, 99999)}",
                    "amount": round(random.uniform(10.0, 500.0), 2),
                    "currency": random.choice(["USD", "EUR", "GBP"]),
                    "customer_id": f"cust_{random.randint(1000, 9999)}",
                },
            ),
            "send_notification_email": (
                [f"user{random.randint(100, 999)}@example.com"],
                {
                    "subject": random.choice([
                        "Your order has been shipped",
                        "Password reset request",
                        "Welcome to our service",
                        "Invoice #INV-{random.randint(1000, 9999)}",
                    ]),
                    "template": random.choice(["welcome", "invoice", "shipping", "reset_password"]),
                },
            ),
            "generate_invoice": (
                [],
                {
                    "order_id": f"ORD-{random.randint(10000, 99999)}",
                    "customer_id": f"cust_{random.randint(1000, 9999)}",
                    "format": random.choice(["pdf", "html"]),
                },
            ),
            "sync_customer_data": (
                [f"cust_{random.randint(1000, 9999)}"],
                {
                    "sync_type": random.choice(["full", "incremental"]),
                    "crm_system": random.choice(["salesforce", "hubspot"]),
                },
            ),
            "process_refund": (
                [],
                {
                    "payment_id": f"pay_{random.randint(10000, 99999)}",
                    "refund_amount": round(random.uniform(5.0, 200.0), 2),
                    "reason": random.choice(["customer_request", "duplicate_charge", "product_defect"]),
                },
            ),
            "export_analytics_report": (
                [],
                {
                    "report_type": random.choice(["sales", "traffic", "conversions", "revenue"]),
                    "date_from": "2025-01-01",
                    "date_to": "2025-01-31",
                    "format": random.choice(["csv", "xlsx", "json"]),
                },
            ),
            "backup_database": (
                [],
                {
                    "database": random.choice(["production", "staging"]),
                    "backup_type": random.choice(["full", "incremental"]),
                    "compression": True,
                },
            ),
            "cleanup_old_logs": (
                [],
                {
                    "days_to_keep": random.choice([30, 60, 90]),
                    "log_type": random.choice(["application", "access", "error"]),
                },
            ),
            "validate_inventory": (
                [],
                {
                    "warehouse_id": f"WH-{random.randint(1, 5)}",
                    "sku_count": random.randint(100, 1000),
                },
            ),
            "send_sms_notification": (
                [f"+1555{random.randint(1000000, 9999999)}"],
                {
                    "message": random.choice([
                        "Your delivery is on its way",
                        "Verification code: 123456",
                        "Order confirmed",
                    ]),
                    "provider": "twilio",
                },
            ),
            "process_webhook": (
                [],
                {
                    "webhook_id": str(uuid.uuid4()),
                    "source": random.choice(["stripe", "github", "shopify"]),
                    "event_type": random.choice(["payment.succeeded", "push", "order.created"]),
                },
            ),
            "generate_thumbnail": (
                [f"images/{uuid.uuid4()}.jpg"],
                {
                    "width": random.choice([150, 300, 500]),
                    "height": random.choice([150, 300, 500]),
                    "quality": random.randint(70, 95),
                },
            ),
            "transcribe_audio": (
                [f"audio/{uuid.uuid4()}.mp3"],
                {
                    "language": random.choice(["en-US", "es-ES", "fr-FR"]),
                    "duration_seconds": random.randint(30, 300),
                },
            ),
            "optimize_images": (
                [],
                {
                    "image_ids": [str(uuid.uuid4()) for _ in range(random.randint(1, 5))],
                    "quality": random.randint(75, 90),
                    "format": random.choice(["webp", "jpg", "png"]),
                },
            ),
            "calculate_shipping": (
                [],
                {
                    "origin_zip": f"{random.randint(10000, 99999)}",
                    "destination_zip": f"{random.randint(10000, 99999)}",
                    "weight_kg": round(random.uniform(0.5, 50.0), 2),
                    "carrier": random.choice(["usps", "fedex", "ups"]),
                },
            ),
        }

        # Return task-specific args/kwargs or generic ones
        return args_kwargs_map.get(task_name, ([], {"task_param": "default_value"}))

    def seed_all(self, days_back: int = 7, clear_existing: bool = True):
        """Seed all tables with demo data."""
        print("🌱 Starting database seeding...")

        if clear_existing:
            self.clear_all_data()

        self.seed_environments()
        self.seed_task_registry()
        self.seed_action_configs()
        self.seed_workflows()
        self.seed_task_events(days_back=days_back)
        self.seed_worker_events(days_back=days_back)
        self.seed_daily_stats(days_back=days_back)

        print("✅ Database seeding completed successfully!")

    def clear_all_data(self):
        """Clear all existing data from tables."""
        print("🗑️  Clearing existing data...")
        with self.db_manager.get_session() as session:
            session.query(TaskEventDB).delete()
            session.query(WorkerEventDB).delete()
            session.query(TaskRegistryDB).delete()
            session.query(TaskDailyStatsDB).delete()
            session.query(EnvironmentDB).delete()
            session.query(WorkflowDB).delete()
            session.query(ActionConfigDB).delete()
            session.query(RetryRelationshipDB).delete()
            session.commit()

    def seed_environments(self):
        """Seed environment configurations."""
        print("🌍 Seeding environments...")

        environments = [
            {
                "id": str(uuid.uuid4()),
                "name": "Production",
                "description": "Production environment with high-priority queues and production workers",
                "queue_patterns": ["default", "high-priority", "payments"],
                "worker_patterns": ["worker-prod-*"],
                "is_active": True,
                "is_default": False,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Staging",
                "description": "Staging environment for pre-production testing",
                "queue_patterns": ["default", "low-priority"],
                "worker_patterns": ["worker-staging-*"],
                "is_active": False,
                "is_default": False,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Development",
                "description": "Local development environment",
                "queue_patterns": ["default", "background"],
                "worker_patterns": ["worker-dev-*"],
                "is_active": False,
                "is_default": True,
            },
        ]

        with self.db_manager.get_session() as session:
            for env_data in environments:
                env = EnvironmentDB(**env_data)
                session.add(env)
            session.commit()

        print(f"   ✓ Created {len(environments)} environments")

    def seed_task_registry(self):
        """Seed task registry with descriptions and metadata."""
        print("📋 Seeding task registry...")

        task_metadata = [
            {
                "name": "process_payment",
                "human_readable_name": "Process Payment",
                "description": "Processes customer payments through payment gateway",
                "tags": ["payments", "critical", "finance"],
            },
            {
                "name": "send_notification_email",
                "human_readable_name": "Send Notification Email",
                "description": "Sends transactional email notifications to customers",
                "tags": ["notifications", "email", "communication"],
            },
            {
                "name": "generate_invoice",
                "human_readable_name": "Generate Invoice",
                "description": "Creates PDF invoices for completed orders",
                "tags": ["finance", "reports", "documents"],
            },
            {
                "name": "sync_customer_data",
                "human_readable_name": "Sync Customer Data",
                "description": "Synchronizes customer data with CRM system",
                "tags": ["integration", "crm", "background"],
            },
            {
                "name": "process_refund",
                "human_readable_name": "Process Refund",
                "description": "Handles customer refund requests",
                "tags": ["payments", "finance", "critical"],
            },
            {
                "name": "export_analytics_report",
                "human_readable_name": "Export Analytics Report",
                "description": "Generates and exports analytics reports in CSV/Excel format",
                "tags": ["reports", "analytics", "data"],
            },
            {
                "name": "backup_database",
                "human_readable_name": "Backup Database",
                "description": "Creates automated database backups",
                "tags": ["maintenance", "critical", "infrastructure"],
            },
            {
                "name": "cleanup_old_logs",
                "human_readable_name": "Cleanup Old Logs",
                "description": "Removes log files older than 90 days",
                "tags": ["maintenance", "cleanup", "infrastructure"],
            },
            {
                "name": "validate_inventory",
                "human_readable_name": "Validate Inventory",
                "description": "Validates inventory counts against warehouse data",
                "tags": ["inventory", "validation", "data"],
            },
            {
                "name": "send_sms_notification",
                "human_readable_name": "Send SMS Notification",
                "description": "Sends SMS notifications via Twilio",
                "tags": ["notifications", "sms", "communication"],
            },
            {
                "name": "process_webhook",
                "human_readable_name": "Process Webhook",
                "description": "Processes incoming webhook events from third-party services",
                "tags": ["integration", "webhooks", "api"],
            },
            {
                "name": "generate_thumbnail",
                "human_readable_name": "Generate Thumbnail",
                "description": "Creates image thumbnails for uploaded media",
                "tags": ["media", "images", "processing"],
            },
            {
                "name": "transcribe_audio",
                "human_readable_name": "Transcribe Audio",
                "description": "Transcribes audio files to text using ML service",
                "tags": ["media", "ml", "processing"],
            },
            {
                "name": "optimize_images",
                "human_readable_name": "Optimize Images",
                "description": "Optimizes images for web delivery",
                "tags": ["media", "images", "processing"],
            },
            {
                "name": "calculate_shipping",
                "human_readable_name": "Calculate Shipping",
                "description": "Calculates shipping costs based on location and weight",
                "tags": ["logistics", "calculations", "shipping"],
            },
        ]

        now = datetime.now(timezone.utc)

        with self.db_manager.get_session() as session:
            for task_meta in task_metadata:
                task = TaskRegistryDB(
                    id=str(uuid.uuid4()),
                    name=task_meta["name"],
                    human_readable_name=task_meta["human_readable_name"],
                    description=task_meta["description"],
                    tags=task_meta["tags"],
                    created_at=now,
                    updated_at=now,
                    first_seen=now - timedelta(days=30),
                    last_seen=now,
                )
                session.add(task)
            session.commit()

        print(f"   ✓ Created {len(task_metadata)} task registry entries")

    def seed_action_configs(self):
        """Seed action configuration templates."""
        print("⚙️  Seeding action configurations...")

        action_configs = [
            {
                "id": str(uuid.uuid4()),
                "name": "Slack Alerts Channel",
                "description": "Send alerts to #alerts channel",
                "action_type": "slack",
                "config": {
                    "webhook_url": "https://hooks.slack.com/services/EXAMPLE/WEBHOOK",
                    "channel": "#alerts",
                    "username": "Kanchi Monitor",
                },
                "usage_count": 5,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "PagerDuty Critical",
                "description": "Trigger critical incidents in PagerDuty",
                "action_type": "pagerduty",
                "config": {
                    "integration_key": "EXAMPLE_INTEGRATION_KEY",
                    "severity": "critical",
                },
                "usage_count": 2,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Email DevOps Team",
                "description": "Send email to DevOps team",
                "action_type": "email",
                "config": {
                    "recipients": ["devops@company.com"],
                    "subject_template": "Task Alert: {task_name}",
                },
                "usage_count": 8,
            },
        ]

        now = datetime.now(timezone.utc)

        with self.db_manager.get_session() as session:
            for config_data in action_configs:
                config = ActionConfigDB(
                    **config_data,
                    created_at=now,
                    updated_at=now,
                    created_by="admin",
                    last_used_at=now - timedelta(hours=random.randint(1, 72)),
                )
                session.add(config)
            session.commit()

        print(f"   ✓ Created {len(action_configs)} action configurations")

    def seed_workflows(self):
        """Seed workflow examples."""
        print("🔄 Seeding workflows...")

        workflows = [
            {
                "id": str(uuid.uuid4()),
                "name": "Alert on Payment Failures",
                "description": "Send Slack alert when payment processing fails",
                "enabled": True,
                "trigger_type": "task_failed",
                "trigger_config": {},
                "conditions": {
                    "operator": "AND",
                    "conditions": [
                        {"field": "task_name", "operator": "equals", "value": "process_payment"},
                        {"field": "retries", "operator": "gte", "value": 3},
                    ],
                },
                "actions": [
                    {
                        "type": "slack",
                        "params": {
                            "message": "⚠️ Payment processing failed after 3 retries for task {task_id}",
                        },
                        "continue_on_failure": True,
                    },
                ],
                "priority": 100,
                "execution_count": 12,
                "success_count": 11,
                "failure_count": 1,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Auto-retry Failed Reports",
                "description": "Automatically retry failed analytics report generation",
                "enabled": True,
                "trigger_type": "task_failed",
                "trigger_config": {},
                "conditions": {
                    "operator": "AND",
                    "conditions": [
                        {"field": "task_name", "operator": "equals", "value": "export_analytics_report"},
                        {"field": "retries", "operator": "lt", "value": 3},
                    ],
                },
                "actions": [
                    {
                        "type": "retry",
                        "params": {"countdown": 300},
                        "continue_on_failure": False,
                    },
                ],
                "priority": 90,
                "cooldown_seconds": 60,
                "execution_count": 8,
                "success_count": 8,
                "failure_count": 0,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Database Backup Monitoring",
                "description": "Monitor database backup completion and alert if it takes too long",
                "enabled": True,
                "trigger_type": "task_succeeded",
                "trigger_config": {},
                "conditions": {
                    "operator": "AND",
                    "conditions": [
                        {"field": "task_name", "operator": "equals", "value": "backup_database"},
                        {"field": "runtime", "operator": "gt", "value": 300},
                    ],
                },
                "actions": [
                    {
                        "type": "email",
                        "params": {
                            "subject": "Database backup took longer than expected",
                            "body": "Backup completed in {runtime}s",
                        },
                        "continue_on_failure": True,
                    },
                ],
                "priority": 80,
                "execution_count": 3,
                "success_count": 3,
                "failure_count": 0,
            },
        ]

        now = datetime.now(timezone.utc)

        with self.db_manager.get_session() as session:
            for workflow_data in workflows:
                workflow = WorkflowDB(
                    **workflow_data,
                    created_at=now - timedelta(days=random.randint(5, 30)),
                    updated_at=now - timedelta(days=random.randint(0, 5)),
                    created_by="admin",
                    last_executed_at=now - timedelta(hours=random.randint(1, 24)),
                )
                session.add(workflow)
            session.commit()

        print(f"   ✓ Created {len(workflows)} workflows")

    def seed_task_events(self, days_back: int = 7):
        """Seed task events with various states and scenarios."""
        print(f"📊 Seeding task events for last {days_back} days...")

        events = []
        now = datetime.now(timezone.utc)

        # Generate events for each day
        for day_offset in range(days_back):
            day_start = now - timedelta(days=day_offset)

            # Generate 50-200 events per day
            events_per_day = random.randint(50, 200)

            for _ in range(events_per_day):
                task_name = random.choice(self.task_names)
                task_id = str(uuid.uuid4())
                worker = random.choice(self.worker_hostnames)
                queue = random.choice(self.queues)

                # Random timestamp within the day
                event_time = day_start - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )

                # Determine outcome (90% success, 5% fail, 3% orphan, 2% retry)
                outcome = random.choices(
                    ['success', 'failed', 'orphan', 'retry'],
                    weights=[90, 5, 3, 2]
                )[0]

                if outcome == 'success':
                    events.extend(self._create_successful_task(
                        task_id, task_name, worker, queue, event_time
                    ))
                elif outcome == 'failed':
                    events.extend(self._create_failed_task(
                        task_id, task_name, worker, queue, event_time
                    ))
                elif outcome == 'orphan':
                    events.extend(self._create_orphaned_task(
                        task_id, task_name, worker, queue, event_time
                    ))
                else:  # retry
                    events.extend(self._create_retried_task(
                        task_id, task_name, worker, queue, event_time
                    ))

        # Bulk insert events
        with self.db_manager.get_session() as session:
            for event in events:
                session.add(event)
            session.commit()

        print(f"   ✓ Created {len(events)} task events")

    def _create_successful_task(
        self, task_id: str, task_name: str, worker: str, queue: str, timestamp: datetime
    ) -> List[TaskEventDB]:
        """Create events for a successful task execution."""
        runtime = random.uniform(0.1, 5.0)
        args, kwargs = self._generate_task_arguments(task_name)

        return [
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-received",
                timestamp=timestamp,
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-started",
                timestamp=timestamp + timedelta(milliseconds=50),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-succeeded",
                timestamp=timestamp + timedelta(seconds=runtime),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                runtime=runtime,
                result={"status": "completed", "items_processed": random.randint(1, 100)},
                args=args,
                kwargs=kwargs,
            ),
        ]

    def _create_failed_task(
        self, task_id: str, task_name: str, worker: str, queue: str, timestamp: datetime
    ) -> List[TaskEventDB]:
        """Create events for a failed task execution."""
        runtime = random.uniform(0.1, 2.0)
        args, kwargs = self._generate_task_arguments(task_name)

        errors = [
            "Connection timeout to external service",
            "Invalid data format in request",
            "Rate limit exceeded",
            "Database connection lost",
            "Memory allocation error",
        ]

        return [
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-received",
                timestamp=timestamp,
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-started",
                timestamp=timestamp + timedelta(milliseconds=50),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-failed",
                timestamp=timestamp + timedelta(seconds=runtime),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                runtime=runtime,
                exception=random.choice(errors),
                traceback=f"Traceback (most recent call last):\n  File task.py, line 42\n    raise Exception('{random.choice(errors)}')",
                args=args,
                kwargs=kwargs,
            ),
        ]

    def _create_orphaned_task(
        self, task_id: str, task_name: str, worker: str, queue: str, timestamp: datetime
    ) -> List[TaskEventDB]:
        """Create events for an orphaned task (started but never completed)."""
        args, kwargs = self._generate_task_arguments(task_name)

        return [
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-received",
                timestamp=timestamp,
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=task_id,
                task_name=task_name,
                event_type="task-started",
                timestamp=timestamp + timedelta(milliseconds=50),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=task_id,
                is_orphan=True,
                orphaned_at=timestamp + timedelta(hours=1),
                args=args,
                kwargs=kwargs,
            ),
        ]

    def _create_retried_task(
        self, task_id: str, task_name: str, worker: str, queue: str, timestamp: datetime
    ) -> List[TaskEventDB]:
        """Create events for a task that was retried and eventually succeeded."""
        original_id = task_id
        retry_id = str(uuid.uuid4())
        args, kwargs = self._generate_task_arguments(task_name)

        # First attempt (failed)
        first_attempt = [
            TaskEventDB(
                task_id=original_id,
                task_name=task_name,
                event_type="task-received",
                timestamp=timestamp,
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=original_id,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=original_id,
                task_name=task_name,
                event_type="task-started",
                timestamp=timestamp + timedelta(milliseconds=50),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=original_id,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=original_id,
                task_name=task_name,
                event_type="task-failed",
                timestamp=timestamp + timedelta(seconds=1),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=original_id,
                runtime=1.0,
                exception="Temporary error",
                retries=1,
                has_retries=True,
                args=args,
                kwargs=kwargs,
            ),
        ]

        # Retry attempt (succeeded)
        retry_attempt = [
            TaskEventDB(
                task_id=retry_id,
                task_name=task_name,
                event_type="task-received",
                timestamp=timestamp + timedelta(seconds=5),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=retry_id,
                retry_of=original_id,
                is_retry=True,
                retries=1,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=retry_id,
                task_name=task_name,
                event_type="task-started",
                timestamp=timestamp + timedelta(seconds=5.05),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=retry_id,
                retry_of=original_id,
                is_retry=True,
                retries=1,
                args=args,
                kwargs=kwargs,
            ),
            TaskEventDB(
                task_id=retry_id,
                task_name=task_name,
                event_type="task-succeeded",
                timestamp=timestamp + timedelta(seconds=6),
                hostname=worker,
                worker_name=worker,
                queue=queue,
                exchange="default",
                routing_key=queue,
                root_id=retry_id,
                runtime=0.95,
                result={"status": "completed"},
                retry_of=original_id,
                is_retry=True,
                retries=1,
                args=args,
                kwargs=kwargs,
            ),
        ]

        return first_attempt + retry_attempt

    def seed_worker_events(self, days_back: int = 7):
        """Seed worker heartbeat events."""
        print(f"👷 Seeding worker events for last {days_back} days...")

        events = []
        now = datetime.now(timezone.utc)

        for worker in self.worker_hostnames:
            # Generate heartbeats every 5 minutes for each worker
            start_time = now - timedelta(days=days_back)
            current_time = start_time

            while current_time <= now:
                events.append(
                    WorkerEventDB(
                        hostname=worker,
                        event_type="worker-heartbeat",
                        timestamp=current_time,
                        status="online",
                        active_tasks=[],
                        processed=random.randint(100, 1000),
                    )
                )
                current_time += timedelta(minutes=5)

        with self.db_manager.get_session() as session:
            for event in events:
                session.add(event)
            session.commit()

        print(f"   ✓ Created {len(events)} worker events")

    def seed_daily_stats(self, days_back: int = 7):
        """Seed daily aggregated statistics."""
        print(f"📈 Seeding daily statistics for last {days_back} days...")

        stats = []
        now = datetime.now(timezone.utc)

        for day_offset in range(days_back):
            current_date = (now - timedelta(days=day_offset)).date()

            for task_name in self.task_names:
                total_executions = random.randint(10, 200)
                succeeded = int(total_executions * random.uniform(0.85, 0.98))
                failed = int(total_executions * random.uniform(0.01, 0.10))
                retried = int(total_executions * random.uniform(0.01, 0.05))
                orphaned = total_executions - succeeded - failed - retried

                # Generate realistic runtime percentiles
                avg_runtime = random.uniform(0.5, 10.0)

                stats.append(
                    TaskDailyStatsDB(
                        task_name=task_name,
                        date=current_date,
                        total_executions=total_executions,
                        succeeded=succeeded,
                        failed=failed,
                        pending=0,
                        retried=retried,
                        revoked=0,
                        orphaned=orphaned,
                        avg_runtime=avg_runtime,
                        min_runtime=avg_runtime * 0.2,
                        max_runtime=avg_runtime * 3.0,
                        p50_runtime=avg_runtime * 0.9,
                        p95_runtime=avg_runtime * 1.8,
                        p99_runtime=avg_runtime * 2.5,
                        first_execution=datetime.combine(current_date, datetime.min.time()).replace(
                            tzinfo=timezone.utc
                        ),
                        last_execution=datetime.combine(current_date, datetime.max.time()).replace(
                            tzinfo=timezone.utc
                        ),
                    )
                )

        with self.db_manager.get_session() as session:
            for stat in stats:
                session.add(stat)
            session.commit()

        print(f"   ✓ Created {len(stats)} daily statistics records")


def main():
    """Main entry point for database seeder."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed Kanchi database with marketing/demo data")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days of historical data to generate (default: 7)",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Keep existing data (don't clear tables before seeding)",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        help="Database URL (default: from DATABASE_URL env var or sqlite:///kanchi.db)",
    )

    args = parser.parse_args()

    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL', 'sqlite:///kanchi.db')

    print(f"📦 Using database: {database_url}")

    # Initialize database manager
    db_manager = DatabaseManager(database_url)

    # Create seeder and run
    seeder = DatabaseSeeder(db_manager)
    seeder.seed_all(days_back=args.days, clear_existing=not args.keep_existing)

    print("\n✨ All done! Your database is now populated with marketing data.")
    print("   Start the application to see the results:")
    print("   $ poetry run python app.py")


if __name__ == "__main__":
    main()
