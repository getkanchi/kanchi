// From frontend/: npm install --no-save --package-lock=false @playwright/test@1.56.1
// npx playwright install chromium; npm run dev -- --host 127.0.0.1
// In another terminal: npx playwright test tests/e2e/workflow-cancel-edits.spec.ts --workers=1
import { test, expect } from '@playwright/test'

const baseURL = process.env.TEST_BASE_URL || 'http://127.0.0.1:3000'

for (const action of [
  { type: 'task.retry', params: { delay_seconds: 10 }, continue_on_failure: true },
  { type: 'slack.notify', params: { config_id: 'slack', channel: '#original', template: 'Task failed' }, continue_on_failure: true },
]) {
  test(`Cancel discards ${action.type} parameters; Save keeps them`, async ({ page }) => {
    const workflow = {
      id: 'test', name: 'Cancel regression', enabled: true, priority: 100, cooldown_seconds: 0,
      trigger: { type: 'task.failed' }, actions: [action],
    }
    await page.route(`${baseURL}/api/**`, route => route.fulfill({ json: [] }))
    await page.route('**/api/workflows/metadata', route => route.fulfill({ json: { triggers: [], actions: [] } }))
    await page.route('**/api/action-configs*', route => route.fulfill({ json: [
      { id: 'slack', name: 'Test Slack', action_type: 'slack.notify' },
    ] }))
    await page.route('**/api/workflows/test', route => route.fulfill({ json: workflow }))
    await page.goto(`${baseURL}/workflows/test/edit`)

    // The action settings button currently has no accessible name.
    const configure = page.locator('button').filter({ has: page.locator('svg.lucide-settings-icon') })
    const dialog = page.getByRole('dialog')
    const field = action.type === 'task.retry'
      ? dialog.getByRole('spinbutton') : dialog.getByPlaceholder('#channel-name')
    const original = action.type === 'task.retry' ? '10' : '#original'
    const changed = action.type === 'task.retry' ? '50' : '#changed'

    await configure.click()
    await field.fill(changed)
    await dialog.getByRole('button', { name: 'Cancel', exact: true }).click()
    await configure.click()
    await expect(field).toHaveValue(original)
    await field.fill(changed)
    await dialog.getByRole('button', { name: 'Save', exact: true }).click()
    await configure.click()
    await expect(field).toHaveValue(changed)
    await dialog.getByRole('button', { name: 'Cancel', exact: true }).click()

    const saved = page.waitForRequest(request => request.method() === 'PUT' && request.url().endsWith('/api/workflows/test'))
    await page.getByRole('button', { name: 'Save Changes', exact: true }).click()
    expect((await saved).postDataJSON().actions[0].params).toEqual({
      ...action.params, ...(action.type === 'task.retry' ? { delay_seconds: 50 } : { channel: '#changed' }),
    })
  })
}
