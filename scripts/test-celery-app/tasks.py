"""
Sample Celery tasks for testing Kanchi monitoring capabilities.
"""
import time
import random
import json
import hashlib
from datetime import datetime
from celery import Task, group, chain, chord
from celery_app import app


class CallbackTask(Task):
    """Task with callbacks for monitoring state changes."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful execution."""
        print(f"Task {task_id} completed successfully with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure."""
        print(f"Task {task_id} failed with exception: {exc}")


@app.task(name='tasks.simple_task', 
          kanchi_description='Adds two numbers with random failure for testing',
          kanchi_category='arithmetic',
          kanchi_example_args='[5, 3]')
def simple_task(x, y):
    """Simple arithmetic task that adds two numbers.
    
    Randomly fails 50% of the time to demonstrate error handling.
    Useful for basic task monitoring and failure testing.
    """
    # Fail 50/50
    if random.choice([True, False]):
        raise ValueError("Random failure for testing")
    return x + y


@app.task(name='tasks.long_running_task', bind=True,
          kanchi_description='Simulates long-running work with progress updates',
          kanchi_category='simulation',
          kanchi_example_args='[30]')
def long_running_task(self, duration=10):
    """Long-running task with progress updates.
    
    Simulates a long-running process that updates its progress periodically.
    Perfect for testing progress tracking and monitoring long-running operations.
    """
    for i in range(duration):
        time.sleep(1)
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': duration, 'status': f'Processing step {i + 1}/{duration}'}
        )
    return {'status': 'completed', 'duration': duration}


@app.task(name='tasks.failing_task', bind=True, max_retries=3)
def failing_task(self, should_fail=True):
    """Task designed to fail and demonstrate retry behavior.
    
    Fails on first few attempts then succeeds, demonstrating Celery's
    automatic retry mechanism. Useful for testing retry logic and failure recovery.
    """
    attempt = self.request.retries + 1
    print(f"Attempt {attempt} of {self.max_retries + 1}")
    
    if should_fail and attempt <= 2:
        raise self.retry(exc=Exception(f"Failed on attempt {attempt}"), countdown=2)
    
    return f"Success on attempt {attempt}"


