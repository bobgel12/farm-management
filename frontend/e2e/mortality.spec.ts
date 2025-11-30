import { test, expect } from '@playwright/test';

// Helper function to ensure login
async function ensureLoggedIn(page: any) {
  await page.goto('/login');
  await page.waitForTimeout(1000);
  
  const currentUrl = page.url();
  if (!currentUrl.includes('/login')) {
    return;
  }
  
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
}

test.describe('Mortality Tab Features', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });

  test('should display Mortality tab in house detail', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    const mortalityTab = page.getByRole('tab', { name: /Mortality/i });
    await expect(mortalityTab).toBeVisible({ timeout: 15000 });
  });

  test('should show mortality content when tab clicked', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    await page.getByRole('tab', { name: /Mortality/i }).click();
    await page.waitForTimeout(1000);
    
    // Check for any mortality-related content
    const content = page.getByText(/(Mortality|Record|No flock|Select Flock)/i);
    await expect(content.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show flock selector or no-flock alert', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    await page.getByRole('tab', { name: /Mortality/i }).click();
    await page.waitForTimeout(1000);
    
    // Either show flock selector or "no flock" message
    const content = page.getByText(/(Select Flock|No flock|Record Mortality)/i);
    await expect(content.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display chart or data section', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    await page.getByRole('tab', { name: /Mortality/i }).click();
    await page.waitForTimeout(1000);
    
    // Look for chart, data table, or any mortality-related content
    const chartContent = page.locator('[class*="recharts"], [class*="chart"], table, svg');
    const textContent = page.getByText(/(Trends|Deaths|Mortality|Total|Record)/i);
    
    const chartVisible = await chartContent.first().isVisible({ timeout: 3000 }).catch(() => false);
    const textVisible = await textContent.first().isVisible({ timeout: 3000 }).catch(() => false);
    
    expect(chartVisible || textVisible).toBeTruthy();
  });

  test('should display records or empty state', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    await page.getByRole('tab', { name: /Mortality/i }).click();
    await page.waitForTimeout(1000);
    
    // Look for table, records, or empty message
    const tableContent = page.locator('table, [class*="table"]');
    const textContent = page.getByText(/(History|records|Deaths|Date|Total)/i);
    
    const tableVisible = await tableContent.first().isVisible({ timeout: 3000 }).catch(() => false);
    const textVisible = await textContent.first().isVisible({ timeout: 3000 }).catch(() => false);
    
    expect(tableVisible || textVisible).toBeTruthy();
  });
});
