export const PAYLOAD_PLACEHOLDER_KEY = '__kanchi_placeholder__'
export const PAYLOAD_PLACEHOLDER_VALUE = 'celery_payload_truncated'
export const DEFAULT_PLACEHOLDER_MESSAGE = 'Value truncated before reaching Kanchi.'

export function containsTruncatedValue(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some(containsTruncatedValue)
  }

  if (value && typeof value === 'object') {
    const record = value as Record<string, unknown>
    if (record[PAYLOAD_PLACEHOLDER_KEY] === PAYLOAD_PLACEHOLDER_VALUE) {
      return true
    }
    return Object.values(record).some(containsTruncatedValue)
  }

  return false
}

export function isPayloadPlaceholder(value: unknown): value is Record<string, unknown> {
  return Boolean(
    value &&
    typeof value === 'object' &&
    (value as Record<string, unknown>)[PAYLOAD_PLACEHOLDER_KEY] === PAYLOAD_PLACEHOLDER_VALUE
  )
}

export function getPlaceholderMessage(value: unknown): string {
  if (!isPayloadPlaceholder(value)) {
    return DEFAULT_PLACEHOLDER_MESSAGE
  }
  const record = value as Record<string, unknown>
  return typeof record.message === 'string' ? record.message : DEFAULT_PLACEHOLDER_MESSAGE
}

export function collectTruncationMessages(value: unknown): string[] {
  const messages = new Set<string>()

  function walk(node: unknown) {
    if (Array.isArray(node)) {
      node.forEach(walk)
      return
    }

    if (node && typeof node === 'object') {
      const record = node as Record<string, unknown>
      if (isPayloadPlaceholder(record)) {
        messages.add(getPlaceholderMessage(record))
        return
      }

      Object.values(record).forEach(walk)
    }
  }

  walk(value)

  return Array.from(messages)
}
