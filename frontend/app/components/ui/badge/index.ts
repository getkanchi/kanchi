import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Badge } from "./Badge.vue"

export const badgeVariants = cva(
  "inline-flex hover:cursor-default items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
        outline: "text-foreground border border-border bg-background-base hover:bg-background-surface",
        success: "border-status-success-border bg-status-success-bg text-status-success hover:bg-status-success-hover",
        failed: "border-status-error-border bg-status-error-bg text-status-error hover:bg-status-error-hover",
        pending: "border-status-warning-border bg-status-warning-bg text-status-warning hover:bg-status-warning-hover",
        running: "border-status-info-border bg-status-info-bg text-status-info hover:bg-status-info-hover",
        retry: "border-status-retry-border bg-status-retry-bg text-status-retry hover:bg-status-retry-hover",
        revoked: "border-status-neutral-border bg-status-neutral-bg text-status-neutral hover:bg-status-neutral-hover",
        received: "border-status-special-border bg-status-special-bg text-status-special hover:bg-status-special-hover",
        orphaned: "border-status-error-border bg-status-error-bg text-status-error hover:bg-status-error-hover",
        // Worker status variants
        online: "border-status-success-border bg-status-success-bg text-status-success hover:bg-status-success-hover",
        offline: "border-status-error-border bg-status-error-bg text-status-error hover:bg-status-error-hover",
        heartbeat: "border-status-info-border bg-status-info-bg text-status-info hover:bg-status-info-hover",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
)

export type BadgeVariants = VariantProps<typeof badgeVariants>
