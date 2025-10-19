/**
 * Generate a consistent color for a tag based on its text content
 */

const TAG_COLOR_PALETTE = [
  // Green variants
  { bg: 'hsl(158, 64%, 12%)', border: 'hsl(158, 64%, 25%)', text: 'hsl(158, 64%, 75%)' },
  // Blue variants
  { bg: 'hsl(199, 89%, 12%)', border: 'hsl(199, 89%, 25%)', text: 'hsl(199, 89%, 75%)' },
  // Purple variants
  { bg: 'hsl(263, 70%, 12%)', border: 'hsl(263, 70%, 25%)', text: 'hsl(263, 70%, 75%)' },
  // Orange variants
  { bg: 'hsl(24, 95%, 12%)', border: 'hsl(24, 95%, 25%)', text: 'hsl(24, 95%, 75%)' },
  // Cyan variants
  { bg: 'hsl(180, 85%, 12%)', border: 'hsl(180, 85%, 25%)', text: 'hsl(180, 85%, 75%)' },
  // Pink variants
  { bg: 'hsl(330, 80%, 12%)', border: 'hsl(330, 80%, 25%)', text: 'hsl(330, 80%, 75%)' },
  // Teal variants
  { bg: 'hsl(170, 75%, 12%)', border: 'hsl(170, 75%, 25%)', text: 'hsl(170, 75%, 75%)' },
  // Indigo variants
  { bg: 'hsl(240, 75%, 12%)', border: 'hsl(240, 75%, 25%)', text: 'hsl(240, 75%, 75%)' },
  // Amber variants
  { bg: 'hsl(45, 85%, 12%)', border: 'hsl(45, 85%, 25%)', text: 'hsl(45, 85%, 75%)' },
  // Emerald variants
  { bg: 'hsl(150, 80%, 12%)', border: 'hsl(150, 80%, 25%)', text: 'hsl(150, 80%, 75%)' },
  // Sky variants
  { bg: 'hsl(200, 90%, 12%)', border: 'hsl(200, 90%, 25%)', text: 'hsl(200, 90%, 75%)' },
  // Violet variants
  { bg: 'hsl(250, 80%, 12%)', border: 'hsl(250, 80%, 25%)', text: 'hsl(250, 80%, 75%)' },
]

/**
 * Simple hash function to convert string to number
 */
function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  return Math.abs(hash)
}

/**
 * Get color for a tag based on its text content
 */
export function getTagColor(text: string): { bg: string; border: string; text: string } {
  const hash = hashString(text)
  const index = hash % TAG_COLOR_PALETTE.length
  return TAG_COLOR_PALETTE[index]
}
