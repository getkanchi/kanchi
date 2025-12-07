<template>
  <div class="mx-auto max-w-5xl space-y-10 py-6 lg:py-8">
    <section class="rounded-3xl border border-border-subtle bg-background-surface px-8 py-10 shadow-sm">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-text-secondary">Workspace</p>
      <h1 class="mt-3 text-3xl font-semibold text-text-primary">Workspace settings</h1>
      <p class="mt-4 max-w-2xl text-sm text-text-secondary">
        Configure how Kanchi behaves for everyone in this environment. Update appearance preferences,
        review resources, and manage workflow integrations.
      </p>
    </section>

    <div class="space-y-6">
      <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 class="text-base font-semibold text-text-primary">Appearance</h2>
            <p class="mt-1 text-sm text-text-secondary">
              Toggle between light and dark themes. Theme applies instantly for your browser.
            </p>
          </div>
          <ThemeToggle />
        </div>
      </section>

      <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
        <div class="space-y-4">
          <div>
            <h2 class="text-base font-semibold text-text-primary">Resources</h2>
            <p class="mt-1 text-sm text-text-secondary">Stay aligned with releases and contribute to Kanchi.</p>
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

      <section class="rounded-2xl border border-border-subtle bg-background-surface p-6 shadow-sm">
        <div class="mb-6">
          <h2 class="text-base font-semibold text-text-primary">Slack webhooks</h2>
          <p class="mt-1 text-sm text-text-secondary">
            Configure reusable Slack webhook destinations for workflow notifications and alerts.
          </p>
        </div>
        <WorkflowSlackConfigPanel :active="true" :enable-selection="false" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowUpRight, Github, Sparkles } from 'lucide-vue-next'
import ThemeToggle from '~/components/ThemeToggle.vue'
import WorkflowSlackConfigPanel from '~/components/workflows/WorkflowSlackConfigPanel.vue'
import { Button } from '~/components/ui/button'

definePageMeta({
  middleware: [],
})
</script>
