#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
OUTPUT_DIR="$ROOT_DIR/agent/ui"

NUXT_APP_BASE_URL="${NUXT_APP_BASE_URL:-/ui/}"
NUXT_PUBLIC_API_URL="${NUXT_PUBLIC_API_URL:-http://localhost:8765}"
NUXT_PUBLIC_WS_URL="${NUXT_PUBLIC_WS_URL:-ws://localhost:8765/ws}"

if [[ "${NUXT_APP_BASE_URL: -1}" != "/" ]]; then
  NUXT_APP_BASE_URL="${NUXT_APP_BASE_URL}/"
fi

cd "$FRONTEND_DIR"

if [[ ! -d node_modules || "${FORCE_NPM_INSTALL:-0}" == "1" ]]; then
  npm ci
fi

NUXT_APP_BASE_URL="$NUXT_APP_BASE_URL" \
NUXT_PUBLIC_API_URL="$NUXT_PUBLIC_API_URL" \
NUXT_PUBLIC_WS_URL="$NUXT_PUBLIC_WS_URL" \
npm run generate

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
cp -R .output/public/. "$OUTPUT_DIR"

echo "Built frontend copied to $OUTPUT_DIR (baseURL=${NUXT_APP_BASE_URL})"
