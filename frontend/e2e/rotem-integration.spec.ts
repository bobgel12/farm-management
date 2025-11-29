import { test, expect } from '@playwright/test';

// Helper function to ensure login
async function ensureLoggedIn(page: any) {
  // First try to access a protected page
  await page.goto('/rotem');
  
  // Wait a bit for any redirects
  await page.waitForTimeout(1000);
  
  // Check if we're on login page
  const currentUrl = page.url();
  if (currentUrl.includes('/login')) {
    // Need to login
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
  }
}

test.describe('Rotem Integration Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });

  test('should display Rotem dashboard with farms', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Check for dashboard heading
    await expect(page.getByRole('heading', { name: /Rotem Integration/i })).toBeVisible({ timeout: 15000 });

    // Check for action buttons
    await expect(page.getByRole('button', { name: /Add Farm/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Refresh/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Scrape All/i })).toBeVisible();
  });

  test('should display farm cards with actions', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    await expect(page.getByRole('heading', { name: /Rotem Integration/i })).toBeVisible({ timeout: 15000 });

    // Check for View Details buttons (one per farm)
    const viewButtons = page.getByRole('button', { name: /View Detail/i });
    const count = await viewButtons.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should be able to refresh data', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    await expect(page.getByRole('heading', { name: /Rotem Integration/i })).toBeVisible({ timeout: 15000 });

    // Click refresh button
    const refreshButton = page.getByRole('button', { name: /Refresh/i }).first();
    await refreshButton.click();
    
    // Wait for refresh to complete
    await page.waitForTimeout(2000);
    
    // Page should still be visible
    await expect(page.getByRole('heading', { name: /Rotem Integration/i })).toBeVisible();
  });

  test('should display ML Insights Dashboard section', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    await expect(page.getByRole('heading', { name: /Rotem Integration/i })).toBeVisible({ timeout: 15000 });

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Check for ML Insights heading
    await expect(page.getByRole('heading', { name: /ML Insight/i })).toBeVisible();
  });

  test('should display ML tabs', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Check for tabs
    await expect(page.getByRole('tab', { name: /Anomal/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Failure/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Optimization/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Performance/i })).toBeVisible();
  });

  test('should switch ML tabs', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Click on Failures tab
    await page.getByRole('tab', { name: /Failure/i }).click();
    await page.waitForTimeout(500);

    // Click on Optimization tab
    await page.getByRole('tab', { name: /Optimization/i }).click();
    await page.waitForTimeout(500);

    // Click on Performance tab
    await page.getByRole('tab', { name: /Performance/i }).click();
    await page.waitForTimeout(500);
  });
});
