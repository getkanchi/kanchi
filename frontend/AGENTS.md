# Agents.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanchi is a Celery task monitoring frontend built with Nuxt.js (Vue 3) that connects to a FastAPI backend via REST API and WebSocket for real-time monitoring of Celery workers and tasks.

## Development Commands

### Quick Start (from project root)
```bash
# Start both backend and frontend
make dev

# View unified logs
make logs
```

### Environment Setup
```bash
npm install
```

### Development
```bash
npm run dev          # Start development server (localhost:3000)
```

### Build & Deployment
```bash
npm run build        # Build for production
npm run generate     # Generate static site
npm run preview      # Preview production build
```

### API Type Generation
```bash
# Generate TypeScript types from backend OpenAPI schema (use the script to avoid formatting issues)
npm run generate:api:local  # For local development (localhost:8765)
npm run generate:api         # For default backend URL

# Or use the script directly
./generate-api-types.sh http://localhost:8765

# ⚠️ IMPORTANT: Always use the axios template to avoid formatting issues
# The default modular template has a bug that generates malformed TypeScript
# The scripts above handle this automatically
```

## Architecture Overview

### Frontend Stack
- **Framework**: Nuxt 4 (Vue 3) with TypeScript
- **Styling**: TailwindCSS with Radix UI components (reka-ui)
- **State Management**: Pinia stores for centralized state
- **Tables**: TanStack Vue Table for data display
- **Real-time**: WebSocket connection with auto-reconnect
- **HTTP Client**: Auto-generated from OpenAPI spec

### Key Architectural Patterns

#### State Management Layer
All application state is managed through Pinia stores:
- `stores/tasks.ts` - Task events, pagination, filtering, stats
- `stores/workers.ts` - Worker status and management  
- `stores/websocket.ts` - WebSocket connection and real-time updates

#### API Service Layer
- `services/apiClient.ts` - Centralized API service using auto-generated types
- `app/src/types/` - Auto-generated TypeScript types from backend OpenAPI (DO NOT EDIT)

#### Component Architecture
- **`components/ui/`** - ONLY shadcn/ui components (installed via npx shadcn-vue)
- **`components/common/`** - Custom reusable components (Pill, Tag, Select, TimeInput, IconButton, TimePicker)
- **`components/domain/`** - Domain-specific feature components
  - `tasks/` - Task-related components (TaskCard, TaskDetailSheet, etc.)
  - `workers/` - Worker-related components
  - `orphans/` - Orphan task components
- **`components/layout/`** - Layout components (navbar, etc.)
- Business components consume Pinia stores directly
- All data is type-safe using generated API types

### Real-time Data Flow
1. WebSocket connection managed by `websocket` store
2. Live mode: Events stream directly from WebSocket to UI
3. Static mode: Paginated API calls with manual refresh
4. Stores automatically update components when data changes

## Environment Configuration

### Runtime Config (nuxt.config.ts)
```typescript
runtimeConfig: {
  public: {
    wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8765/ws',
    apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8765'
  }
}
```

### Environment Variables
```bash
NUXT_PUBLIC_API_URL=http://localhost:8765    # Backend API URL
NUXT_PUBLIC_WS_URL=ws://localhost:8765/ws    # WebSocket URL
```

## Code Patterns

### Using Stores in Components
```typescript
// Always use stores for data access
const tasksStore = useTasksStore()
const workersStore = useWorkersStore()
const wsStore = useWebSocketStore()

// Reactive data
const { recentEvents, isLoading } = tasksStore

// Actions
await tasksStore.fetchRecentEvents()
tasksStore.setPage(2)
wsStore.setMode('live')
```

### Logging
```typescript
// Use the logger service for unified logging (development mode only)
import { useLogger } from '~/services/logger'

const logger = useLogger()

logger.debug('Debug message', { context: 'data' })
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message', { error: 'details' })
logger.critical('Critical message')
```

Logs are sent to the backend at `/api/logs/frontend` and written to the unified log file at `agent/kanchi.log`. **This feature only works in development mode** - logs are still written to console but not sent to backend in production.

