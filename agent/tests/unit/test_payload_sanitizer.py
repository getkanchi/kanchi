from datetime import datetime, timezone

import json

from models import TaskEvent
from utils.payload_sanitizer import (
    PLACEHOLDER_KEY,
    PLACEHOLDER_TRUNCATED,
    sanitize_payload,
    find_placeholder_paths,
)


def test_sanitize_payload_replaces_ellipsis_with_placeholder():
    payload = ["foo", Ellipsis, {"nested": Ellipsis}]

    sanitized, truncated = sanitize_payload(payload)

    assert truncated is True
    assert isinstance(sanitized, list)
    assert sanitized[1][PLACEHOLDER_KEY] == PLACEHOLDER_TRUNCATED
    assert sanitized[2]["nested"][PLACEHOLDER_KEY] == PLACEHOLDER_TRUNCATED
    # Ensure the sanitized payload is JSON serializable
    json.dumps(sanitized)


def test_task_event_handles_ellipsis_in_args():
    event = TaskEvent(
        task_id="123",
        task_name="demo",
        event_type="task-sent",
        timestamp=datetime.now(timezone.utc),
        args=[Ellipsis],
        kwargs={"data": Ellipsis},
    )

    placeholder = event.args[0]
    assert isinstance(placeholder, dict)
    assert placeholder[PLACEHOLDER_KEY] == PLACEHOLDER_TRUNCATED
    assert event.kwargs["data"][PLACEHOLDER_KEY] == PLACEHOLDER_TRUNCATED


def test_find_placeholder_paths_reports_precise_locations():
    payload = {
        "root_list": [
            {"foo": "bar"},
            {PLACEHOLDER_KEY: PLACEHOLDER_TRUNCATED},
            {"inner": [{PLACEHOLDER_KEY: PLACEHOLDER_TRUNCATED}]},
        ],
        "regular": "value",
    }

    paths = find_placeholder_paths(payload)

    assert "$.root_list[1]" in paths
    assert "$.root_list[2].inner[0]" in paths
    assert len(paths) == 2
