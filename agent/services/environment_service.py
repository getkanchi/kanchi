"""Service for managing environment filters."""

import logging
import uuid
import fnmatch
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import EnvironmentDB
from models import EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse

logger = logging.getLogger(__name__)


class EnvironmentService:
    """Service for environment filter operations."""

    def __init__(self, session: Session):
        self.session = session

    def create_environment(self, env_create: EnvironmentCreate) -> EnvironmentResponse:
        """Create a new environment."""
        env_id = str(uuid.uuid4())

        # If this is marked as default, unset any existing default
        if env_create.is_default:
            self._unset_all_defaults()

        env_db = EnvironmentDB(
            id=env_id,
            name=env_create.name,
            description=env_create.description,
            queue_patterns=env_create.queue_patterns,
            worker_patterns=env_create.worker_patterns,
            is_default=env_create.is_default,
            is_active=False,
        )

        self.session.add(env_db)
        self.session.commit()
        self.session.refresh(env_db)

        logger.info(f"Created environment: {env_create.name}")
        return EnvironmentResponse.model_validate(env_db)

    def list_environments(self) -> List[EnvironmentResponse]:
        """List all environments."""
        envs = self.session.query(EnvironmentDB).order_by(
            desc(EnvironmentDB.is_default),
            desc(EnvironmentDB.is_active),
            EnvironmentDB.name
        ).all()
        return [EnvironmentResponse.model_validate(env) for env in envs]

    def get_environment(self, env_id: str) -> Optional[EnvironmentResponse]:
        """Get environment by ID."""
        env = self.session.query(EnvironmentDB).filter(EnvironmentDB.id == env_id).first()
        if env:
            return EnvironmentResponse.model_validate(env)
        return None

    def get_active_environment(self) -> Optional[EnvironmentResponse]:
        """Get the currently active environment."""
        env = self.session.query(EnvironmentDB).filter(EnvironmentDB.is_active == True).first()
        if env:
            return EnvironmentResponse.model_validate(env)
        return None

    def update_environment(self, env_id: str, env_update: EnvironmentUpdate) -> Optional[EnvironmentResponse]:
        """Update an environment."""
        env = self.session.query(EnvironmentDB).filter(EnvironmentDB.id == env_id).first()
        if not env:
            return None

        # If setting as default, unset any existing default
        if env_update.is_default is True:
            self._unset_all_defaults()

        # Update fields
        if env_update.name is not None:
            env.name = env_update.name
        if env_update.description is not None:
            env.description = env_update.description
        if env_update.queue_patterns is not None:
            env.queue_patterns = env_update.queue_patterns
        if env_update.worker_patterns is not None:
            env.worker_patterns = env_update.worker_patterns
        if env_update.is_default is not None:
            env.is_default = env_update.is_default

        env.updated_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(env)

        logger.info(f"Updated environment: {env.name}")
        return EnvironmentResponse.model_validate(env)

    def delete_environment(self, env_id: str) -> bool:
        """Delete an environment."""
        env = self.session.query(EnvironmentDB).filter(EnvironmentDB.id == env_id).first()
        if not env:
            return False

        # Cannot delete active environment
        if env.is_active:
            logger.warning(f"Cannot delete active environment: {env.name}")
            return False

        self.session.delete(env)
        self.session.commit()

        logger.info(f"Deleted environment: {env.name}")
        return True

    def activate_environment(self, env_id: str) -> Optional[EnvironmentResponse]:
        """Activate an environment (deactivates all others)."""
        # Deactivate all environments
        self.session.query(EnvironmentDB).update({EnvironmentDB.is_active: False})

        # Activate the specified environment
        env = self.session.query(EnvironmentDB).filter(EnvironmentDB.id == env_id).first()
        if not env:
            self.session.commit()
            return None

        env.is_active = True
        self.session.commit()
        self.session.refresh(env)

        logger.info(f"Activated environment: {env.name}")
        return EnvironmentResponse.model_validate(env)

    def deactivate_all_environments(self) -> None:
        """Deactivate all environments (show all data)."""
        self.session.query(EnvironmentDB).update({EnvironmentDB.is_active: False})
        self.session.commit()
        logger.info("Deactivated all environments")

    def _unset_all_defaults(self):
        """Unset default flag on all environments."""
        self.session.query(EnvironmentDB).update({EnvironmentDB.is_default: False})

    @staticmethod
    def matches_patterns(value: str, patterns: List[str]) -> bool:
        """
        Check if a value matches any of the wildcard patterns.

        Args:
            value: The value to check (e.g., queue name or worker hostname)
            patterns: List of wildcard patterns (e.g., ["prod-*", "staging-?"])

        Returns:
            True if value matches any pattern, False otherwise
        """
        if not patterns:
            return True  # Empty patterns = match all

        for pattern in patterns:
            if fnmatch.fnmatch(value, pattern):
                return True
        return False

    def should_include_event(
        self,
        queue_name: Optional[str] = None,
        worker_hostname: Optional[str] = None,
        env: Optional[EnvironmentResponse] = None
    ) -> bool:
        """
        Check if an event should be included based on active environment filters.

        Args:
            queue_name: The queue name from the task event
            worker_hostname: The worker hostname from the task event
            env: Optional environment to check against (uses active if not provided)

        Returns:
            True if the event should be included, False if it should be filtered out
        """
        # Get active environment if not provided
        if env is None:
            env = self.get_active_environment()

        # No active environment = show all events
        if not env:
            return True

        # Check queue patterns if queue name is provided
        if queue_name and env.queue_patterns:
            if not self.matches_patterns(queue_name, env.queue_patterns):
                return False

        # Check worker patterns if hostname is provided
        if worker_hostname and env.worker_patterns:
            if not self.matches_patterns(worker_hostname, env.worker_patterns):
                return False

        return True
