# Local operator-flow verification checklist

Use this for any Kanchi issue that needs end-to-end local proof.

## 1. Prepare an isolated disposable database

- Pick a fresh temp DB path like `/tmp/kanchi-<issue>-app.sqlite`
- Boot the backend once against that DB so startup migrations create the schema
- If the flow needs richer data, seed the same DB with either:
  - `python3 seed_database.py --days 7 --database-url <DATABASE_URL>`
  - an issue-specific helper under `/data/.openclaw/workspace/tmp/seed-kanchi-<issue>-*.py`

## 2. Start the backend

From `agent/`:

```bash
PYTHONPATH=../scripts/test-support \
CELERY_BROKER_URL='sqla+sqlite:////tmp/kanchi-playwright-broker.sqlite' \
DATABASE_URL='sqlite:////tmp/kanchi-<issue>-app.sqlite' \
WS_HOST='127.0.0.1' \
WS_PORT='<backend-port>' \
LOG_LEVEL='INFO' \
python3 main.py --host 127.0.0.1 --port <backend-port>
```

## 3. Run backend validation first

From `agent/`:

- Run the targeted unit suite for the issue
- Hit the new or changed API directly once with `curl` to confirm the seeded scenario is visible before opening the browser

## 4. Build and serve the frontend

From `frontend/`:

```bash
NUXT_PUBLIC_API_URL='http://127.0.0.1:<backend-port>' \
NUXT_PUBLIC_WS_URL='ws://127.0.0.1:<backend-port>/ws' \
npm run build

HOST='127.0.0.1' \
PORT='<frontend-port>' \
NITRO_HOST='127.0.0.1' \
NITRO_PORT='<frontend-port>' \
NUXT_PUBLIC_API_URL='http://127.0.0.1:<backend-port>' \
NUXT_PUBLIC_WS_URL='ws://127.0.0.1:<backend-port>/ws' \
node .output/server/index.mjs
```

Important: use the built app, never `nuxt dev`, for proof runs.

## 5. Capture browser proof

- Use the standalone Playwright runtime under `/data/.openclaw/workspace/tmp/pw`
- Record the exact operator flow that proves the issue behavior
- Save:
  - one video artifact (`.mp4` preferred, `.webm` acceptable if conversion is blocked)
  - one or more screenshots for the key end state

## 6. Close the loop

- Write the exact test/build/proof commands and artifact paths back into `PLAN.md`
- If verification revealed a bug, patch it, rebuild, and re-record proof
- Commit, push, and open/update the PR when repo action is warranted
- Send Bernhard the proof artifact once the flow is genuinely verified

## Proven flow summary to record in PLAN.md

For each issue, note:

- what operator action was demonstrated
- which API response proved the backend slice
- which UI screen confirmed the end state
- where the final video/screenshot artifacts live
