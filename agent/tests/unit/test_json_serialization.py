"""Test JSON serialization fix for Celery task events."""

import json
import pytest
from datetime import datetime, timezone

from services.task_service import make_json_serializable, TaskService
from models import TaskEvent
from database import DatabaseManager


class TestMakeJsonSerializable:
    """Test the make_json_serializable function."""

    def test_handles_ellipsis(self):
        """Test that Ellipsis is converted to string."""
        result = make_json_serializable(Ellipsis)
        assert result == "..."
        # Verify it's JSON serializable
        assert json.dumps(result) == '"..."'

    def test_handles_set(self):
        """Test that sets are converted to lists."""
        test_set = {1, 2, 3}
        result = make_json_serializable(test_set)
        assert isinstance(result, list)
        assert set(result) == test_set
        # Verify it's JSON serializable
        json.dumps(result)

    def test_handles_nested_structures_with_ellipsis(self):
        """Test nested structures containing Ellipsis."""
        data = {
            "args": [1, 2, Ellipsis],
            "kwargs": {"key": "value", "default": Ellipsis}
        }
        result = make_json_serializable(data)
        assert result["args"] == [1, 2, "..."]
        assert result["kwargs"]["default"] == "..."
        # Verify it's JSON serializable
        json.dumps(result)

    def test_handles_nested_structures_with_sets(self):
        """Test nested structures containing sets."""
        data = {
            "items": {1, 2, 3},
            "nested": {"inner_set": {"a", "b", "c"}}
        }
        result = make_json_serializable(data)
        assert isinstance(result["items"], list)
        assert isinstance(result["nested"]["inner_set"], list)
        # Verify it's JSON serializable
        json.dumps(result)

    def test_handles_tuples(self):
        """Test that tuples are converted to lists."""
        data = (1, 2, 3)
        result = make_json_serializable(data)
        assert result == [1, 2, 3]
        # Verify it's JSON serializable
        json.dumps(result)

    def test_preserves_basic_types(self):
        """Test that basic JSON types are preserved."""
        assert make_json_serializable(None) is None
        assert make_json_serializable(True) is True
        assert make_json_serializable(42) == 42
        assert make_json_serializable(3.14) == 3.14
        assert make_json_serializable("hello") == "hello"

    def test_handles_bytes(self):
        """Test that bytes are converted to strings."""
        data = b"hello"
        result = make_json_serializable(data)
        assert isinstance(result, str)
        # Verify it's JSON serializable
        json.dumps(result)

    def test_handles_mixed_complex_structure(self):
        """Test complex nested structure with multiple non-serializable types."""
        data = {
            "args": [1, "test", Ellipsis, {1, 2, 3}],
            "kwargs": {
                "timeout": ...,
                "tags": {"urgent", "important"},
                "nested": {
                    "tuple": (1, 2, 3),
                    "set": {"x", "y"}
                }
            }
        }
        result = make_json_serializable(data)

        # Verify all problematic types are converted
        assert result["args"][2] == "..."
        assert isinstance(result["args"][3], list)
        assert result["kwargs"]["timeout"] == "..."
        assert isinstance(result["kwargs"]["tags"], list)
        assert isinstance(result["kwargs"]["nested"]["tuple"], list)
        assert isinstance(result["kwargs"]["nested"]["set"], list)

        # Most importantly, verify it's JSON serializable
        json_str = json.dumps(result)
        assert json_str  # Should not raise


class TestTaskServiceJsonSerialization:
    """Test that TaskService properly handles non-serializable objects."""

    def test_save_task_event_with_ellipsis(self):
        """Test saving task event with Ellipsis in args/kwargs."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.run_migrations()

        with db_manager.get_session() as session:
            task_service = TaskService(session)

            # Create task event with Ellipsis
            task_event = TaskEvent(
                task_id="test-123",
                task_name="test.task",
                event_type="task-received",
                timestamp=datetime.now(timezone.utc),
                args=[1, 2, Ellipsis],
                kwargs={"timeout": Ellipsis}
            )

            # This should NOT raise an exception
            saved_event = task_service.save_task_event(task_event)
            assert saved_event.task_id == "test-123"

            # Verify data is properly sanitized in database
            assert saved_event.args == [1, 2, "..."]
            assert saved_event.kwargs == {"timeout": "..."}

    def test_save_task_event_with_sets(self):
        """Test saving task event with sets in args/kwargs."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.run_migrations()

        with db_manager.get_session() as session:
            task_service = TaskService(session)

            # Create task event with sets
            task_event = TaskEvent(
                task_id="test-456",
                task_name="test.task",
                event_type="task-received",
                timestamp=datetime.now(timezone.utc),
                args=[{1, 2, 3}],
                kwargs={"tags": {"urgent", "important"}}
            )

            # This should NOT raise an exception
            saved_event = task_service.save_task_event(task_event)
            assert saved_event.task_id == "test-456"

            # Verify sets are converted to lists
            assert isinstance(saved_event.args[0], list)
            assert isinstance(saved_event.kwargs["tags"], list)

    def test_save_task_event_with_complex_non_serializable(self):
        """Test saving task event with complex nested non-serializable objects."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.run_migrations()

        with db_manager.get_session() as session:
            task_service = TaskService(session)

            # Create task event with mixed non-serializable objects
            task_event = TaskEvent(
                task_id="test-789",
                task_name="test.task",
                event_type="task-received",
                timestamp=datetime.now(timezone.utc),
                args=[(1, 2), Ellipsis, {4, 5, 6}],
                kwargs={
                    "timeout": ...,
                    "tags": {"a", "b"},
                    "nested": {"tuple": (7, 8), "set": {9, 10}}
                }
            )

            # This should NOT raise an exception
            saved_event = task_service.save_task_event(task_event)
            assert saved_event.task_id == "test-789"

            # Verify all data is JSON serializable
            # The database uses JSON columns, so if this succeeds, serialization worked
            json.dumps(saved_event.args)
            json.dumps(saved_event.kwargs)
