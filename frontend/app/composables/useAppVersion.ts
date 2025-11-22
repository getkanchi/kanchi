import { computed } from 'vue'
import { useRuntimeConfig } from '#imports'

export function useAppVersion() {
  const config = useRuntimeConfig()
  const rawVersion = (config.public.kanchiVersion as string | undefined)?.trim() || 'dev'

  const displayVersion = computed(() => rawVersion || 'dev')
  const changelogUrl = computed(() => {
    if (displayVersion.value.toLowerCase() === 'dev') {
      return 'https://kanchi.io/changelog'
    }
    const anchor = displayVersion.value.replace(/^v/, '')
    return `https://kanchi.io/changelog#${anchor}`
  })

  return {
    displayVersion,
    changelogUrl,
  }
}
