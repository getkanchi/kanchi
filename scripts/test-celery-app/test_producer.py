#!/usr/bin/env python
"""
Test producer to generate various Celery tasks for monitoring testing.
"""
import time
import random
import argparse
from datetime import datetime
from celery_app import app
from tasks import (
    simple_task,
    long_running_task,
    failing_task,
    random_delay_task,
    high_priority_task,
    low_priority_task,
    cpu_intensive_task,
    io_intensive_task,
    memory_intensive_task,
    error_types_task,
    dynamic_task,
    trigger_workflow,
    sdk_progress_task,
    sdk_steps_task,
)


class TaskProducer:
    """Generate test tasks for Kanchi monitoring."""
    
    def __init__(self, rate=1.0, burst=False):
        self.rate = rate  # Tasks per second
        self.burst = burst
        self.task_count = 0
        self.start_time = datetime.utcnow()
    
    def generate_simple_tasks(self, count=10):
        """Generate simple arithmetic tasks."""
        print(f"Generating {count} simple tasks...")
        results = []
        for i in range(count):
            x, y = random.randint(1, 100), random.randint(1, 100)
            result = simple_task.delay(x, y)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def generate_long_running_tasks(self, count=5):
        """Generate long-running tasks."""
        print(f"Generating {count} long-running tasks...")
        results = []
        for i in range(count):
            duration = random.randint(5, 20)
            result = long_running_task.delay(duration=duration)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def generate_failing_tasks(self, count=5):
        """Generate tasks that will fail and retry."""
        print(f"Generating {count} failing tasks...")
        results = []
        for i in range(count):
            result = failing_task.delay(should_fail=True)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def generate_priority_tasks(self, count=10):
        """Generate tasks with different priorities."""
        print(f"Generating {count} priority tasks...")
        results = []
        for i in range(count):
            if random.random() > 0.7:
                result = high_priority_task.delay(f"urgent_data_{i}")
            else:
                result = low_priority_task.delay(f"normal_data_{i}")
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def generate_resource_intensive_tasks(self, count=5):
        """Generate CPU, IO, and memory intensive tasks."""
        print(f"Generating {count} resource-intensive tasks...")
        results = []
        task_types = [
            (cpu_intensive_task, {}),
            (io_intensive_task, {'file_operations': random.randint(5, 20)}),
            (memory_intensive_task, {'size_mb': random.randint(5, 20)})
        ]
        
        for i in range(count):
            task_func, kwargs = random.choice(task_types)
            result = task_func.delay(**kwargs)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def generate_workflow_tasks(self, count=3):
        """Generate workflow tasks (chains, groups, chords)."""
        print(f"Generating {count} workflow tasks...")
        results = []
        workflow_types = ['chain', 'group', 'chord']
        
        for i in range(count):
            workflow_type = random.choice(workflow_types)
            result = trigger_workflow.delay(workflow_type=workflow_type)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def generate_error_tasks(self, count=5):
        """Generate tasks with different error types."""
        print(f"Generating {count} error tasks...")
        results = []
        error_types = ['exception', 'division', 'retry', 'timeout']
        
        for i in range(count):
            error_type = random.choice(error_types)
            result = error_types_task.delay(error_type=error_type)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def generate_mixed_load(self, duration=60):
        """Generate mixed load for specified duration."""
        print(f"Generating mixed load for {duration} seconds...")
        end_time = time.time() + duration
        results = []
        
        task_generators = [
            (self.generate_simple_tasks, {'count': random.randint(5, 15)}),
            (self.generate_long_running_tasks, {'count': random.randint(1, 3)}),
            (self.generate_failing_tasks, {'count': random.randint(1, 3)}),
            (self.generate_priority_tasks, {'count': random.randint(3, 8)}),
            (self.generate_resource_intensive_tasks, {'count': random.randint(1, 3)}),
            (self.generate_workflow_tasks, {'count': 1}),
            (self.generate_error_tasks, {'count': random.randint(1, 2)})
        ]
        
        while time.time() < end_time:
            generator, kwargs = random.choice(task_generators)
            batch_results = generator(**kwargs)
            results.extend(batch_results)
            
            # Random pause between batches
            if not self.burst:
                time.sleep(random.uniform(1, 5))
        
        return results
    
    def generate_stress_test(self, total_tasks=1000):
        """Generate high volume of tasks for stress testing."""
        print(f"Starting stress test with {total_tasks} tasks...")
        results = []
        batch_size = 100
        
        for batch in range(0, total_tasks, batch_size):
            current_batch = min(batch_size, total_tasks - batch)
            print(f"Generating batch {batch // batch_size + 1}: {current_batch} tasks")
            
            for i in range(current_batch):
                # Mix of different task types
                task_type = random.randint(0, 4)
                if task_type == 0:
                    result = simple_task.delay(random.randint(1, 100), random.randint(1, 100))
                elif task_type == 1:
                    result = random_delay_task.delay()
                elif task_type == 2:
                    result = high_priority_task.delay(f"data_{i}")
                elif task_type == 3:
                    result = low_priority_task.delay(f"data_{i}")
                else:
                    result = dynamic_task.delay(
                        operation='sum',
                        values=[random.randint(1, 10) for _ in range(5)]
                    )
                
                results.append(result)
                self.task_count += 1
            
            # Small pause between batches to avoid overwhelming
            if not self.burst:
                time.sleep(0.5)
        
        return results

    def generate_sdk_progress(self, count=1, total_steps=5, delay=3):
        """Generate tasks that emit percentage-only progress via SDK."""
        print(f"Generating {count} SDK progress tasks...")
        results = []
        for _ in range(count):
            result = sdk_progress_task.delay(total_steps=total_steps, delay=delay)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results

    def generate_sdk_steps(self, count=1, delay=4.0):
        """Generate tasks that define steps and emit per-step progress via SDK."""
        print(f"Generating {count} SDK steps tasks...")
        results = []
        for _ in range(count):
            result = sdk_steps_task.delay(delay=delay)
            results.append(result)
            self.task_count += 1
            if not self.burst:
                time.sleep(1 / self.rate)
        return results
    
    def print_stats(self):
        """Print statistics about generated tasks."""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        print(f"\n--- Task Generation Stats ---")
        print(f"Total tasks generated: {self.task_count}")
        print(f"Time elapsed: {elapsed:.2f} seconds")
        print(f"Average rate: {self.task_count / elapsed:.2f} tasks/second")


