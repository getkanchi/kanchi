"""
Celery application for testing Kanchi monitoring.
"""
from celery import Celery
from kombu import Queue
import os

BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672//')
BACKEND_URL = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

app = Celery('test_celery_app')

app.conf.update(
    broker_url=BROKER_URL,
    result_backend=BACKEND_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_send_sent_event=True,
    worker_send_task_events=True,
    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='task.#'),
        Queue('high_priority', routing_key='high.#'),
        Queue('low_priority', routing_key='low.#'),
        Queue('cpu_intensive', routing_key='cpu.#'),
        Queue('io_intensive', routing_key='io.#'),
    ),
    task_routes={
        'tasks.high_priority_task': {'queue': 'high_priority'},
        'tasks.low_priority_task': {'queue': 'low_priority'},
        'tasks.cpu_intensive_task': {'queue': 'cpu_intensive'},
        'tasks.io_intensive_task': {'queue': 'io_intensive'},
    },
    task_annotations={
        'tasks.long_running_task': {'time_limit': 300},
        'tasks.cpu_intensive_task': {'time_limit': 60},
    },
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    beat_schedule={
        'periodic-hello': {
            'task': 'tasks.periodic_task',
            'schedule': 30.0,
        },
        'health-check': {
            'task': 'tasks.health_check',
            'schedule': 60.0,
        },
    },
)

app.autodiscover_tasks(['tasks'], force=True)

if __name__ == '__main__':
    app.start()
