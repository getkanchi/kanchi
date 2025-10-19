/**
 * Filter parser composable
 * Handles parsing and serialization of filter syntax: field:operator:value(s)
 */

export interface ParsedFilter {
  field: string
  operator: string
  values: string[]
  raw: string
}

export type FilterField = 'state' | 'worker' | 'task' | 'queue' | 'id'
export type FilterOperator = 'is' | 'not' | 'in' | 'not_in' | 'contains' | 'starts'

export interface FilterFieldConfig {
  value: FilterField
  label: string
  description: string
  operators: FilterOperator[]
  suggestValues?: () => string[]
}

export const useFilterParser = () => {
  const { getAllStatuses } = useTaskStatus()

  // Available filter fields with their configurations
  const filterFields: FilterFieldConfig[] = [
    {
      value: 'state',
      label: 'State',
      description: 'Filter by task state',
      operators: ['is', 'not', 'in', 'not_in'],
      suggestValues: () => getAllStatuses()
    },
    {
      value: 'worker',
      label: 'Worker',
      description: 'Filter by worker hostname',
      operators: ['is', 'not', 'contains', 'starts', 'in', 'not_in']
    },
    {
      value: 'task',
      label: 'Task',
      description: 'Filter by task name',
      operators: ['is', 'not', 'contains', 'starts', 'in', 'not_in']
    },
    {
      value: 'queue',
      label: 'Queue',
      description: 'Filter by queue/routing key',
      operators: ['is', 'not', 'contains', 'starts', 'in', 'not_in']
    },
    {
      value: 'id',
      label: 'Task ID',
      description: 'Filter by task UUID',
      operators: ['is', 'not', 'contains', 'starts', 'in', 'not_in']
    }
  ]

  // Operator labels and descriptions
  const operatorLabels: Record<FilterOperator, { label: string; description: string }> = {
    is: { label: 'is', description: 'Exact match' },
    not: { label: 'is not', description: 'Not equal to' },
    in: { label: 'is one of', description: 'Matches any of the values' },
    not_in: { label: 'is not one of', description: 'Does not match any of the values' },
    contains: { label: 'contains', description: 'Contains substring' },
    starts: { label: 'starts with', description: 'Starts with' }
  }

  /**
   * Parse a single filter string into a structured object
   * Format: field:operator:value or field:value (defaults to 'is' operator)
   */
  function parseFilter(filterStr: string): ParsedFilter | null {
    if (!filterStr || !filterStr.trim()) return null

    const segments = filterStr.split(':')
    if (segments.length < 2) return null

    const field = segments[0].trim().toLowerCase()

    if (!filterFields.find(f => f.value === field)) return null

    let operator: string
    let valueStr: string

    if (segments.length === 2) {
      // Format: field:value (default to 'is' operator)
      operator = 'is'
      valueStr = segments[1].trim()
    } else {
      // Format: field:operator:value
      operator = segments[1].trim().toLowerCase()
      valueStr = segments.slice(2).join(':').trim()
    }

    // Parse multiple values for in/not_in operators
    const values = (operator === 'in' || operator === 'not_in')
      ? valueStr.split(',').map(v => v.trim()).filter(v => v)
      : [valueStr]

    return {
      field,
      operator,
      values,
      raw: filterStr
    }
  }

  /**
   * Serialize a parsed filter back to string format
   */
  function serializeFilter(filter: ParsedFilter): string {
    const { field, operator, values } = filter

    // For multi-value operators, join with commas
    const valueStr = (operator === 'in' || operator === 'not_in')
      ? values.join(',')
      : values[0] || ''

    // Omit operator if it's the default 'is'
    if (operator === 'is') {
      return `${field}:${valueStr}`
    }

    return `${field}:${operator}:${valueStr}`
  }

  /**
   * Parse multiple filters from an array of filter objects
   * Used for converting from the UI filter format to API format
   */
  function filtersToQueryString(filters: ParsedFilter[]): string {
    return filters.map(f => serializeFilter(f)).join(';')
  }

  /**
   * Parse query string to array of filters
   */
  function queryStringToFilters(queryStr: string): ParsedFilter[] {
    if (!queryStr) return []

    return queryStr
      .split(';')
      .map(f => parseFilter(f))
      .filter((f): f is ParsedFilter => f !== null)
  }

  /**
   * Validate a filter
   */
  function isValidFilter(filter: ParsedFilter): boolean {
    const fieldConfig = filterFields.find(f => f.value === filter.field)
    if (!fieldConfig) return false

    if (!fieldConfig.operators.includes(filter.operator as FilterOperator)) {
      return false
    }

    if (filter.values.length === 0) return false

    return true
  }

  /**
   * Get available operators for a field
   */
  function getOperatorsForField(field: FilterField): FilterOperator[] {
    const fieldConfig = filterFields.find(f => f.value === field)
    return fieldConfig?.operators || []
  }

  /**
   * Get suggestions for a field
   */
  function getSuggestionsForField(field: FilterField): string[] {
    const fieldConfig = filterFields.find(f => f.value === field)
    return fieldConfig?.suggestValues?.() || []
  }

  /**
   * Format operator for display
   */
  function formatOperator(operator: string): string {
    return operatorLabels[operator as FilterOperator]?.label || operator
  }

  /**
   * Check if a string is a UUID
   */
  function isUUID(str: string): boolean {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    return uuidRegex.test(str)
  }

  return {
    filterFields,
    operatorLabels,
    parseFilter,
    serializeFilter,
    filtersToQueryString,
    queryStringToFilters,
    isValidFilter,
    getOperatorsForField,
    getSuggestionsForField,
    formatOperator,
    isUUID
  }
}
