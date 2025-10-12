/**
 * URL Query Sync Composable
 * Syncs filters, search, sorting, pagination, and environment to URL query params
 * Allows sharing links with current view state
 */

import { watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { ParsedFilter } from './useFilterParser'
import type { TimeRange } from '~/components/TimeRangeFilter.vue'

export interface UrlQueryState {
  search?: string | null
  filters?: string | null
  sortBy?: string | null
  sortOrder?: 'asc' | 'desc' | null
  page?: number
  pageSize?: number
  startTime?: string | null
  endTime?: string | null
  environment?: string | null
}

export const useUrlQuerySync = () => {
  const router = useRouter()
  const route = useRoute()
  const { filtersToQueryString, queryStringToFilters } = useFilterParser()

  /**
   * Parse query params from URL
   */
  function parseQueryParams(): UrlQueryState {
    const query = route.query
    return {
      search: query.search as string | undefined,
      filters: query.filters as string | undefined,
      sortBy: query.sortBy as string | undefined,
      sortOrder: (query.sortOrder as 'asc' | 'desc') || undefined,
      page: query.page ? parseInt(query.page as string, 10) : undefined,
      pageSize: query.pageSize ? parseInt(query.pageSize as string, 10) : undefined,
      startTime: query.startTime as string | undefined,
      endTime: query.endTime as string | undefined,
      environment: query.environment as string | undefined
    }
  }

  /**
   * Update URL query params without navigation
   */
  async function updateQueryParams(state: UrlQueryState, replace = true) {
    const query: Record<string, string> = {}

    // Only add non-empty values to query
    if (state.search) query.search = state.search
    if (state.filters) query.filters = state.filters
    if (state.sortBy) query.sortBy = state.sortBy
    if (state.sortOrder) query.sortOrder = state.sortOrder
    if (state.page !== undefined && state.page > 0) query.page = state.page.toString()
    if (state.pageSize) query.pageSize = state.pageSize.toString()
    if (state.startTime) query.startTime = state.startTime
    if (state.endTime) query.endTime = state.endTime
    if (state.environment) query.environment = state.environment

    // Update URL without reloading
    if (replace) {
      await router.replace({ query })
    } else {
      await router.push({ query })
    }
  }

  /**
   * Clear all query params
   */
  async function clearQueryParams() {
    await router.replace({ query: {} })
  }

  /**
   * Sync store state to URL
   */
  function syncToUrl(getState: () => UrlQueryState) {
    // Watch for state changes and update URL
    watch(
      getState,
      async (newState) => {
        await updateQueryParams(newState, true)
      },
      { deep: true }
    )
  }

  /**
   * Initialize state from URL on mount
   */
  function initializeFromUrl(applyState: (state: UrlQueryState) => void) {
    onMounted(() => {
      const state = parseQueryParams()

      // Only apply if we have any params
      if (Object.keys(state).some(key => state[key as keyof UrlQueryState] !== undefined)) {
        applyState(state)
      }
    })
  }

  /**
   * Convert ParsedFilter[] to query string
   */
  function filtersToQuery(filters: ParsedFilter[]): string | null {
    if (!filters || filters.length === 0) return null
    return filtersToQueryString(filters)
  }

  /**
   * Convert query string to ParsedFilter[]
   */
  function queryToFilters(query: string | null): ParsedFilter[] {
    if (!query) return []
    return queryStringToFilters(query)
  }

  /**
   * Get shareable URL with current state
   */
  function getShareableUrl(state?: UrlQueryState): string {
    const origin = window.location.origin
    const path = route.path

    if (state) {
      const queryStr = Object.entries(state)
        .filter(([_, value]) => value !== null && value !== undefined)
        .map(([key, value]) => `${key}=${encodeURIComponent(String(value))}`)
        .join('&')

      return queryStr ? `${origin}${path}?${queryStr}` : `${origin}${path}`
    }

    return `${origin}${route.fullPath}`
  }

  return {
    parseQueryParams,
    updateQueryParams,
    clearQueryParams,
    syncToUrl,
    initializeFromUrl,
    filtersToQuery,
    queryToFilters,
    getShareableUrl
  }
}
