"""Shared utilities for service layer."""

import logging
from typing import List, Optional, Callable, Any
from sqlalchemy.orm import Query
from sqlalchemy import or_

from database import TaskEventDB

logger = logging.getLogger(__name__)


class EnvironmentFilter:
    """Applies environment-based filtering to database queries."""

    @staticmethod
    def apply(query: Query, active_env, model=TaskEventDB) -> Query:
        """
        Apply environment filtering using wildcard patterns.

        Args:
            query: SQLAlchemy query to filter
            active_env: Environment configuration with queue_patterns and worker_patterns

        Returns:
            Filtered query
        """
        if not active_env:
            return query

        conditions = []

        if active_env.queue_patterns:
            queue_conditions = []
            for pattern in active_env.queue_patterns:
                sql_pattern = pattern.replace('*', '%').replace('?', '_')
                queue_conditions.append(getattr(model, 'queue').like(sql_pattern))
            if queue_conditions:
                conditions.append(or_(*queue_conditions))

        if active_env.worker_patterns:
            worker_conditions = []
            for pattern in active_env.worker_patterns:
                sql_pattern = pattern.replace('*', '%').replace('?', '_')
                worker_conditions.append(getattr(model, 'hostname').like(sql_pattern))
            if worker_conditions:
                conditions.append(or_(*worker_conditions))

        if conditions:
            query = query.filter(or_(*conditions))

        return query


class GenericFilter:
    """Generic filter application with operator support."""

    VALID_OPERATORS = ['is', 'not', 'contains', 'starts', 'in', 'not_in']

    @staticmethod
    def apply(
        query: Query,
        column,
        operator: str,
        values: List[str],
        value_mapper: Optional[Callable[[str], Any]] = None
    ) -> Query:
        """
        Apply a filter to a query with operator support.

        Args:
            query: SQLAlchemy query to filter
            column: Database column to filter on
            operator: Filter operator (is, not, contains, starts, in, not_in)
            values: Values to filter by
            value_mapper: Optional function to transform values before filtering

        Returns:
            Filtered query
        """
        if not values:
            return query

        if value_mapper:
            values = [value_mapper(v) for v in values if value_mapper(v)]
            if not values:
                return query

        if operator in ['is', '']:
            return query.filter(column == values[0])
        elif operator == 'not':
            return query.filter(column != values[0])
        elif operator == 'contains':
            return query.filter(column.ilike(f"%{values[0]}%"))
        elif operator == 'starts':
            return query.filter(column.ilike(f"{values[0]}%"))
        elif operator == 'in':
            return query.filter(column.in_(values))
        elif operator == 'not_in':
            return query.filter(~column.in_(values))

        logger.warning(f"Unknown operator '{operator}', returning unmodified query")
        return query


def parse_filter_string(filters_str: str) -> List[dict]:
    """
    Parse filter string into structured filter objects.

    Format: field:operator:value(s)
    Multiple filters separated by semicolons

    Example: "state:is:success;worker:contains:celery"

    Args:
        filters_str: Filter string to parse

    Returns:
        List of filter dictionaries with 'field', 'operator', and 'values' keys
    """
    if not filters_str:
        return []

    parsed = []
    filter_parts = filters_str.split(';')

    for part in filter_parts:
        part = part.strip()
        if not part:
            continue

        segments = part.split(':', 2)
        if len(segments) < 2:
            continue

        field = segments[0].strip().lower()

        if len(segments) == 2:
            operator = 'is'
            value_str = segments[1].strip()
        else:
            operator = segments[1].strip().lower()
            value_str = segments[2].strip()

        if operator in ['in', 'not_in']:
            values = [v.strip() for v in value_str.split(',') if v.strip()]
        else:
            values = [value_str]

        parsed.append({
            'field': field,
            'operator': operator,
            'values': values
        })

    return parsed
