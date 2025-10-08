/**
 * Unified logging service for frontend
 * Sends logs to backend for unified logging (only in development mode)
 */

type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical'

interface LogContext {
  [key: string]: any
}

class Logger {
  private apiUrl: string
  private isDevelopment: boolean

  constructor(apiUrl: string, isDevelopment: boolean) {
    this.apiUrl = apiUrl
    this.isDevelopment = isDevelopment
  }

  private async sendLog(level: LogLevel, message: string, context?: LogContext) {
    // Only send to backend in development mode
    if (!this.isDevelopment) {
      return
    }

    try {
      await fetch(`${this.apiUrl}/api/logs/frontend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          level,
          message,
          timestamp: new Date().toISOString(),
          context,
        }),
      })
    } catch (error) {
      // Fallback to console if backend logging fails
      console.error('Failed to send log to backend:', error)
      console.log(`[${level.toUpperCase()}]`, message, context)
    }
  }

  debug(message: string, context?: LogContext) {
    console.debug(`[DEBUG]`, message, context)
    this.sendLog('debug', message, context)
  }

  info(message: string, context?: LogContext) {
    console.info(`[INFO]`, message, context)
    this.sendLog('info', message, context)
  }

  warning(message: string, context?: LogContext) {
    console.warn(`[WARNING]`, message, context)
    this.sendLog('warning', message, context)
  }

  warn(message: string, context?: LogContext) {
    this.warning(message, context)
  }

  error(message: string, context?: LogContext) {
    console.error(`[ERROR]`, message, context)
    this.sendLog('error', message, context)
  }

  critical(message: string, context?: LogContext) {
    console.error(`[CRITICAL]`, message, context)
    this.sendLog('critical', message, context)
  }
}

// Create singleton instance
let logger: Logger | null = null

export function useLogger(): Logger {
  if (!logger) {
    const config = useRuntimeConfig()
    // Check if we're in development mode
    const isDevelopment = process.dev || import.meta.env.DEV || false
    logger = new Logger(config.public.apiUrl as string, isDevelopment)
  }
  return logger
}
