// Must stay within TASK_ISSUE_LOOKBACK_MAX_HOURS in agent/models.py.
export const TASK_ISSUE_LOOKBACK_OPTIONS = [12, 24, 48, 72, 168, 336, 720] as const
export const DEFAULT_TASK_ISSUE_LOOKBACK_HOURS = 24

export function formatLookbackLabel(hours: number): string {
  if (hours % 24 === 0 && hours >= 24) {
    return `${hours / 24}d`
  }
  return `${hours}h`
}

export function normalizeLookback(hours?: number | null): number {
  const candidate = Number.isFinite(hours) ? Math.round(Number(hours)) : NaN
  if (!Number.isFinite(candidate)) {
    return DEFAULT_TASK_ISSUE_LOOKBACK_HOURS
  }
  return TASK_ISSUE_LOOKBACK_OPTIONS.reduce<number>((closest, option) => {
    return Math.abs(option - candidate) < Math.abs(closest - candidate) ? option : closest
  }, TASK_ISSUE_LOOKBACK_OPTIONS[0])
}
