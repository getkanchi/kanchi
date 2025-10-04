import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Button } from "./Button.vue"

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded text-sm font-normal transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/30 disabled:pointer-events-none disabled:opacity-40 cursor-default [&_svg]:pointer-events-none [&_svg]:size-3.5 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-background-raised text-text-primary border border-border/60 hover:bg-background-surface hover:border-border/40 active:bg-background-base",
        destructive:
          "bg-status-error/10 text-status-error border border-status-error/20 hover:bg-status-error/15 hover:border-status-error/30 active:bg-status-error/20",
        outline:
          "border border-border/40 bg-transparent hover:bg-background-hover-subtle hover:border-border/60 text-text-secondary hover:text-text-primary active:bg-background-active",
        secondary:
          "bg-background-surface/60 text-text-secondary hover:bg-background-hover hover:text-text-primary active:bg-background-active",
        ghost: "hover:bg-background-hover-subtle text-text-secondary hover:text-text-primary active:bg-background-active",
        link: "text-text-secondary hover:text-text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-7 px-3 py-1",
        xs: "h-6 px-2 text-xs",
        sm: "h-6.5 px-2.5 text-xs",
        lg: "h-8 px-4",
        icon: "h-7 w-7",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
