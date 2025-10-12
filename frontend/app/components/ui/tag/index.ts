import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as BaseTag } from "./BaseTag.vue"

export const tagVariants = cva(
  "inline-flex items-center gap-1.5 font-mono font-medium transition-all duration-200 uppercase tracking-wide",
  {
    variants: {
      variant: {
        default: "bg-background-raised text-text-secondary border border-border hover:bg-background-hover hover:border-border-highlight",
        primary: "bg-primary-bg text-primary border border-primary-border hover:bg-primary/10",
        subtle: "bg-background-surface text-text-muted border border-border-subtle hover:text-text-secondary",
        outlined: "bg-transparent text-text-secondary border border-border hover:bg-background-surface",
        solid: "bg-background-hover text-text-primary border border-transparent hover:bg-background-active",
      },
      size: {
        xs: "text-[9px] px-1.5 py-0.5 rounded gap-1",
        sm: "text-[10px] px-2 py-0.5 rounded-md gap-1.5",
        default: "text-[11px] px-2.5 py-1 rounded-md gap-1.5",
        md: "text-xs px-3 py-1.5 rounded-md gap-2",
      },
      interactive: {
        true: "cursor-pointer hover:scale-[1.02] active:scale-[0.98]",
        false: "cursor-default",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "sm",
      interactive: false,
    },
  },
)

export type TagVariants = VariantProps<typeof tagVariants>
