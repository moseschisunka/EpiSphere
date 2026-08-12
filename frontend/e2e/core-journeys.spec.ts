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

test('country analyst can view a scoped country dashboard', async ({ page }) => {
  await authenticated(page)
  await page.route('**/api/v1/countries/1', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ id: 1, name: 'Zambia', iso_code: 'ZMB' }),
  }))
  await page.route('**/api/v1/diseases*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Cholera' }]),
  }))
  await page.route('**/api/v1/dashboard/country/1*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      latest_stats: { daily_cases: 18, cumulative_cases: 120, daily_deaths: 1, cumulative_deaths: 4, date: '2026-08-12' },
      time_series: [{ date: '2026-08-12', value: 18 }],
      moving_averages: [{ date: '2026-08-12', value: 15 }],
    }),
  }))

  await page.goto('/dashboard/country/1')
  await expect(page.getByRole('heading', { name: 'Zambia Dashboard' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Daily Cases Time Series' })).toBeVisible()
  await expect(page.getByText('18', { exact: true })).toBeVisible()
})

test('clinician can open a patient encounter workflow', async ({ page }) => {
  await authenticated(page)
  await page.route('**/api/v1/clinical/patients*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 12, mrn_display: 'MRN-0012', dob: '1990-04-01', gender: 'F' }]),
  }))
  await page.route('**/api/v1/diseases*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Cholera' }]),
  }))

  await page.goto('/clinical')
  await expect(page.getByRole('heading', { name: 'Clinical Desk' })).toBeVisible()
  await expect(page.getByText('MRN-0012')).toBeVisible()
  await page.getByRole('button', { name: 'New Visit' }).click()
  await expect(page.getByRole('heading', { name: 'New Clinical Encounter' })).toBeVisible()
})

test('pharmacist can dispense a queued prescription without exposing raw identity', async ({ page }) => {
  await authenticated(page)
  await page.route('**/api/v1/pharmacy/prescriptions*', (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{ id: 21, drug_name: 'Oral rehydration salts', quantity: 2, patient_mrn: 'Protected', clinician_name: 'Clinical Officer' }]),
    })
  })
  await page.route('**/api/v1/pharmacy/dispense', (route) => {
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ id: 21, status: 'dispensed' }) })
  })

  await page.goto('/pharmacy')
  await expect(page.getByRole('heading', { name: 'Pharmacy Desk' })).toBeVisible()
  await expect(page.getByText('Oral rehydration salts')).toBeVisible()
  await expect(page.getByText('Protected')).toBeVisible()
  await page.getByRole('button', { name: 'Dispense' }).click()
  await expect(page.getByText('No pending prescriptions')).toBeVisible()
})

test('platform administrator can access the operations hub', async ({ page }) => {
  await authenticated(page)
  await page.route('**/api/v1/auth/me*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ id: 1, username: 'platform-admin', roles: ['admin'] }),
  }))
  await page.route('**/api/v1/news*', (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{
      id: 44,
      title: 'Cholera response update',
      summary: 'Operational update for the current response.',
      content: 'Operational update',
      source: 'EpiSphere',
      is_public: true,
      published_at: '2026-08-12T00:00:00Z',
    }]),
  }))
  await page.route('**/api/v1/users*', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, username: 'platform-admin', email: 'admin@example.com', role_id: 1, is_active: true, is_verified: true }]) }))
  // Register the specific route after the broad user matcher; Playwright
  // evaluates matching handlers in reverse registration order.
  await page.route('**/api/v1/users/roles*', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, name: 'admin' }, { id: 2, name: 'clinician' }]) }))
  await page.route('**/api/v1/facilities*', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, name: 'Lusaka Clinic', country_id: 1, public_visible: false }]) }))
  await page.route('**/api/v1/interop/source-systems*', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, name: 'WHO GHO', code: 'who_gho', system_type: 'api_ingestion', is_active: true }]) }))

  await page.goto('/admin')
  await expect(page.getByRole('heading', { name: 'System Control & Operations Hub' })).toBeVisible()
  await expect(page.getByText('Cholera response update')).toBeVisible()
  await page.getByRole('button', { name: 'Access & Sources' }).click()
  await expect(page.getByRole('heading', { name: 'Access and source administration' })).toBeVisible({ timeout: 15_000 })
  await expect(page.getByText('WHO GHO')).toBeVisible()
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
