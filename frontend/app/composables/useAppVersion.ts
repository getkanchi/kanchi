import { computed } from 'vue'
import { usePublicEnv } from '~/composables/usePublicEnv'

export function useAppVersion() {
  const { kanchiVersion } = usePublicEnv()
  const rawVersion = kanchiVersion?.trim() || 'dev'

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