@app.task(name='tasks.random_delay_task')
def random_delay_task(min_delay=1, max_delay=5):
    """Task with random execution time.
    
    Simulates variable processing time by sleeping for a random duration.
    Useful for testing load balancing and variable workload scenarios.
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)
    return {'delay': delay, 'timestamp': datetime.utcnow().isoformat()}


@app.task(name='tasks.high_priority_task')
def high_priority_task(data):
    """High priority task for urgent processing.
    
    Designed for time-sensitive operations that need immediate attention.
    Typically routed to dedicated high-priority queues.
    """
    time.sleep(0.5)
    return {'priority': 'high', 'processed': data}


@app.task(name='tasks.low_priority_task')
def low_priority_task(data):
    """Low priority task for background processing.
    
    Handles non-urgent operations that can be processed when resources are available.
    Good for batch processing and cleanup operations.
    """
    time.sleep(2)
    return {'priority': 'low', 'processed': data}


@app.task(name='tasks.cpu_intensive_task')
def cpu_intensive_task(n=1000000):
    """CPU-intensive task for prime number calculation.
    
    Calculates prime numbers up to a given limit to simulate heavy CPU work.
    Useful for testing CPU utilization monitoring and worker performance.
    """
    primes = []
    for num in range(2, min(n, 10000)):
        if all(num % i != 0 for i in range(2, int(num ** 0.5) + 1)):
            primes.append(num)
    
    result = hashlib.sha256(str(primes).encode()).hexdigest()
    return {'primes_found': len(primes), 'hash': result}


@app.task(name='tasks.io_intensive_task')
def io_intensive_task(file_operations=10):
    """I/O intensive task simulating file operations.
    
    Performs multiple simulated I/O operations with delays.
    Good for testing I/O-bound workload monitoring and performance.
    """
    results = []
    for i in range(file_operations):
        data = f"Operation {i}: {datetime.utcnow().isoformat()}"
        time.sleep(0.1)
        results.append(data)
    
    return {'operations': file_operations, 'results': results[:5]}  # Return first 5 results


@app.task(name='tasks.memory_intensive_task')
def memory_intensive_task(size_mb=10):
    """Memory-intensive task for testing resource usage.
    
    Allocates and processes large amounts of memory to simulate memory-heavy operations.
    Useful for testing memory monitoring and resource constraints.
    """
    data = []
    for _ in range(size_mb):
        data.append([random.random() for _ in range(131072)])  # 131072 * 8 bytes ≈ 1MB
    
    result = sum(sum(chunk) for chunk in data)
    return {'size_mb': size_mb, 'result': result}


@app.task(name='tasks.chain_task_start')
def chain_task_start(value):
    return value * 2


@app.task(name='tasks.chain_task_middle')
def chain_task_middle(value):
    return value + 10


@app.task(name='tasks.chain_task_end')
def chain_task_end(value):
    return {'final_result': value, 'timestamp': datetime.utcnow().isoformat()}


@app.task(name='tasks.group_task_item')
def group_task_item(item_id, data):
    time.sleep(random.uniform(0.5, 2))
    return {'item_id': item_id, 'processed_data': data.upper() if isinstance(data, str) else data}


@app.task(name='tasks.chord_callback')
def chord_callback(results):
    return {
        'total_items': len(results),
        'results': results,
        'completed_at': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.periodic_task')
def periodic_task():
    """Periodic maintenance task.
    
    Designed to run on a schedule for routine maintenance operations.
    Useful for testing periodic task scheduling and cron-like functionality.
    """
    return {
        'type': 'periodic',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Periodic task executed'
    }


@app.task(name='tasks.health_check')
def health_check():
    """System health check task.
    
    Performs basic health checks on the Celery system and broker.
    Essential for monitoring system health and detecting connectivity issues.
    """
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'broker': app.conf.broker_url.split('@')[-1] if '@' in app.conf.broker_url else 'unknown'
    }


@app.task(name='tasks.error_types_task', bind=True)
def error_types_task(self, error_type='timeout'):
    if error_type == 'timeout':
        time.sleep(100)  # Will timeout if time_limit is set
    elif error_type == 'exception':
        raise ValueError(f"Intentional error: {error_type}")
    elif error_type == 'division':
        return 1 / 0
    elif error_type == 'memory':
        data = [0] * (10**9)
        return len(data)
    elif error_type == 'retry':
        if self.request.retries < 2:
            raise self.retry(exc=Exception(f"Retry attempt {self.request.retries + 1}"))
    
    return f"No error for type: {error_type}"


@app.task(name='tasks.dynamic_task', base=CallbackTask)
def dynamic_task(**kwargs):
    """Dynamic task that processes arbitrary arguments.
    
    Flexible task that can perform different operations based on input parameters.
    Useful for testing dynamic task creation and variable argument handling.
    """
    result = {'received_args': kwargs}
    
    # Process based on arguments
    if 'operation' in kwargs:
        op = kwargs['operation']
        if op == 'sum' and 'values' in kwargs:
            result['result'] = sum(kwargs['values'])
        elif op == 'concat' and 'strings' in kwargs:
            result['result'] = ''.join(kwargs['strings'])
    
    result['processed_at'] = datetime.utcnow().isoformat()
    return result


def create_workflow_examples():
    workflow_chain = chain(
        chain_task_start.s(5),
        chain_task_middle.s(),
        chain_task_end.s()
    )
    
    workflow_group = group(
        group_task_item.s(i, f"data_{i}")
        for i in range(5)
    )
    
    workflow_chord = chord(
        (group_task_item.s(i, f"item_{i}") for i in range(3)),
        chord_callback.s()
    )
    
    return {
        'chain': workflow_chain,
        'group': workflow_group,
        'chord': workflow_chord
    }


@app.task(name='tasks.trigger_workflow')
def trigger_workflow(workflow_type='chain'):
    """Trigger complex workflow patterns.
    
    Demonstrates Celery's workflow capabilities including chains, groups, and chords.
    Perfect for testing complex task orchestration and workflow monitoring.
    """
    """Trigger different workflow patterns."""
    workflows = create_workflow_examples()
    
    if workflow_type in workflows:
        result = workflows[workflow_type].apply_async()
        return {
            'workflow_type': workflow_type,
            'workflow_id': str(result.id) if hasattr(result, 'id') else 'multiple',
            'status': 'triggered'
        }
    
    return {'error': f'Unknown workflow type: {workflow_type}'}
