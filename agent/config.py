import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration for the Celery WebSocket Bridge"""
    
    # Celery broker configuration (RabbitMQ URL)
    broker_url: str = os.getenv('RABBITMQ_URL')
    
    # Database configuration
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///kanchi.db')  # Default to SQLite
    
    # WebSocket server configuration
    ws_host: str = os.getenv('WS_HOST', 'localhost')
    ws_port: int = int(os.getenv('WS_PORT', 8765))
    
    # Logging configuration
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Event filtering (optional)
    event_types_filter: Optional[list] = None  # If set, only these event types will be broadcast
    task_names_filter: Optional[list] = None   # If set, only these task names will be broadcast
    
    # Performance settings
    max_clients: int = int(os.getenv('MAX_WS_CLIENTS', 100))
    event_buffer_size: int = int(os.getenv('EVENT_BUFFER_SIZE', 1000))
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables"""
        config = cls()
        
        # Parse filter lists from environment if present
        event_types = os.getenv('EVENT_TYPES_FILTER', '')
        if event_types:
            config.event_types_filter = [e.strip() for e in event_types.split(',')]
        
        task_names = os.getenv('TASK_NAMES_FILTER', '')
        if task_names:
            config.task_names_filter = [t.strip() for t in task_names.split(',')]
        
        return config
    
    def should_broadcast_event(self, event_type: str, task_name: str) -> bool:
        """Check if an event should be broadcast based on filters"""
        if self.event_types_filter and event_type not in self.event_types_filter:
            return False
        
        if self.task_names_filter and task_name not in self.task_names_filter:
            return False
        
        return True
