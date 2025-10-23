import type { TaskEventResponse } from '~/services/apiClient'
import type { Environment } from '~/stores/environment'

type EnvironmentMatchTarget = Pick<TaskEventResponse, 'hostname' | 'routing_key'> & {
  queue?: string | null
}

export const useEnvironmentMatcher = () => {
  const patternToRegExp = (pattern: string): RegExp => {
    const escaped = pattern
      .trim()
      .replace(/[.+^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.')
    return new RegExp(`^${escaped}$`, 'i')
  }

  const matchesAnyPattern = (value: string | null, patterns: string[] | null | undefined): boolean => {
    if (!value || !patterns?.length) {
      return false
    }

    const normalizedValue = value.trim()
    if (!normalizedValue) {
      return false
    }

    return patterns.some(pattern => patternToRegExp(pattern).test(normalizedValue))
  }

  const matchesEnvironment = (
    target: EnvironmentMatchTarget,
    environment: Environment | null
  ): boolean => {
    if (!environment) {
      return true
    }

    const hasQueuePatterns = Boolean(environment.queue_patterns?.length)
    const hasWorkerPatterns = Boolean(environment.worker_patterns?.length)

    if (!hasQueuePatterns && !hasWorkerPatterns) {
      return true
    }

    const queueValue = target.routing_key ?? target.queue ?? null
    const workerValue = target.hostname ?? null

    const queueMatches = hasQueuePatterns
      ? matchesAnyPattern(queueValue, environment.queue_patterns)
      : false

    const workerMatches = hasWorkerPatterns
      ? matchesAnyPattern(workerValue, environment.worker_patterns)
      : false

    if (hasQueuePatterns && hasWorkerPatterns) {
      return queueMatches || workerMatches
    }

    return hasQueuePatterns ? queueMatches : workerMatches
  }

  return {
    matchesEnvironment
  }
}
