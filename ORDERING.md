# Table Ordering Plan

## Objective
Configure the data table to display tasks with the most recent "started_at" timestamp at the top by default.

## Implementation Steps

### 1. Update TanStack Table Configuration
- Add `getSortedRowModel` to the table configuration in `data-table.vue`
- Set default sorting state to sort by "started_at" column in descending order

### 2. Modify Column Definition
- Update the "started_at" column definition in `app.vue` to include:
  - `enableSorting: true`
  - Default sort direction as descending

### 3. Data Preprocessing (Alternative Approach)
- Sort the data array before passing to the table component
- Ensure new WebSocket updates maintain the sort order when added to the task list

### 4. Handle Live Updates
- When new tasks are added via WebSocket, insert them in the correct position based on timestamp
- Ensure the sorting persists when live mode updates occur

## Technical Details

### Required TanStack Table Features
- Import `getSortedRowModel` from `@tanstack/vue-table`
- Add to table configuration alongside `getCoreRowModel`
- Set initial sort state in table options

### Column Configuration
```typescript
{
  accessorKey: 'started_at',
  header: 'Started At',
  enableSorting: true,
  sortDescFirst: true // Most recent first
}
```

### Initial Sort State
```typescript
const table = useVueTable({
  // ... existing config
  getSortedRowModel: getSortedRowModel(),
  initialState: {
    sorting: [
      {
        id: 'started_at',
        desc: true
      }
    ]
  }
})
```

## Files to Modify
1. `frontend/app/components/data-table.vue` - Add sorting configuration
2. `frontend/app/app.vue` - Update column definition for started_at
3. Optionally: Update WebSocket task insertion logic to maintain order