"""Service for managing action configurations."""

import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from database import ActionConfigDB
from models import ActionConfigDefinition, ActionConfigCreateRequest, ActionConfigUpdateRequest

logger = logging.getLogger(__name__)


class ActionConfigService:
    """Service for action config CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create_config(self, config_data: ActionConfigCreateRequest) -> ActionConfigDefinition:
        """Create a new action configuration."""
        config_id = str(uuid.uuid4())

        config_db = ActionConfigDB(
            id=config_id,
            name=config_data.name,
            description=config_data.description,
            action_type=config_data.action_type,
            config=config_data.config
        )

        self.session.add(config_db)
        self.session.commit()

        logger.info(f"Created action config: {config_data.name} (type={config_data.action_type})")

        return self._db_to_config(config_db)

    def get_config(self, config_id: str) -> Optional[ActionConfigDefinition]:
        """Get action config by ID."""
        config_db = self.session.query(ActionConfigDB).filter_by(id=config_id).first()
        return self._db_to_config(config_db) if config_db else None

    def get_config_by_name(self, name: str) -> Optional[ActionConfigDefinition]:
        """Get action config by name."""
        config_db = self.session.query(ActionConfigDB).filter_by(name=name).first()
        return self._db_to_config(config_db) if config_db else None

    def list_configs(
        self,
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActionConfigDefinition]:
        """List action configs with filtering."""
        query = self.session.query(ActionConfigDB)

        if action_type:
            query = query.filter(ActionConfigDB.action_type == action_type)

        query = query.order_by(ActionConfigDB.name)
        query = query.limit(limit).offset(offset)

        configs_db = query.all()
        return [self._db_to_config(c) for c in configs_db]

    def update_config(
        self,
        config_id: str,
        updates: ActionConfigUpdateRequest
    ) -> Optional[ActionConfigDefinition]:
        """Update an existing action config."""
        config_db = self.session.query(ActionConfigDB).filter_by(id=config_id).first()

        if not config_db:
            return None

        update_dict = updates.dict(exclude_unset=True)

        for field, value in update_dict.items():
            if hasattr(config_db, field):
                setattr(config_db, field, value)

        config_db.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        logger.info(f"Updated action config: {config_id}")

        return self._db_to_config(config_db)

    def delete_config(self, config_id: str) -> bool:
        """Delete an action config."""
        config_db = self.session.query(ActionConfigDB).filter_by(id=config_id).first()

        if not config_db:
            return False

        self.session.delete(config_db)
        self.session.commit()

        logger.info(f"Deleted action config: {config_id}")
        return True

    def increment_usage(self, config_id: str):
        """Increment usage count for an action config."""
        config_db = self.session.query(ActionConfigDB).filter_by(id=config_id).first()

        if config_db:
            config_db.usage_count += 1
            config_db.last_used_at = datetime.now(timezone.utc)
            self.session.commit()

    def _db_to_config(self, config_db: ActionConfigDB) -> ActionConfigDefinition:
        """Convert database model to Pydantic model."""
        return ActionConfigDefinition(
            id=config_db.id,
            name=config_db.name,
            description=config_db.description,
            action_type=config_db.action_type,
            config=config_db.config,
            created_at=config_db.created_at,
            updated_at=config_db.updated_at,
            created_by=config_db.created_by,
            usage_count=config_db.usage_count,
            last_used_at=config_db.last_used_at
        )
