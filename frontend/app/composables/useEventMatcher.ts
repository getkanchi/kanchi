/**
 * Event matcher composable for client-side filtering of live events
 * Replicates backend filter logic to ensure consistency between server and client filtering
 */

import type { TaskEventResponse } from '~/services/apiClient'
import type { ParsedFilter } from '~/composables/useFilterParser'

export const useEventMatcher = () => {
  const { eventTypeToStatus } = useTaskStatus()

  /**
   * Main entry point - validates event against all active filters
   * Returns true if event matches ALL criteria (filters are AND-ed together)
   */
  function matchesFilters(
    event: TaskEventResponse,
    filters: ParsedFilter[],
    searchQuery?: string,
    timeRange?: { start: string | null; end: string | null }
  ): boolean {
    // Check search first (most common filter)
    if (searchQuery && !matchesSearch(event, searchQuery)) {
      return false
    }

    // Check time range
    if (timeRange && !matchesTimeRange(event, timeRange)) {
      return false
    }

    // Check each structured filter
    for (const filter of filters) {
      if (!matchesFilter(event, filter)) {
        return false
      }
    }

    return true
  }

  /**
   * Dispatcher - routes to specific field matcher based on filter type
   */
  function matchesFilter(event: TaskEventResponse, filter: ParsedFilter): boolean {
    switch (filter.field) {
      case 'state':
        return matchesStateFilter(event, filter.operator, filter.values)
      case 'worker':
        return matchesWorkerFilter(event, filter.operator, filter.values)
      case 'task':
        return matchesTaskFilter(event, filter.operator, filter.values)
      case 'queue':
        return matchesQueueFilter(event, filter.operator, filter.values)
      case 'id':
        return matchesIdFilter(event, filter.operator, filter.values)
      default:
        // Unknown filters don't exclude events
        return true
    }
  }

  /**
   * Match state filter (maps event_type to user-friendly status)
   * Mirrors backend logic: agent/services/task_service.py:607-635
   */
  function matchesStateFilter(
    event: TaskEventResponse,
    operator: string,
    values: string[]
  ): boolean {
    // Map event_type to user-friendly status (handles orphaned special case)
    const status = event.is_orphan ? 'ORPHANED' : eventTypeToStatus(event.event_type)
    const upperValues = values.map(v => v.toUpperCase())

    switch (operator) {
      case 'is':
        return status === upperValues[0]
      case 'not':
        return status !== upperValues[0]
      case 'in':
        return upperValues.includes(status)
      case 'not_in':
        return !upperValues.includes(status)
      default:
        return true
    }
  }

  /**
   * Generic string field matcher with operator support
   * Mirrors backend ilike() behavior with case-insensitive matching
   * Used by worker, task, queue, and id filters
   */
  function matchesStringField(
    value: string | undefined,
    operator: string,
    filterValues: string[]
  ): boolean {
    if (!value) return false

    const lowerValue = value.toLowerCase()
    const lowerFilters = filterValues.map(v => v.toLowerCase())

    switch (operator) {
      case 'is':
      case '': // Default operator
        return lowerValue === lowerFilters[0]
      case 'not':
        return lowerValue !== lowerFilters[0]
      case 'contains':
        return lowerValue.includes(lowerFilters[0])
      case 'starts':
        return lowerValue.startsWith(lowerFilters[0])
      case 'in':
        return lowerFilters.includes(lowerValue)
      case 'not_in':
        return !lowerFilters.includes(lowerValue)
      default:
        return true
    }
  }

  /**
   * Match worker filter (hostname field)
   * Mirrors backend logic: agent/services/task_service.py:637-655
   */
  function matchesWorkerFilter(
    event: TaskEventResponse,
    operator: string,
    values: string[]
  ): boolean {
    return matchesStringField(event.hostname, operator, values)
  }

  /**
   * Match task filter (task_name field)
   * Mirrors backend logic: agent/services/task_service.py:657-675
   */
  function matchesTaskFilter(
    event: TaskEventResponse,
    operator: string,
    values: string[]
  ): boolean {
    return matchesStringField(event.task_name, operator, values)
  }

  /**
   * Match queue filter (routing_key field)
   * Mirrors backend logic: agent/services/task_service.py:677-695
   */
  function matchesQueueFilter(
    event: TaskEventResponse,
    operator: string,
    values: string[]
  ): boolean {
    return matchesStringField(event.routing_key, operator, values)
  }

  /**
   * Match ID filter (task_id field)
   * Mirrors backend logic: agent/services/task_service.py:697-715
   */
  function matchesIdFilter(
    event: TaskEventResponse,
    operator: string,
    values: string[]
  ): boolean {
    return matchesStringField(event.task_id, operator, values)
  }

  /**
   * Search matcher - searches across multiple fields
   * Mirrors backend logic: agent/services/task_service.py:243-255
   * Searches: task_name, task_id, hostname, event_type, args, kwargs
   */
  function matchesSearch(event: TaskEventResponse, query: string): boolean {
    if (!query) return true

    const lowerQuery = query.toLowerCase()

    // Search across all searchable fields (same as backend)
    const searchableFields = [
      event.task_name,
      event.task_id,
      event.hostname,
      event.event_type,
      // Search in serialized args/kwargs (same as backend casting to text)
      event.args ? JSON.stringify(event.args) : '',
      event.kwargs ? JSON.stringify(event.kwargs) : ''
    ]

    return searchableFields.some(field =>
      field?.toLowerCase().includes(lowerQuery)
    )
  }

  /**
   * Time range matcher
   * Mirrors backend logic: agent/services/task_service.py:204-228
   */
  function matchesTimeRange(
    event: TaskEventResponse,
    timeRange: { start: string | null; end: string | null }
  ): boolean {
    if (!event.timestamp) return true

    const eventTime = new Date(event.timestamp).getTime()

    // Check start time boundary
    if (timeRange.start) {
      const startTime = new Date(timeRange.start).getTime()
      if (eventTime < startTime) return false
    }

    // Check end time boundary
    if (timeRange.end) {
      const endTime = new Date(timeRange.end).getTime()
      if (eventTime > endTime) return false
    }

    return true
  }

  return {
    matchesFilters,
    matchesFilter,
    matchesSearch,
    matchesTimeRange
  }
}
