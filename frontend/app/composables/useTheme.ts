import { ref, watch, onMounted } from 'vue'

export type Theme = 'dark' | 'light' | 'system'

const THEME_KEY = 'kanchi-theme'

// Shared state across all consumers
const theme = ref<Theme>('dark')
const resolvedTheme = ref<'dark' | 'light'>('dark')
let initialized = false

const applyTheme = (newTheme: 'dark' | 'light') => {
  if (newTheme === 'light') {
    document.documentElement.classList.add('light')
    document.documentElement.classList.remove('dark')
  } else {
    document.documentElement.classList.add('dark')
    document.documentElement.classList.remove('light')
  }
  resolvedTheme.value = newTheme
}

const resolveTheme = (themeValue: Theme): 'dark' | 'light' => {
  if (themeValue === 'system') {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  }
  return themeValue
}

const setTheme = (newTheme: Theme) => {
  theme.value = newTheme
  localStorage.setItem(THEME_KEY, newTheme)
  const resolved = resolveTheme(newTheme)
  applyTheme(resolved)
}

const toggleTheme = () => {
  // Cycle through: dark -> light -> system
  const nextTheme: Theme =
    theme.value === 'dark' ? 'light' :
    theme.value === 'light' ? 'dark' :
    'dark'
  setTheme(nextTheme)
}

const initializeTheme = () => {
  if (initialized) return
  initialized = true

  const stored = localStorage.getItem(THEME_KEY) as Theme | null
  theme.value = stored || 'dark'

  const resolved = resolveTheme(theme.value)
  applyTheme(resolved)

  const mediaQuery = window.matchMedia('(prefers-color-scheme: light)')
  mediaQuery.addEventListener('change', (e) => {
    if (theme.value === 'system') {
      applyTheme(e.matches ? 'light' : 'dark')
    }
  })

  watch(theme, (newTheme) => {
    const resolvedValue = resolveTheme(newTheme)
    applyTheme(resolvedValue)
  })
}

export const useTheme = () => {
  onMounted(() => {
    initializeTheme()
  })

  return {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme
  }
}
