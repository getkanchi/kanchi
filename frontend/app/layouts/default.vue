<template>
  <div v-if="isLoginRoute" class="min-h-screen bg-background-base text-text-primary">
    <slot />
  </div>

  <div v-else class="min-h-screen bg-background-base text-text-primary lg:flex">
    <div class="hidden lg:block lg:h-screen lg:sticky lg:top-0">
      <AppSidebar />
    </div>

    <div class="flex min-h-screen min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-40 border-b border-border-subtle bg-background-surface/95 px-4 py-3 backdrop-blur-sm lg:hidden">
        <div class="flex items-center justify-between gap-3">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.28em] text-text-secondary">Kanchi</p>
            <p class="text-sm font-semibold text-text-primary">Control center</p>
          </div>

          <Sheet>
            <SheetTrigger as-child>
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-xl border border-border-subtle bg-background-base p-2 text-text-primary"
              >
                <Menu class="h-5 w-5" />
              </button>
            </SheetTrigger>
            <SheetContent side="left" class="w-[300px] border-r border-border-subtle bg-background-surface p-0">
              <AppSidebar />
            </SheetContent>
          </Sheet>
        </div>
      </header>

      <main class="w-full max-w-screen-2xl flex-1 px-4 py-6 sm:px-6 lg:px-8 xl:px-10">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from '#imports'
import { Menu } from 'lucide-vue-next'
import AppSidebar from '~/components/AppSidebar.vue'
import { Sheet, SheetContent, SheetTrigger } from '~/components/ui/sheet'
import { useEnvironmentStore } from '~/stores/environment'

const route = useRoute()
const environmentStore = useEnvironmentStore()
const isLoginRoute = computed(() => route.path === '/login')

onMounted(async () => {
  await environmentStore.initialize()
})
</script>
