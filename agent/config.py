import os
import secrets
from dataclasses import dataclass, field
from typing import List, Optional


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    """Parse truthy environment variables."""
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _split_csv(value: Optional[str]) -> List[str]:
    """Parse comma- or space-separated strings into a list."""
    if not value:
        return []
    parts: List[str] = []
    for item in value.replace(" ", "").split(","):
        if item:
            parts.append(item)
    return parts


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

    # CORS / Hosts
    allowed_origins: List[str] = field(default_factory=lambda: _split_csv(os.getenv('ALLOWED_ORIGINS')))
    allowed_hosts: List[str] = field(default_factory=lambda: _split_csv(os.getenv('ALLOWED_HOSTS')))
    cors_allow_credentials: bool = _as_bool(os.getenv('CORS_ALLOW_CREDENTIALS', 'true'), default=True)

    # Security & authentication
    auth_enabled: bool = _as_bool(os.getenv('AUTH_ENABLED', 'false'))
    auth_basic_enabled: bool = _as_bool(os.getenv('AUTH_BASIC_ENABLED', 'false'))
    auth_google_enabled: bool = _as_bool(os.getenv('AUTH_GOOGLE_ENABLED', 'false'))
    auth_github_enabled: bool = _as_bool(os.getenv('AUTH_GITHUB_ENABLED', 'false'))
    allowed_email_patterns: List[str] = field(
        default_factory=lambda: _split_csv(os.getenv('ALLOWED_EMAIL_PATTERNS'))
    )

    # Basic auth credentials (optional)
    basic_auth_username: Optional[str] = os.getenv('BASIC_AUTH_USERNAME')
    basic_auth_password: Optional[str] = os.getenv('BASIC_AUTH_PASSWORD')
    basic_auth_password_hash: Optional[str] = os.getenv('BASIC_AUTH_PASSWORD_HASH')

    # Token management
    session_secret_key: str = os.getenv('SESSION_SECRET_KEY', 'change-me')
    token_secret_key: str = os.getenv('TOKEN_SECRET_KEY', os.getenv('SESSION_SECRET_KEY', 'change-me'))
    access_token_lifetime_minutes: int = int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', 30))
    refresh_token_lifetime_hours: int = int(os.getenv('REFRESH_TOKEN_LIFETIME_HOURS', 24))

    # OAuth settings
    oauth_redirect_base_url: Optional[str] = os.getenv('OAUTH_REDIRECT_BASE_URL')
    google_client_id: Optional[str] = os.getenv('GOOGLE_CLIENT_ID')
    google_client_secret: Optional[str] = os.getenv('GOOGLE_CLIENT_SECRET')
    github_client_id: Optional[str] = os.getenv('GITHUB_CLIENT_ID')
    github_client_secret: Optional[str] = os.getenv('GITHUB_CLIENT_SECRET')
    oauth_state_ttl_minutes: int = int(os.getenv('OAUTH_STATE_TTL_MINUTES', 5))
    oauth_scope_google: List[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv('GOOGLE_OAUTH_SCOPES', 'openid,email,profile')
        )
    )
    oauth_scope_github: List[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv('GITHUB_OAUTH_SCOPES', 'read:user,user:email')
        )
    )

    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        return cls()

    def __post_init__(self) -> None:
        """Normalize secrets so we never operate with predictable defaults."""
        if self.session_secret_key == 'change-me':
            self.session_secret_key = secrets.token_urlsafe(32)

        if self.token_secret_key == 'change-me':
            # Default to the session secret to preserve existing behaviour.
            self.token_secret_key = self.session_secret_key
