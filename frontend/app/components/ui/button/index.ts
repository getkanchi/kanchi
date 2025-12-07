import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Button } from "./Button.vue"

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded border text-sm font-normal transition-colors duration-150 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-40 cursor-pointer [&_svg]:pointer-events-none [&_svg]:size-3.5 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-background-raised text-text-primary border-border-subtle hover:bg-background-surface active:bg-background-base",
        primary: "bg-primary text-white border-primary-border hover:bg-primary-hover active:bg-primary-hover font-medium",
        destructive:
          "bg-status-error/10 text-status-error border-status-error-border hover:bg-status-error/15 active:bg-status-error/20",
        outline:
          "bg-transparent border-border rounded-md hover:bg-background-hover text-text-primary active:bg-background-active",
        secondary:
          "bg-background-surface/60 text-text-secondary border-border-subtle hover:bg-background-hover hover:text-text-primary active:bg-background-active",
        ghost: "border-transparent hover:bg-background-hover-subtle text-text-secondary hover:text-text-primary active:bg-background-active",
        link: "border-transparent text-text-secondary hover:text-text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-8 px-4",
        xs: "h-7 px-3 text-xs",
        sm: "h-7.5 px-3.5 py-1 text-xs",
        md: "h-7 px-3 py-1",
        lg: "h-9 px-5",
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
