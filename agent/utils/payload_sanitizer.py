"""Utilities for keeping task payloads JSON-safe."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple

PLACEHOLDER_KEY = "__kanchi_placeholder__"
PLACEHOLDER_TRUNCATED = "celery_payload_truncated"
PLACEHOLDER_MESSAGE = (
    "Value truncated before reaching Kanchi. "
    "Increase celery.amqp.argsrepr_maxsize or celery.amqp.kwargsrepr_maxsize in your producer "
    "to capture the full payload."
)


def _placeholder() -> Dict[str, str]:
    return {
        PLACEHOLDER_KEY: PLACEHOLDER_TRUNCATED,
        "message": PLACEHOLDER_MESSAGE,
    }


def sanitize_payload(value: Any) -> Tuple[Any, bool]:
    """Return a JSON-serializable copy of *value* and flag when we had to truncate."""

    truncated = False

    def _sanitize(item: Any) -> Any:
        nonlocal truncated

        if item is Ellipsis:
            truncated = True
            return _placeholder()

        if isinstance(item, list):
            return [_sanitize(elem) for elem in item]

        if isinstance(item, tuple):
            truncated = True
            return [_sanitize(elem) for elem in item]

        if isinstance(item, set):
            truncated = True
            return [_sanitize(elem) for elem in item]

        if isinstance(item, dict):
            sanitized_dict = {}
            for key, val in item.items():
                sanitized_key = str(key)
                sanitized_dict[sanitized_key] = _sanitize(val)
            return sanitized_dict

        if isinstance(item, (str, int, float, bool)) or item is None:
            return item

        if isinstance(item, (datetime, date)):
            truncated = True
            return item.isoformat()

        if isinstance(item, Decimal):
            return float(item)

        if isinstance(item, bytes):
            truncated = True
            return item.decode("utf-8", errors="replace")

        try:
            json.dumps(item)
            return item
        except TypeError:
            truncated = True
            return f"<{type(item).__name__} not JSON serializable>"

    return _sanitize(value), truncated


def is_placeholder_node(value: Any) -> bool:
    """Return True if *value* is one of our placeholder markers."""
    return isinstance(value, dict) and value.get(PLACEHOLDER_KEY) == PLACEHOLDER_TRUNCATED


def contains_placeholder(value: Any) -> bool:
    """Check if a nested payload already contains our placeholder marker."""
    if isinstance(value, list):
        return any(contains_placeholder(elem) for elem in value)

    if isinstance(value, dict):
        if is_placeholder_node(value):
            return True
        return any(contains_placeholder(elem) for elem in value.values())

    return False


def find_placeholder_paths(value: Any, current_path: str = "$") -> List[str]:
    """
    Return a list of JSON-style paths that contain placeholder nodes.

    Args:
        value: Payload to inspect
        current_path: Current traversal path (used internally)
    """
    paths: List[str] = []

    if is_placeholder_node(value):
        paths.append(current_path)
        return paths

    if isinstance(value, list):
        for idx, item in enumerate(value):
            child_path = f"{current_path}[{idx}]"
            paths.extend(find_placeholder_paths(item, child_path))
    elif isinstance(value, dict):
        for key, item in value.items():
            safe_key = str(key)
            child_path = f"{current_path}.{safe_key}"
            paths.extend(find_placeholder_paths(item, child_path))

    return paths


__all__ = [
    "PLACEHOLDER_KEY",
    "PLACEHOLDER_TRUNCATED",
    "PLACEHOLDER_MESSAGE",
    "sanitize_payload",
    "contains_placeholder",
    "is_placeholder_node",
    "find_placeholder_paths",
]
