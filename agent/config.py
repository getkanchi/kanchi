import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for the Celery WebSocket Bridge"""

    # Celery broker configuration (supports both RabbitMQ and Redis)
    broker_url: str = os.getenv('CELERY_BROKER_URL')

    # Database configuration
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///kanchi.db')  # Default to SQLite

    # WebSocket server configuration
    ws_host: str = os.getenv('WS_HOST', 'localhost')
    ws_port: int = int(os.getenv('WS_PORT', 8765))

    # Development mode (enables unified logging)
    development_mode: bool = os.getenv('DEVELOPMENT_MODE', 'false').lower() in ('true', '1', 'yes')

    # Logging configuration
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_file: str = os.getenv('LOG_FILE', 'kanchi.log')

    # Performance settings
    max_clients: int = int(os.getenv('MAX_WS_CLIENTS', 100))
    event_buffer_size: int = int(os.getenv('EVENT_BUFFER_SIZE', 1000))
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        return cls()
