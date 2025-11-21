import json
from enum import Enum

from services.workflow_service import WorkflowService


class _DummyEnum(str, Enum):
    FOO = "foo"


class _PlainObject:
    def __init__(self):
        self.value = "bar"


def test_json_safe_handles_enums_and_plain_objects():
    svc = WorkflowService(None)  # Session is unused in _json_safe

    payload = {
        "enum": _DummyEnum.FOO,
        "plain": _PlainObject(),
        "nested": {"things": [_DummyEnum.FOO]},
    }

    sanitized = svc._json_safe(payload)

    # Enum should become its value
    assert sanitized["enum"] == "foo"
    # Plain object should be reduced to its __dict__ contents
    assert sanitized["plain"] == {"value": "bar"}
    # Nested enums should also be converted
    assert sanitized["nested"]["things"] == ["foo"]

    # And the whole structure must be JSON serializable
    json.dumps(sanitized)
