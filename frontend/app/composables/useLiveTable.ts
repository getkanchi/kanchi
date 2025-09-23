import { ref, computed, watch } from 'vue'

interface PaginationInfo {
  page: number
  limit: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

interface Filter {
  key: string
  value: string
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
  const sorting = ref<{ id: string; desc: boolean }[]>([])
  const searchQuery = ref('')
  const filters = ref<Filter[]>([])
  const pagination = ref<PaginationInfo>({
    page: 0,
    limit: 10,
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  })

  const secondsSinceUpdate = computed(() => {
    if (!lastUpdated.value) return 0
    return Math.floor((Date.now() - lastUpdated.value.getTime()) / 1000)
  })

  const fetchData = async () => {
    if (!apiUrl) return
    
    isLoading.value = true
    try {
        const params = new URLSearchParams({
        page: pageIndex.value.toString(),
        limit: pageSize.value.toString()
      })
      
      if (sorting.value.length > 0) {
        const sort = sorting.value[0]
        params.append('sort_by', sort.id)
        params.append('sort_order', sort.desc ? 'desc' : 'asc')
      }
      
      if (searchQuery.value) {
        params.append('search', searchQuery.value)
      }
      
      filters.value.forEach(filter => {
        params.append(`filter_${filter.key}`, filter.value)
      })
      
      const response = await fetch(`${apiUrl}?${params.toString()}`)
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
      if (apiUrl) {
        pageIndex.value = 0
        fetchData()
      }
    } else {
      if (apiUrl) {
        fetchData()
      }
    }
  }

  const updateData = (newData: TData[]) => {
    if (isLiveMode.value) {
      if (pageIndex.value === 0) {
        data.value = newData
        lastUpdated.value = new Date()
      }
    } else {
    }
  }

  const setPageIndex = (index: number) => {
    pageIndex.value = index
    pagination.value.page = index
    if (apiUrl) {
      fetchData()
    }
  }

  const setPageSize = (size: number) => {
    pageSize.value = size
    pagination.value.limit = size
    pageIndex.value = 0
    pagination.value.page = 0
    if (apiUrl) {
      fetchData()
    }
  }

  const setSorting = (newSorting: { id: string; desc: boolean }[]) => {
    sorting.value = newSorting
    pageIndex.value = 0
    pagination.value.page = 0
    if (apiUrl) {
      fetchData()
    }
  }

  const setSearchQuery = (query: string) => {
    searchQuery.value = query
    pageIndex.value = 0
    pagination.value.page = 0
    if (apiUrl) {
      fetchData()
    }
  }

  const setFilters = (newFilters: Filter[]) => {
    filters.value = newFilters
    pageIndex.value = 0
    pagination.value.page = 0
    if (apiUrl) {
      fetchData()
    }
  }

  watch([pageIndex, pageSize], () => {
    if (apiUrl && !isLiveMode.value) {
      fetchData()
    }
  })

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
    sorting: computed(() => sorting.value),
    searchQuery: computed(() => searchQuery.value),
    filters: computed(() => filters.value),
    toggleLiveMode,
    updateData,
    setPageIndex,
    setPageSize,
    setSorting,
    setSearchQuery,
    setFilters,
    fetchData
  }
}