import { ref, computed, watch } from 'vue'

interface PaginationInfo {
  page: number
  limit: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export const useLiveTable = <TData>(
  initialData: TData[] = [],
  apiUrl?: string
) => {
  const data = ref<TData[]>(initialData)
  const isLiveMode = ref(false)
  const lastUpdated = ref<Date | null>(null)
  const pageIndex = ref(0)
  const pageSize = ref(10)
  const isLoading = ref(false)
  const pagination = ref<PaginationInfo>({
    page: 0,
    limit: 10,
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  })

  // Calculate seconds since last update
  const secondsSinceUpdate = computed(() => {
    if (!lastUpdated.value) return 0
    return Math.floor((Date.now() - lastUpdated.value.getTime()) / 1000)
  })

  // Fetch data from API
  const fetchData = async () => {
    if (!apiUrl) return
    
    isLoading.value = true
    try {
      const response = await fetch(`${apiUrl}?page=${pageIndex.value}&limit=${pageSize.value}`)
      const result = await response.json()
      
      if (result.data && result.pagination) {
        data.value = result.data
        pagination.value = result.pagination
        lastUpdated.value = new Date()
      }
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      isLoading.value = false
    }
  }

  const toggleLiveMode = () => {
    isLiveMode.value = !isLiveMode.value
    if (isLiveMode.value) {
      lastUpdated.value = new Date()
      // In live mode, go to first page to see newest data
      if (apiUrl) {
        pageIndex.value = 0
        fetchData()
      }
    } else {
      // When switching to static mode, fetch current page data
      if (apiUrl) {
        fetchData()
      }
    }
  }

  // Update data externally (e.g., from WebSocket in live mode)
  const updateData = (newData: TData[]) => {
    if (isLiveMode.value) {
      // In live mode, only update if we're on the first page (to see newest data)
      if (pageIndex.value === 0) {
        data.value = newData
        lastUpdated.value = new Date()
      }
    } else {
      // In static mode, don't update from websocket - user controls pagination
      // data.value = newData
    }
  }

  const setPageIndex = (index: number) => {
    pageIndex.value = index
    pagination.value.page = index
    // Fetch data for the new page if we have an API
    if (apiUrl) {
      fetchData()
    }
  }

  const setPageSize = (size: number) => {
    pageSize.value = size
    pagination.value.limit = size
    pageIndex.value = 0 // Reset to first page when changing page size
    pagination.value.page = 0
    // Fetch data with new page size if we have an API
    if (apiUrl) {
      fetchData()
    }
  }

  // Watch for changes in page/size and fetch data
  watch([pageIndex, pageSize], () => {
    if (apiUrl && !isLiveMode.value) {
      fetchData()
    }
  })

  // Initial data fetch if API is provided
  if (apiUrl) {
    fetchData()
  }

  return {
    data: computed(() => data.value),
    isLiveMode: computed(() => isLiveMode.value),
    lastUpdated: computed(() => lastUpdated.value),
    secondsSinceUpdate,
    pageIndex: computed(() => pageIndex.value),
    pageSize: computed(() => pageSize.value),
    pagination: computed(() => pagination.value),
    isLoading: computed(() => isLoading.value),
    toggleLiveMode,
    updateData,
    setPageIndex,
    setPageSize,
    fetchData
  }
}