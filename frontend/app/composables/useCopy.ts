import { ref } from 'vue'

export function useCopy() {
  const copiedItems = ref(new Set<string>())

  const copyToClipboard = async (text: string, key?: string) => {
    try {
      // Try modern Clipboard API first (requires HTTPS or localhost)
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
      } else {
        // Fallback for non-secure contexts (HTTP)
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()

        const successful = document.execCommand('copy')
        document.body.removeChild(textArea)

        if (!successful) {
          throw new Error('execCommand copy failed')
        }
      }

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