import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Button } from "./Button.vue"

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 disabled:pointer-events-none disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-background-raised text-text-primary border border-border shadow-sm hover:bg-background-surface hover:border-border/80",
        destructive:
          "bg-status-error text-white shadow-sm hover:bg-status-error/90",
        outline:
          "border border-border bg-transparent hover:bg-background-surface text-text-primary",
        secondary:
          "bg-background-surface text-text-secondary border border-border hover:bg-background-raised",
        ghost: "hover:bg-background-surface/50 text-text-primary",
        link: "text-text-primary underline-offset-4 hover:underline hover:text-text-secondary",
      },
      size: {
        default: "h-9 px-4 py-2",
        xs: "h-7 rounded px-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
