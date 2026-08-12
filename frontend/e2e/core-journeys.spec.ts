import { expect, test, type Page } from '@playwright/test'

const dashboardData = {
  global_stats: {
    total_cases: 120,
    total_deaths: 4,
    total_countries: 1,
    active_diseases: 1,
    active_alerts: 1,
    latest_data_date: '2026-08-12',
    data_completeness: 0.95,
    median_reporting_lag_days: 1,
  },
  country_stats: [{
    country_id: 1,
    country_name: 'Zambia',
    iso_code: 'ZMB',
    disease_id: 1,
    disease_name: 'Cholera',
    total_cases: 120,
    total_deaths: 4,
    total_recovered: 0,
    latest_date: '2026-08-12',
    reporting_lag_days: 0,
    data_quality_score: 0.95,
  }],
  time_series: [{ date: '2026-08-12', value: 12 }],
  alerts_summary: { high: 1, moderate: 0, low: 0 },
  top_countries: [],
}

async function authenticated(page: Page) {
  await page.context().addCookies([{ name: 'token', value: 'e2e-session', domain: '127.0.0.1', path: '/' }])
}

test('epidemiologist can view the live global dashboard data surface', async ({ page }) => {
  await authenticated(page)
  await page.route('**/api/v1/diseases*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Cholera' }]),
  }))
  await page.route('**/api/v1/dashboard/global*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(dashboardData),
  }))

  await page.goto('/dashboard/global')
  await expect(page.getByRole('heading', { name: 'Global Dashboard' })).toBeVisible()
  await expect(page.getByText('Zambia')).toBeVisible()
  await expect(page.getByText('120', { exact: true }).first()).toBeVisible()
})

test('facility administrator can review staff and change public-map consent', async ({ page }) => {
  await authenticated(page)
  await page.route('**/api/v1/auth/me*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ id: 7, username: 'facility-admin', email: 'facility@example.com', facility_id: 1 }),
  }))
  await page.route('**/api/v1/facilities', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Lusaka Clinic', type: 'clinic', country_id: 1, public_visible: false }]),
  }))
  await page.route('**/api/v1/facilities/1/staff*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 8, username: 'clinician', email: 'clinician@example.com', full_name: 'Clinical Officer', role_id: 5, is_active: true, is_verified: true, mfa_enabled: true }]),
  }))
  await page.route('**/api/v1/facilities/1/consent*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ status: 'success', public_visible: true }),
  }))

  await page.goto('/facility')
  await expect(page.getByRole('heading', { name: 'Authorized facility workspace' })).toBeVisible()
  await expect(page.getByText('Clinical Officer')).toBeVisible()
  await page.getByRole('button', { name: 'Public map: disabled' }).click()
  await expect(page.getByRole('button', { name: 'Public map: enabled' })).toBeVisible()
})

test('privileged login redirects to the MFA challenge', async ({ page }) => {
  await page.route('**/api/auth/login', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true, mfa_required: true }),
  }))

  await page.goto('/auth/login')
  await page.locator('input').nth(0).fill('admin@example.com')
  await page.locator('input[type="password"]').fill('strong-password')
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page).toHaveURL(/\/auth\/mfa$/)
  await expect(page.getByRole('heading', { name: 'Multi-factor verification' })).toBeVisible()
})
