// Requires a frontend server at TEST_BASE_URL (default: http://127.0.0.1:3000).
import { test, expect } from '@playwright/test'

const baseURL = process.env.TEST_BASE_URL || 'http://127.0.0.1:3000'

for (const mode of ['new', 'edit']) {
  test(`${mode}: workflow and action switches update the saved payload`, async ({ page }) => {
    const actions = [
      { type: 'task.retry', params: { delay_seconds: 0 }, continue_on_failure: true },
      { type: 'slack.notify', params: { config_id: 'slack', template: 'Task failed' }, continue_on_failure: true },
    ]
    const workflow = {
      id: 'test', name: 'Switch regression', enabled: true, priority: 100, cooldown_seconds: 0,
      trigger: { type: 'task.failed' }, actions,
    }
    await page.route(`${baseURL}/api/**`, route => route.fulfill({ json: [] }))
    await page.route('**/api/workflows/metadata', route => route.fulfill({ json: {
      triggers: [{ type: 'task.failed', label: 'Task Failed', category: 'task', description: '' }],
      actions: [{ type: 'task.retry', label: 'Retry Task' }],
    } }))
    await page.route('**/api/action-configs*', route => route.fulfill({ json: [
      { id: 'slack', name: 'Test Slack', action_type: 'slack.notify' },
    ] }))
    await page.route('**/api/workflows/test', route => route.fulfill({ json: workflow }))
    await page.route('**/api/workflows', route => route.fulfill({ json: workflow }))
    const metadata = page.waitForResponse('**/api/workflows/metadata')
    await page.goto(`${baseURL}/workflows/${mode === 'new' ? 'new' : 'test/edit'}`)
    await metadata

    if (mode === 'new') {
      await page.getByPlaceholder('e.g., Alert on Critical Failures').fill(workflow.name)
      await page.getByText('Select a trigger event', { exact: true }).click()
      await page.getByRole('button', { name: 'Task Failed', exact: true }).click()
      await page.getByRole('button', { name: 'Add Action', exact: true }).click()
      await page.getByRole('button', { name: 'Retry Task', exact: true }).click()
      await page.keyboard.press('Escape')
    } else {
      for (let index = 0; index < actions.length; index++) {
        // The action settings buttons currently have no accessible names.
        await page.locator('button').filter({ has: page.locator('svg.lucide-settings-icon') }).nth(index).click()
        const dialog = page.getByRole('dialog')
        if (index === 1) await dialog.getByText('Advanced Options', { exact: true }).click()
        const toggle = dialog.getByRole('switch')
        await expect(toggle).toBeChecked()
        await toggle.click()
        await expect(toggle).not.toBeChecked()
        await dialog.getByRole('button', { name: 'Save', exact: true }).click()
      }
    }

    const enabled = page.locator('label').filter({ hasText: /^Enabled$/ }).locator('../..').getByRole('switch')
    await expect(enabled).toBeChecked()
    await enabled.click()
    await expect(enabled).not.toBeChecked()
    const saved = page.waitForRequest(request =>
      request.method() === (mode === 'new' ? 'POST' : 'PUT') && /\/api\/workflows(?:\/test)?$/.test(request.url()))
    await page.getByRole('button', { name: mode === 'new' ? 'Save' : 'Save Changes', exact: true }).click()
    const payload = (await saved).postDataJSON()
    expect(payload.enabled).toBe(false)
    if (mode === 'edit') expect(payload.actions.map(action => action.continue_on_failure)).toEqual([false, false])
  })
}