### Type Safety
- All API calls use auto-generated types from backend OpenAPI
- Import types from `~/services/apiClient` for consistency
- Never manually edit files in `app/src/types/` - they are auto-generated

### Error Handling
- Stores handle errors internally and expose error state
- Components should catch store action errors for user feedback
- Use try/catch around store actions that need user notification

## Component Organization

### Directory Structure
```
components/
├── ui/                    # ONLY shadcn/ui components (installed via CLI)
│   ├── button/
│   ├── input/
│   ├── badge/
│   └── ... (all shadcn components)
│
├── common/                # Custom reusable components
│   ├── Pill.vue          # Status pill component
│   ├── Tag.vue           # Tag component with variants
│   ├── TimePicker.vue    # Time picker component
│   ├── IconButton.vue    # Icon-only button component
│   ├── Select.vue        # Styled select dropdown
│   ├── TimeInput.vue     # Styled time input
│   └── index.ts          # Barrel exports for easy imports
│
├── domain/                # Domain-specific feature components
│   ├── tasks/            # Task-related components
│   ├── workers/          # Worker-related components
│   └── orphans/          # Orphan task components
│
└── layout/                # Layout components
    └── (navbar, etc.)
```

### Using Common Components

Import from the index for convenience:
```typescript
import { Pill, Tag, IconButton, Select, TimeInput } from '~/components/common'
```

Or import directly:
```typescript
import Pill from '~/components/common/Pill.vue'
```

### Component Guidelines

1. **Never** add custom components to `components/ui/` - that folder is reserved for shadcn components
2. Place reusable components in `components/common/`
3. Place feature-specific components in `components/domain/{feature}/`
4. Always use existing components instead of inline styles
5. For components with `export` statements (like cva variants), use two `<script>` blocks:
   ```vue
   <script lang="ts">
   import { cva } from "class-variance-authority"
   export const myVariants = cva(...)
   </script>

   <script setup lang="ts">
   // Component logic here
   </script>
   ```

## Important File Locations

### Core Application Files
- `app/app.vue` - Main application component
- `app/layouts/default.vue` - Default layout with navigation

### Configuration
- `nuxt.config.ts` - Nuxt configuration and runtime config
- `package.json` - Dependencies and scripts
- `tailwind.config.js` - TailwindCSS configuration

### Generated Files (DO NOT EDIT)
- `app/src/types/` - Auto-generated from backend OpenAPI schema

## Backend Integration

### API Type Generation
When backend API changes, regenerate types:
```bash
npx swagger-typescript-api generate -p http://localhost:8765/openapi.json -o app/src/types -n api.ts --modular
```

### WebSocket Protocol
- Connection automatically established on app load
- Supports live/static modes for different data consumption patterns
- Auto-reconnect with exponential backoff on connection loss

## Development Workflow

1. **Backend First**: Ensure backend is running on port 8765
2. **Types**: Regenerate types if backend API changed
3. **Development**: Use `npm run dev` for hot-reload development
4. **State**: Always use Pinia stores for data management
5. **Components**: Follow existing patterns in `components/` directory

## Common Tasks

### Adding New API Endpoint
1. Update backend OpenAPI spec
2. Regenerate frontend types
3. Add method to appropriate store
4. Use in components via store

### Adding New UI Component
1. **For shadcn components**: Use `npx shadcn-vue@latest add <component-name>` - components go to `components/ui/`
2. **For custom reusable components**: Create in `components/common/` and add to `index.ts` for barrel exports
3. **For feature-specific components**: Create in `components/domain/{feature}/`
4. Follow existing patterns for consistency (Button, Input, Badge variants from shadcn; custom Pill, Tag, Select from common)
5. Use TailwindCSS classes following existing patterns
6. Consume data via Pinia stores

### Debugging WebSocket Issues
- Check `websocket` store connection state
- Monitor browser network tab for WebSocket frames
- Verify backend WebSocket server is running
- Check runtime config for correct WebSocket URL
