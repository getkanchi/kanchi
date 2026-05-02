<script setup lang="ts">
const route = useRoute()

await navigateTo(
  {
    path: '/settings/audit',
    query: route.query,
    hash: route.hash,
  },
  { replace: true },
)
</script>
