// From frontend/: npm install --no-save --package-lock=false @playwright/test@1.56.1
// npx playwright install chromium; npm run dev -- --host 127.0.0.1
// In another terminal: npx playwright test tests/e2e/workflow-action-dialog.spec.ts --workers=1
import { test, expect } from '@playwright/test'

const baseURL = process.env.TEST_BASE_URL || 'http://127.0.0.1:3000'

test('adding an action opens its configuration, including after an existing action', async ({ page }) => {
  await page.route(`${baseURL}/api/**`, route => route.fulfill({ json: [] }))
  await page.route('**/api/workflows/metadata', route => route.fulfill({ json: {
    triggers: [], actions: [
      { type: 'task.retry', label: 'Retry Task' },
      { type: 'slack.notify', label: 'Slack Notification' },
    ],
  } }))
  const metadata = page.waitForResponse('**/api/workflows/metadata')
  await page.goto(`${baseURL}/workflows/new`)
  await metadata

  await page.getByRole('button', { name: 'Add Action', exact: true }).click()
  await page.getByRole('button', { name: 'Retry Task', exact: true }).click()
  const retry = page.getByRole('dialog', { name: 'Configure Task Retry' })
  await expect(retry).toBeVisible()
  await retry.getByRole('spinbutton').fill('30')
  await retry.getByRole('button', { name: 'Save', exact: true }).click()
  await expect(page.getByText('Delay: 30s', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: 'Add Action', exact: true }).click()
  await page.getByRole('button', { name: 'Slack Notification', exact: true }).click()
  const slack = page.getByRole('dialog', { name: 'Configure Slack Notification' })
  await expect(slack).toBeVisible()
  await slack.getByRole('button', { name: 'Cancel', exact: true }).click()
  await expect(slack).not.toBeVisible()
  await expect(page.getByText('Delay: 30s', { exact: true })).toBeVisible()
})
