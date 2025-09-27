import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Pill } from "./Pill.vue"

export const pillVariants = cva(
  "inline-flex items-center justify-center font-mono transition-colors",
  {
    variants: {
      variant: {
        default: "bg-background-primary text-text-secondary border border-card-border",
        shortcut: "bg-background-primary text-text-secondary border border-card-border hover:bg-background-secondary hover:border-card-border/80 transition-all duration-200 hover:scale-[1.02]",
        accent: "bg-card-base text-text-primary border border-card-border shadow-sm",
        subtle: "bg-background-primary/60 text-text-tertiary border border-card-border/50",
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
