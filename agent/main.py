#!/usr/bin/env python3
"""
Legacy main.py - now redirects to FastAPI app
For backwards compatibility, this can still be used but FastAPI app is recommended
"""
import argparse
import logging
import uvicorn
from config import Config

logger = logging.getLogger(__name__)


def main():
    """Main entry point - now uses FastAPI app"""
    parser = argparse.ArgumentParser(description='Celery Event Monitor with FastAPI and WebSocket Broadcasting')
    parser.add_argument(
        '--broker',
        help='Celery broker URL (can also set CELERY_BROKER_URL env var)'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Server host (default: localhost, can also set WS_HOST env var)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='Server port (default: 8765, can also set WS_PORT env var)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO, can also set LOG_LEVEL env var)'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )
    
    args = parser.parse_args()
    
    # Override config with command line args if provided
    config = Config.from_env()
    if args.broker:
        config.broker_url = args.broker
    if args.host != 'localhost':
        config.ws_host = args.host
    if args.port != 8765:
        config.ws_port = args.port
    if args.log_level != 'INFO':
        config.log_level = args.log_level
    
    logger.info(f"Starting Celery Event Monitor server on {config.ws_host}:{config.ws_port}")
    logger.info(f"Monitoring Celery broker: {config.broker_url}")
    logger.info(f"Web interface: http://{config.ws_host}:{config.ws_port}")
    logger.info(f"WebSocket endpoint: ws://{config.ws_host}:{config.ws_port}/ws")
    
    # Start the FastAPI server
    uvicorn.run(
        "app:app",
        host=config.ws_host,
        port=config.ws_port,
        log_level=config.log_level.lower(),
        reload=args.reload
    )


if __name__ == '__main__':
    main()
