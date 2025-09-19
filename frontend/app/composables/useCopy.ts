import { ref } from 'vue'

export function useCopy() {
  const copiedItems = ref(new Set<string>())

  const copyToClipboard = async (text: string, key?: string) => {
    try {
      await navigator.clipboard.writeText(text)
      
      if (key) {
        copiedItems.value.add(key)
        setTimeout(() => {
          copiedItems.value.delete(key)
        }, 2000)
      }
      
      return true
    } catch (err) {
      console.error('Failed to copy:', err)
      return false
    }
  }

  const isCopied = (key: string) => copiedItems.value.has(key)

  return {
    copyToClipboard,
    isCopied
  }
}