def main():
    parser = argparse.ArgumentParser(description='Generate test Celery tasks')
    parser.add_argument('--mode', '-m',
                       default='mixed',
                       choices=['simple', 'long', 'failing', 'priority', 'resource',
                               'workflow', 'error', 'mixed', 'stress', 'sdk-progress', 'sdk-steps'],
                       help='Type of tasks to generate')
    parser.add_argument('--count', '-c',
                       type=int,
                       default=10,
                       help='Number of tasks to generate')
    parser.add_argument('--duration', '-d',
                       type=int,
                       default=60,
                       help='Duration for mixed load (seconds)')
    parser.add_argument('--rate', '-r',
                       type=float,
                       default=1.0,
                       help='Task generation rate (tasks per second)')
    parser.add_argument('--burst', '-b',
                       action='store_true',
                       help='Generate tasks in burst mode (no delays)')
    
    args = parser.parse_args()
    
    producer = TaskProducer(rate=args.rate, burst=args.burst)
    
    try:
        if args.mode == 'simple':
            results = producer.generate_simple_tasks(args.count)
        elif args.mode == 'long':
            results = producer.generate_long_running_tasks(args.count)
        elif args.mode == 'failing':
            results = producer.generate_failing_tasks(args.count)
        elif args.mode == 'priority':
            results = producer.generate_priority_tasks(args.count)
        elif args.mode == 'resource':
            results = producer.generate_resource_intensive_tasks(args.count)
        elif args.mode == 'workflow':
            results = producer.generate_workflow_tasks(args.count)
        elif args.mode == 'error':
            results = producer.generate_error_tasks(args.count)
        elif args.mode == 'mixed':
            results = producer.generate_mixed_load(args.duration)
        elif args.mode == 'stress':
            results = producer.generate_stress_test(args.count)
        elif args.mode == 'sdk-progress':
            results = producer.generate_sdk_progress(args.count)
        elif args.mode == 'sdk-steps':
            results = producer.generate_sdk_steps(args.count)
        
        producer.print_stats()
        
        # Optionally wait for some results
        if args.mode in ['simple', 'priority'] and not args.burst:
            print("\nChecking first 5 task results...")
            for result in results[:5]:
                try:
                    print(f"Task {result.id}: {result.get(timeout=5)}")
                except Exception as e:
                    print(f"Task {result.id}: Failed - {e}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        producer.print_stats()


if __name__ == '__main__':
    main()
