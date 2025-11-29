import { test, expect } from '@playwright/test';

// Helper function to ensure login
async function ensureLoggedIn(page: any) {
  await page.goto('/rotem');
  await page.waitForTimeout(1000);
  
  const currentUrl = page.url();
  if (currentUrl.includes('/login')) {
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
  }
}

test.describe('ML Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });

  test('should display ML Insights section', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Check for ML Insights heading
    await expect(page.getByRole('heading', { name: /ML Insight/i })).toBeVisible({ timeout: 10000 });
  });

  test('should display prediction tabs', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Check for all tabs
    await expect(page.getByRole('tab', { name: /Anomal/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Failure/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Optimization/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /Performance/i })).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Click on each tab
    await page.getByRole('tab', { name: /Failure/i }).click();
    await page.waitForTimeout(300);

    await page.getByRole('tab', { name: /Optimization/i }).click();
    await page.waitForTimeout(300);

    await page.getByRole('tab', { name: /Performance/i }).click();
    await page.waitForTimeout(300);

    await page.getByRole('tab', { name: /Anomal/i }).click();
    await page.waitForTimeout(300);
  });

  test('should display Run Analysis button', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Check for Run Analysis button
    await expect(page.getByRole('button', { name: /Run Analy/i })).toBeVisible();
  });

  test('should be able to run ML analysis', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Click Run Analysis button
    const runButton = page.getByRole('button', { name: /Run Analy/i });
    await runButton.click();
    
    // Wait for analysis to start
    await page.waitForTimeout(2000);
    
    // Page should still be visible (no errors)
    await expect(page.getByRole('heading', { name: /ML Insight/i })).toBeVisible();
  });

  test('should display Refresh button', async ({ page }) => {
    await page.goto('/rotem');
    await page.waitForTimeout(1000);

    // Scroll to ML section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // Should have Refresh button in ML section
    const refreshButtons = page.getByRole('button', { name: /Refresh/i });
    const count = await refreshButtons.count();
    expect(count).toBeGreaterThan(0);
  });
});
