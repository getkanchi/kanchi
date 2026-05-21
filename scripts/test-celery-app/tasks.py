"""
Sample Celery tasks for testing Kanchi monitoring capabilities.
"""
import time
import random
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from celery import Task, group, chain, chord
from celery_app import app

# Make local SDK available without installing a package.
try:
    from kanchi_sdk import send_kanchi_progress, define_kanchi_steps
except Exception as exc:
    print(f"Warning: failed to import kanchi_sdk: {exc}")
    define_kanchi_steps = None
    send_kanchi_progress = None


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


@app.task(name='tasks.data_processing_task')
def data_processing_task(data_size=1000):
    """Process and transform a large dataset.

    Simulates data transformation operations like filtering, mapping, and aggregation.
    Useful for testing data pipeline monitoring.
    """
    data = [random.randint(1, 100) for _ in range(data_size)]

    # Filter
    filtered = [x for x in data if x > 50]

    # Map
    squared = [x ** 2 for x in filtered]

    # Aggregate
    result = {
        'total': sum(squared),
        'count': len(squared),
        'average': sum(squared) / len(squared) if squared else 0,
        'max': max(squared) if squared else 0,
        'min': min(squared) if squared else 0
    }

    return result


@app.task(name='tasks.image_processing_task')
def image_processing_task(width=100, height=100, filters=5):
    """Simulate image processing operations.

    Mimics image manipulation tasks like resizing, filtering, and transformations.
    Good for testing media processing workflows.
    """
    # Simulate creating an image matrix
    image = [[random.randint(0, 255) for _ in range(width)] for _ in range(height)]

    # Apply filters
    for _ in range(filters):
        time.sleep(0.1)  # Simulate processing time

    # Calculate some statistics
    flat_image = [pixel for row in image for pixel in row]

    return {
        'dimensions': f'{width}x{height}',
        'filters_applied': filters,
        'brightness': sum(flat_image) / len(flat_image),
        'processed_at': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.api_request_task')
def api_request_task(endpoint='example.com', retries=0):
    """Simulate an API request with random delays.

    Mimics external API calls with variable response times.
    Perfect for testing integration monitoring and timeout handling.
    """
    delay = random.uniform(0.5, 2.0)
    time.sleep(delay)

    # Simulate occasional failures
    if random.random() < 0.1:  # 10% failure rate
        raise Exception(f"API request to {endpoint} failed")

    return {
        'endpoint': endpoint,
        'status_code': 200,
        'response_time': delay,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.database_query_task')
def database_query_task(query_type='SELECT', record_count=100):
    """Simulate database query operations.

    Mimics database operations like SELECT, INSERT, UPDATE.
    Useful for testing database-heavy application monitoring.
    """
    # Simulate query execution time based on record count
    execution_time = record_count / 1000 + random.uniform(0.1, 0.5)
    time.sleep(execution_time)

    return {
        'query_type': query_type,
        'records_affected': record_count,
        'execution_time': execution_time,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.email_send_task')
def email_send_task(recipient='user@example.com', template='welcome'):
    """Simulate sending an email.

    Mimics email delivery with template rendering.
    Good for testing notification system monitoring.
    """
    time.sleep(random.uniform(0.5, 1.5))

    return {
        'recipient': recipient,
        'template': template,
        'sent_at': datetime.utcnow().isoformat(),
        'message_id': hashlib.md5(f"{recipient}{datetime.utcnow()}".encode()).hexdigest()
    }


@app.task(name='tasks.sdk_progress_task')
def sdk_progress_task(total_steps=4, delay=0.5):
    """
    Demonstrates incremental percentage updates via the Kanchi SDK.
    """
    if not send_kanchi_progress:
        return {'status': 'sdk not available', 'reason': 'import failed'}

    for idx in range(total_steps + 1):
        percent = round((idx / total_steps) * 100, 2)
        send_kanchi_progress(
            percent,
            step_key=None,
            message=f"Checkpoint {idx}/{total_steps}"
        )
        time.sleep(delay)

    return {'status': 'completed', 'steps': total_steps}


@app.task(name='tasks.sdk_steps_task')
def sdk_steps_task(delay=0.75):
    """
    Demonstrates step definitions + per-step progress via the Kanchi SDK.
    """
    if not define_kanchi_steps or not send_kanchi_progress:
        return {'status': 'sdk not available', 'reason': 'import failed'}

    steps = [
        {"key": "prepare", "label": "Prepare payload"},
        {"key": "execute", "label": "Execute work"},
        {"key": "finalize", "label": "Finalize task"},
    ]

    define_kanchi_steps(steps)

    send_kanchi_progress(0, step_key="prepare", message="Starting preparation")
    time.sleep(delay)

    send_kanchi_progress(35, step_key="prepare", message="Preparation done")
    send_kanchi_progress(40, step_key="execute", message="Executing core work")
    time.sleep(delay)

    send_kanchi_progress(80, step_key="execute", message="Wrapping up execution")
    send_kanchi_progress(100, step_key="finalize", message="All steps completed")

    return {'status': 'completed', 'steps_defined': [s["key"] for s in steps]}


@app.task(name='tasks.report_generation_task', bind=True)
def report_generation_task(self, report_type='daily', sections=5):
    """Generate a report with progress tracking.

    Simulates report generation with multiple sections and progress updates.
    Perfect for testing long-running document generation monitoring.
    """
    for i in range(sections):
        time.sleep(1)
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': sections,
                'status': f'Generating section {i + 1}/{sections}'
            }
        )

    return {
        'report_type': report_type,
        'sections': sections,
        'size_kb': sections * random.randint(100, 500),
        'generated_at': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.cache_warmup_task')
def cache_warmup_task(cache_entries=50):
    """Warm up cache with pre-computed data.

    Simulates cache population operations.
    Useful for testing cache management and startup procedures.
    """
    cache_data = {}
    for i in range(cache_entries):
        key = f'cache_key_{i}'
        value = hashlib.sha256(str(random.random()).encode()).hexdigest()
        cache_data[key] = value
        time.sleep(0.05)

    return {
        'entries_cached': len(cache_data),
        'sample_keys': list(cache_data.keys())[:5],
        'timestamp': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.ml_prediction_task')
def ml_prediction_task(model='simple', features=10):
    """Simulate machine learning prediction.

    Mimics ML model inference with feature processing.
    Good for testing ML pipeline monitoring.
    """
    # Simulate feature extraction
    feature_vector = [random.random() for _ in range(features)]

    # Simulate prediction time
    time.sleep(random.uniform(0.3, 1.0))

    # Generate fake prediction
    prediction = sum(feature_vector) / len(feature_vector)
    confidence = random.uniform(0.7, 0.99)

    return {
        'model': model,
        'prediction': prediction,
        'confidence': confidence,
        'features_used': features,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.file_conversion_task')
def file_conversion_task(input_format='json', output_format='csv', size_mb=5):
    """Simulate file format conversion.

    Mimics converting files between different formats.
    Useful for testing file processing pipelines.
    """
    # Simulate conversion time based on file size
    conversion_time = size_mb * 0.2 + random.uniform(0.5, 1.5)
    time.sleep(conversion_time)

    return {
        'input_format': input_format,
        'output_format': output_format,
        'input_size_mb': size_mb,
        'output_size_mb': size_mb * random.uniform(0.8, 1.2),
        'conversion_time': conversion_time,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.notification_fanout_task')
def notification_fanout_task(user_count=10, notification_type='update'):
    """Send notifications to multiple users.

    Simulates fanout pattern for broadcasting notifications.
    Perfect for testing bulk notification systems.
    """
    results = []
    for i in range(user_count):
        time.sleep(0.1)
        results.append({
            'user_id': i,
            'status': 'sent',
            'notification_type': notification_type
        })

    return {
        'total_sent': user_count,
        'notification_type': notification_type,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.validation_task')
def validation_task(data_points=100, strict_mode=True):
    """Validate data against business rules.

    Simulates data validation with configurable strictness.
    Useful for testing data quality monitoring.
    """
    valid_count = 0
    invalid_count = 0
    errors = []

    for i in range(data_points):
        # Simulate validation
        is_valid = random.random() > 0.1  # 90% valid

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            if strict_mode:
                errors.append(f"Validation error at index {i}")

    if strict_mode and errors:
        raise ValueError(f"Validation failed: {len(errors)} errors found")

    return {
        'total_validated': data_points,
        'valid': valid_count,
        'invalid': invalid_count,
        'strict_mode': strict_mode,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.task(name='tasks.batch_import_task', bind=True)
def batch_import_task(self, batch_size=1000, batches=5):
    """Import data in batches with progress tracking.

    Simulates batch data import operations.
    Good for testing ETL pipeline monitoring.
    """
    total_imported = 0

    for batch_num in range(batches):
        time.sleep(1)
        imported = random.randint(int(batch_size * 0.9), batch_size)
        total_imported += imported

        self.update_state(
            state='PROGRESS',
            meta={
                'current_batch': batch_num + 1,
                'total_batches': batches,
                'imported_so_far': total_imported,
                'status': f'Processing batch {batch_num + 1}/{batches}'
            }
        )

    return {
        'total_imported': total_imported,
        'batches_processed': batches,
        'average_batch_size': total_imported / batches,
        'timestamp': datetime.utcnow().isoformat()
    }


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
