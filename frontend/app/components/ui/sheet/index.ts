import type { VariantProps } from "class-variance-authority"
import { cva } from "class-variance-authority"

export { default as Sheet } from "./Sheet.vue"
export { default as SheetClose } from "./SheetClose.vue"
export { default as SheetContent } from "./SheetContent.vue"
export { default as SheetDescription } from "./SheetDescription.vue"
export { default as SheetFooter } from "./SheetFooter.vue"
export { default as SheetHeader } from "./SheetHeader.vue"
export { default as SheetTitle } from "./SheetTitle.vue"
export { default as SheetTrigger } from "./SheetTrigger.vue"

export const sheetVariants = cva(
  "fixed z-50 gap-4 bg-background p-6 shadow-lg",
  {
    variants: {
      side: {
        top: "inset-x-0 top-0 border-b data-[state=closed]:animate-slide-out-to-top data-[state=open]:animate-slide-in-from-top",
        bottom:
            "inset-x-0 bottom-0 border-t data-[state=closed]:animate-slide-out-to-bottom data-[state=open]:animate-slide-in-from-bottom",
        left: "inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:animate-slide-out-to-left data-[state=open]:animate-slide-in-from-left sm:max-w-sm",
        right:
            "bottom-0 right-0 h-screen border-l data-[state=closed]:animate-slide-out-to-right data-[state=open]:animate-slide-in-from-right",
      },
    },
    defaultVariants: {
      side: "right",
    },
  },
)

export type SheetVariants = VariantProps<typeof sheetVariants>
