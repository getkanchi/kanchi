import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Alert } from "./Alert.vue"

// We don't actually use cva here since we handle variants in the component,
// but this provides the type structure for consistency with other UI components
export const alertVariants = cva("", {
  variants: {
    variant: {
      success: "",
      warning: "",
      error: "",
      info: "",
    },
    size: {
      sm: "",
      default: "",
      lg: "",
    },
  },
  defaultVariants: {
    variant: "info",
    size: "default",
  },
})

export type AlertVariants = VariantProps<typeof alertVariants>