<template>
  <Sheet :open="open" @update:open="handleOpenChange">
    <SheetContent
      side="right"
      class="w-[720px] max-w-[95vw] border-l border-border bg-background-base p-0"
    >
      <div class="flex h-full flex-col">
        <SheetHeader class="border-b border-border px-6 py-5 bg-background-surface">
          <div class="flex items-start justify-between gap-3">
            <div class="space-y-1">
              <SheetTitle>Workspace Settings</SheetTitle>
              <SheetDescription>
                Tune Kanchi to match your team’s flow.
              </SheetDescription>
            </div>
            <SheetClose as-child>
              <Button variant="ghost" size="icon">
                <X class="h-4 w-4" />
                <span class="sr-only">Close settings</span>
              </Button>
            </SheetClose>
          </div>
        </SheetHeader>

        <div class="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          <section class="rounded-2xl border border-border bg-background-surface px-6 py-5 shadow-sm">
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 class="text-sm font-semibold text-text-primary">Appearance</h3>
                <p class="text-xs text-text-muted">Switch between light and dark themes.</p>
              </div>
              <ThemeToggle />
            </div>
          </section>

          <section class="rounded-2xl border border-border bg-background-surface px-6 py-5 shadow-sm">
            <div class="space-y-4">
              <div>
                <h3 class="text-sm font-semibold text-text-primary">Resources</h3>
                <p class="text-xs text-text-muted">Stay up-to-date with releases and contribute to Kanchi.</p>
              </div>
              <div class="grid gap-3 sm:grid-cols-2">
                <Button
                  as="a"
                  href="https://github.com/getkanchi/kanchi"
                  target="_blank"
                  rel="noreferrer"
                  variant="outline"
                  class="justify-start gap-3"
                >
                  <Github class="h-4 w-4" />
                  View on GitHub
                  <ArrowUpRight class="ml-auto h-3.5 w-3.5 text-text-muted" />
                </Button>
                <Button
                  as="a"
                  href="https://kanchi.io/changelog"
                  target="_blank"
                  rel="noreferrer"
                  variant="outline"
                  class="justify-start gap-3"
                >
                  <Sparkles class="h-4 w-4" />
                  Changelog
                  <ArrowUpRight class="ml-auto h-3.5 w-3.5 text-text-muted" />
                </Button>
              </div>
            </div>
          </section>

          <WorkflowSlackConfigPanel
            :active="open"
            :enable-selection="false"
          />
        </div>

        <SheetFooter class="border-t border-border px-6 py-4 bg-background-surface">
          <p class="text-xs text-text-muted">
            Need a hand? Reach out at <a href="mailto:hello@kanchi.io" class="underline hover:text-text-primary">hello@kanchi.io</a>.
          </p>
        </SheetFooter>
      </div>
    </SheetContent>
  </Sheet>
</template>

<script setup lang="ts">
import { ArrowUpRight, Github, Sparkles, X } from 'lucide-vue-next'
import { Sheet, SheetClose, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '~/components/ui/sheet'
import { Button } from '~/components/ui/button'
import ThemeToggle from '~/components/ThemeToggle.vue'
import WorkflowSlackConfigPanel from '~/components/workflows/WorkflowSlackConfigPanel.vue'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function handleOpenChange(value: boolean) {
  if (!value) {
    emit('close')
  }
}
</script>
