/**
 * Entity input composable
 * Handles tokenized input with entity support (e.g., UUIDs as single tokens)
 */

import { ref, computed, type Ref } from 'vue'
import type { ParsedFilter } from './useFilterParser'

export interface Entity {
  id: string
  type: 'filter' | 'uuid'
  display: string
  data?: ParsedFilter
}

export const useEntityInput = () => {
  const { isUUID, parseFilter } = useFilterParser()

  /**
   * Parse input string into entities and text
   */
  function parseInputToEntities(input: string): Entity[] {
    if (!input) return []

    const entities: Entity[] = []
    const words = input.split(/\s+/).filter(w => w)

    for (const word of words) {
      if (isUUID(word)) {
        entities.push({
          id: crypto.randomUUID(),
          type: 'uuid',
          display: word,
        })
      } else {
        const filter = parseFilter(word)
        if (filter) {
          entities.push({
            id: crypto.randomUUID(),
            type: 'filter',
            display: word,
            data: filter
          })
        }
      }
    }

    return entities
  }

  /**
   * Convert entities back to string
   */
  function entitiesToString(entities: Entity[]): string {
    return entities.map(e => e.display).join(' ')
  }

  /**
   * Check if cursor is at entity boundary
   */
  function isAtEntityBoundary(
    text: string,
    cursorPos: number,
    entities: Entity[]
  ): { entity: Entity | null; atStart: boolean; atEnd: boolean } {
    const textBeforeCursor = text.substring(0, cursorPos)
    const textAfterCursor = text.substring(cursorPos)

    for (const entity of entities) {
      const entityIndex = text.indexOf(entity.display)
      if (entityIndex === -1) continue

      const entityStart = entityIndex
      const entityEnd = entityIndex + entity.display.length

      if (cursorPos === entityStart) {
        return { entity, atStart: true, atEnd: false }
      }
      if (cursorPos === entityEnd) {
        return { entity, atStart: false, atEnd: true }
      }
      if (cursorPos > entityStart && cursorPos < entityEnd) {
        return { entity, atStart: false, atEnd: false }
      }
    }

    return { entity: null, atStart: false, atEnd: false }
  }

  return {
    parseInputToEntities,
    entitiesToString,
    isAtEntityBoundary
  }
}
