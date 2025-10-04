import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Pill } from "./Pill.vue"

export const pillVariants = cva(
  "inline-flex items-center justify-center font-mono transition-colors",
  {
    variants: {
      variant: {
        default: "bg-background-surface text-text-secondary border border-border",
        shortcut: "bg-background-surface text-text-secondary border border-border hover:bg-background-raised hover:border-border/80 transition-all duration-200 hover:scale-[1.02]",
        accent: "bg-background-surface text-text-primary border border-border shadow-sm",
        subtle: "bg-background-surface/60 text-text-muted border border-border",
      },
      size: {
        sm: "text-[12px] px-2 py-0.5 rounded-md max-w-16",
        default: "text-xs px-2 py-1 rounded-md",
        lg: "text-sm px-3 py-1.5 rounded-md",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type PillVariants = VariantProps<typeof pillVariants>
