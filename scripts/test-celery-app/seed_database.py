#!/usr/bin/env python3
"""
Seed the Kanchi database with realistic test data.

Usage:
    python scripts/seed_database.py [--clear] [--tasks N]

Options:
    --clear    Clear existing data before seeding
    --tasks N  Number of tasks to create (default: 10)
"""

import sys
import os
import random
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add agent directory to path
agent_path = Path(__file__).parent.parent.parent / 'agent'
sys.path.insert(0, str(agent_path))

from database import DatabaseManager, TaskRegistryDB, TaskEventDB, TaskDailyStatsDB
from sqlalchemy import func


class DatabaseSeeder:
    """Seed database with realistic Celery task data."""

    def __init__(self, database_url: str = None):
        # Default to kanchi.db in agent directory (relative to script location)
        if database_url is None:
            script_dir = Path(__file__).parent.parent.parent  # Go up to project root
            db_path = script_dir / 'agent' / 'kanchi.db'
            database_url = f"sqlite:///{db_path.absolute()}"

        self.db_manager = DatabaseManager(database_url)
        self.task_names = [
            "tasks.process_payment",
            "tasks.send_email",
            "tasks.generate_report",
            "tasks.backup_database",
            "tasks.sync_inventory",
            "tasks.process_refund",
            "tasks.update_analytics",
            "tasks.cleanup_temp_files",
            "tasks.send_notifications",
            "tasks.export_data",
            "tasks.import_orders",
            "tasks.calculate_metrics",
            "tasks.optimize_images",
            "tasks.archive_old_records",
            "tasks.refresh_cache",
        ]

        self.task_metadata = {
            "tasks.process_payment": {
                "human_readable_name": "Process Payment",
                "description": "Process customer payments via Stripe API",
                "tags": ["payment", "critical", "financial"],
            },
            "tasks.send_email": {
                "human_readable_name": "Send Email",
                "description": "Send transactional emails to customers",
                "tags": ["email", "notification"],
            },
            "tasks.generate_report": {
                "human_readable_name": "Generate Report",
                "description": "Generate and export business intelligence reports",
                "tags": ["analytics", "reporting"],
            },
            "tasks.backup_database": {
                "human_readable_name": "Backup Database",
                "description": "Create incremental database backups",
                "tags": ["maintenance", "critical"],
            },
            "tasks.sync_inventory": {
                "human_readable_name": "Sync Inventory",
                "description": "Synchronize inventory levels across warehouses",
                "tags": ["inventory", "sync"],
            },
            "tasks.process_refund": {
                "human_readable_name": "Process Refund",
                "description": "Process customer refunds and update accounts",
                "tags": ["payment", "financial"],
            },
            "tasks.update_analytics": {
                "human_readable_name": "Update Analytics",
                "description": "Update real-time analytics dashboard metrics",
                "tags": ["analytics", "metrics"],
            },
            "tasks.cleanup_temp_files": {
                "human_readable_name": "Cleanup Temp Files",
                "description": "Clean up temporary files and expired sessions",
                "tags": ["maintenance", "cleanup"],
            },
            "tasks.send_notifications": {
                "human_readable_name": "Send Notifications",
                "description": "Send push notifications to mobile apps",
                "tags": ["notification", "mobile"],
            },
            "tasks.export_data": {
                "human_readable_name": "Export Data",
                "description": "Export data to external systems",
                "tags": ["export", "integration"],
            },
            "tasks.import_orders": {
                "human_readable_name": "Import Orders",
                "description": "Import orders from external marketplaces",
                "tags": ["import", "orders"],
            },
            "tasks.calculate_metrics": {
                "human_readable_name": "Calculate Metrics",
                "description": "Calculate business KPIs and performance metrics",
                "tags": ["analytics", "kpi"],
            },
            "tasks.optimize_images": {
                "human_readable_name": "Optimize Images",
                "description": "Compress and optimize uploaded images",
                "tags": ["media", "optimization"],
            },
            "tasks.archive_old_records": {
                "human_readable_name": "Archive Old Records",
                "description": "Archive old database records for compliance",
                "tags": ["maintenance", "compliance"],
            },
            "tasks.refresh_cache": {
                "human_readable_name": "Refresh Cache",
                "description": "Refresh Redis cache for frequently accessed data",
                "tags": ["cache", "performance"],
            },
        }

    def clear_data(self):
        """Clear all existing task data."""
        print("🗑️  Clearing existing data...")
        with self.db_manager.get_session() as session:
            session.query(TaskEventDB).delete()
            session.query(TaskDailyStatsDB).delete()
            session.query(TaskRegistryDB).delete()
            session.commit()
        print("✅ Data cleared")

    def seed_task_registry(self, num_tasks: int = 10):
        """Create task registry entries."""
        print(f"📋 Creating {num_tasks} task registry entries...")

        selected_tasks = random.sample(self.task_names, min(num_tasks, len(self.task_names)))
        now = datetime.now(timezone.utc)

        with self.db_manager.get_session() as session:
            for task_name in selected_tasks:
                metadata = self.task_metadata.get(task_name, {})
                first_seen = now - timedelta(days=random.randint(7, 90))

                task = TaskRegistryDB(
                    id=str(uuid.uuid4()),
                    name=task_name,
                    human_readable_name=metadata.get("human_readable_name"),
                    description=metadata.get("description"),
                    tags=metadata.get("tags", []),
                    created_at=first_seen,
                    updated_at=now,
                    first_seen=first_seen,
                    last_seen=now - timedelta(minutes=random.randint(0, 120)),
                )
                session.add(task)

            session.commit()

        print(f"✅ Created {num_tasks} task registry entries")
        return selected_tasks

    def generate_execution_pattern(self, task_name: str, hours_back: int = 24):
        """Generate realistic execution pattern for a task."""
        patterns = {
            "high_frequency": {  # Runs every few minutes
                "executions_per_hour": random.randint(20, 40),
                "failure_rate": 0.02,
                "avg_runtime": random.uniform(0.1, 0.5),
            },
            "medium_frequency": {  # Runs several times per hour
                "executions_per_hour": random.randint(5, 15),
                "failure_rate": 0.05,
                "avg_runtime": random.uniform(0.5, 2.0),
            },
            "low_frequency": {  # Runs occasionally
                "executions_per_hour": random.randint(1, 3),
                "failure_rate": 0.10,
                "avg_runtime": random.uniform(2.0, 10.0),
            },
            "cron_hourly": {  # Runs once per hour
                "executions_per_hour": 1,
                "failure_rate": 0.03,
                "avg_runtime": random.uniform(5.0, 30.0),
            },
        }

        # Assign patterns based on task type
        if "payment" in task_name or "notification" in task_name:
            pattern_type = "high_frequency"
        elif "sync" in task_name or "email" in task_name:
            pattern_type = "medium_frequency"
        elif "backup" in task_name or "archive" in task_name:
            pattern_type = "cron_hourly"
        else:
            pattern_type = random.choice(["medium_frequency", "low_frequency"])

        return patterns[pattern_type]

    def seed_task_events(self, task_names: list, hours_back: int = 24):
        """Generate task events over the specified time period."""
        print(f"⚡ Generating task events for last {hours_back} hours...")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)

        events_created = 0

        with self.db_manager.get_session() as session:
            for task_name in task_names:
                pattern = self.generate_execution_pattern(task_name, hours_back)

                # Calculate total executions
                total_executions = int(pattern["executions_per_hour"] * hours_back)

                # Generate events spread across time period
                for i in range(total_executions):
                    # Random timestamp within the period
                    random_offset = random.uniform(0, hours_back * 3600)
                    timestamp = start_time + timedelta(seconds=random_offset)

                    task_id = str(uuid.uuid4())

                    # Task received
                    event = TaskEventDB(
                        task_id=task_id,
                        task_name=task_name,
                        event_type="task-received",
                        timestamp=timestamp,
                        hostname=f"worker{random.randint(1, 3)}@celery",
                        worker_name=f"worker{random.randint(1, 3)}",
                        queue="default",
                        routing_key="celery",
                        args="[]",
                        kwargs="{}",
                        retries=0,
                    )
                    session.add(event)
                    events_created += 1

                    # Determine success or failure
                    failed = random.random() < pattern["failure_rate"]
                    runtime = random.gauss(pattern["avg_runtime"], pattern["avg_runtime"] * 0.3)
                    runtime = max(0.01, runtime)  # Minimum 10ms

                    if failed:
                        # Task failed
                        failure_event = TaskEventDB(
                            task_id=task_id,
                            task_name=task_name,
                            event_type="task-failed",
                            timestamp=timestamp + timedelta(seconds=runtime),
                            hostname=event.hostname,
                            worker_name=event.worker_name,
                            runtime=runtime,
                            exception="TaskExecutionError",
                            traceback="Simulated error traceback",
                        )
                        session.add(failure_event)
                        events_created += 1

                        # Sometimes retry
                        if random.random() < 0.6:
                            retry_id = str(uuid.uuid4())
                            retry_event = TaskEventDB(
                                task_id=retry_id,
                                task_name=task_name,
                                event_type="task-retried",
                                timestamp=timestamp + timedelta(seconds=runtime + 1),
                                hostname=event.hostname,
                                worker_name=event.worker_name,
                                retry_of=task_id,
                                is_retry=True,
                                retries=1,
                            )
                            session.add(retry_event)
                            events_created += 1

                            # Retry usually succeeds
                            if random.random() < 0.8:
                                success_event = TaskEventDB(
                                    task_id=retry_id,
                                    task_name=task_name,
                                    event_type="task-succeeded",
                                    timestamp=timestamp + timedelta(seconds=runtime + 2),
                                    hostname=event.hostname,
                                    worker_name=event.worker_name,
                                    runtime=runtime * 0.9,
                                    result='{"status": "success"}',
                                )
                                session.add(success_event)
                                events_created += 1
                    else:
                        # Task succeeded
                        success_event = TaskEventDB(
                            task_id=task_id,
                            task_name=task_name,
                            event_type="task-succeeded",
                            timestamp=timestamp + timedelta(seconds=runtime),
                            hostname=event.hostname,
                            worker_name=event.worker_name,
                            runtime=runtime,
                            result='{"status": "success"}',
                        )
                        session.add(success_event)
                        events_created += 1

                # Commit per task to avoid huge transactions
                session.commit()

        print(f"✅ Created {events_created} task events")

    def seed_daily_stats(self, task_names: list, days_back: int = 30):
        """Generate daily statistics for tasks."""
        print(f"📊 Generating daily stats for last {days_back} days...")

        end_date = datetime.now(timezone.utc).date()

        with self.db_manager.get_session() as session:
            for task_name in task_names:
                pattern = self.generate_execution_pattern(task_name)

                for day_offset in range(days_back):
                    stat_date = end_date - timedelta(days=day_offset)

                    # Calculate stats for this day
                    total = int(pattern["executions_per_hour"] * 24)
                    total = max(1, int(total * random.uniform(0.8, 1.2)))  # Add variance

                    succeeded = int(total * (1 - pattern["failure_rate"]))
                    failed = total - succeeded
                    retried = int(failed * 0.6)

                    stats = TaskDailyStatsDB(
                        task_name=task_name,
                        date=stat_date,
                        total_executions=total,
                        succeeded=succeeded,
                        failed=failed,
                        pending=0,
                        retried=retried,
                        revoked=0,
                        orphaned=random.randint(0, 2) if failed > 0 else 0,
                        avg_runtime=pattern["avg_runtime"],
                        min_runtime=pattern["avg_runtime"] * 0.5,
                        max_runtime=pattern["avg_runtime"] * 2.0,
                        first_execution=datetime.combine(stat_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                        last_execution=datetime.combine(stat_date, datetime.max.time()).replace(tzinfo=timezone.utc),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    session.add(stats)

                session.commit()

        print(f"✅ Created daily stats for {len(task_names)} tasks over {days_back} days")

    def run(self, clear: bool = False, num_tasks: int = 10, hours_back: int = 24, days_back: int = 30):
        """Run the full seeding process."""
        print("\n🌱 Starting database seeding...")
        print(f"   Tasks: {num_tasks}")
        print(f"   Recent events: {hours_back} hours")
        print(f"   Daily stats: {days_back} days")
        print()

        if clear:
            self.clear_data()

        # Seed data
        task_names = self.seed_task_registry(num_tasks)
        self.seed_task_events(task_names, hours_back)
        self.seed_daily_stats(task_names, days_back)

        print("\n✨ Database seeding complete!")
        print(f"   Visit http://localhost:3000/tasks to see the results")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed Kanchi database with test data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    parser.add_argument("--tasks", type=int, default=10, help="Number of tasks to create")
    parser.add_argument("--hours", type=int, default=24, help="Hours of event history")
    parser.add_argument("--days", type=int, default=30, help="Days of daily stats")
    parser.add_argument("--db", type=str, default=None, help="Database URL (default: agent/kanchi.db)")

    args = parser.parse_args()

    seeder = DatabaseSeeder(args.db)
    seeder.run(
        clear=args.clear,
        num_tasks=args.tasks,
        hours_back=args.hours,
        days_back=args.days
    )


if __name__ == "__main__":
    main()
