#!/bin/bash

# Generate API types from backend OpenAPI spec
# This script ensures consistent and correct type generation

BACKEND_URL="${1:-http://localhost:8765}"
OUTPUT_DIR="app/src/types"
OUTPUT_FILE="api.ts"

echo "📦 Generating TypeScript types from $BACKEND_URL/openapi.json..."

# Use axios template which generates cleaner code without formatting issues
npx swagger-typescript-api generate \
  -p "$BACKEND_URL/openapi.json" \
  -o "$OUTPUT_DIR" \
  -n "$OUTPUT_FILE" \
  --axios

if [ $? -eq 0 ]; then
  echo "✅ Types generated successfully in $OUTPUT_DIR/$OUTPUT_FILE"
  echo "📝 Note: Using axios template for clean code generation"
else
  echo "❌ Failed to generate types. Make sure the backend is running at $BACKEND_URL"
  exit 1
fi