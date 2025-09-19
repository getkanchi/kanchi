#!/usr/bin/env python
"""
Script to run Celery worker with different configurations.
"""
import os
import sys
import argparse
from celery_app import app

# Import tasks to register them
import tasks  # noqa: F401


def main():
    parser = argparse.ArgumentParser(description='Run Celery worker with custom configuration')
    parser.add_argument('--queues', '-Q', 
                       default='default',
                       help='Comma-separated list of queues to consume from')
    parser.add_argument('--concurrency', '-c',
                       type=int,
                       default=4,
                       help='Number of concurrent worker processes/threads')
    parser.add_argument('--loglevel', '-l',
                       default='info',
                       choices=['debug', 'info', 'warning', 'error', 'critical'],
                       help='Logging level')
    parser.add_argument('--hostname', '-n',
                       default=None,
                       help='Set custom hostname for the worker')
    parser.add_argument('--pool', '-P',
                       default='prefork',
                       choices=['prefork', 'eventlet', 'gevent', 'solo', 'threads'],
                       help='Pool implementation')
    parser.add_argument('--autoscale',
                       default=None,
                       help='Autoscaling settings (max,min)')
    parser.add_argument('--events', '-E',
                       action='store_true',
                       help='Send task events for monitoring')
    
    args = parser.parse_args()
    
    # Build worker arguments
    worker_args = [
        'worker',
        '--loglevel', args.loglevel,
        '--concurrency', str(args.concurrency),
        '--queues', args.queues,
        '--pool', args.pool,
    ]
    
    if args.hostname:
        worker_args.extend(['--hostname', args.hostname])
    
    if args.autoscale:
        worker_args.extend(['--autoscale', args.autoscale])
    
    if args.events:
        worker_args.append('--events')
    
    app.worker_main(argv=worker_args)


if __name__ == '__main__':
    main()
