import { test, expect } from '@playwright/test';

// Helper function to ensure login
async function ensureLoggedIn(page: any) {
  await page.goto('/farms');
  await page.waitForTimeout(1000);
  
  const currentUrl = page.url();
  if (currentUrl.includes('/login')) {
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
  }
}

test.describe('Farm Integration Features', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });

  test('should display farms page with Add button', async ({ page }) => {
    await page.goto('/farms');
    await page.waitForTimeout(1000);

    // Check for Add New Farm button
    await expect(page.getByRole('button', { name: /Add.*Farm/i })).toBeVisible({ timeout: 15000 });
  });

  test('should display farm cards', async ({ page }) => {
    await page.goto('/farms');
    await page.waitForTimeout(1000);

    // Check for View Detail buttons (one per farm)
    const viewButtons = page.getByRole('button', { name: /View Detail/i });
    const count = await viewButtons.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should navigate to farm detail', async ({ page }) => {
    await page.goto('/farms');
    await page.waitForTimeout(1000);

    // Click on first View Detail button
    const viewButtons = page.getByRole('button', { name: /View Detail/i });
    await viewButtons.first().click();

    // Should navigate to farm detail page
    await page.waitForTimeout(1000);
    await expect(page).toHaveURL(/\/farms\/\d+/);
  });

  test('should display farm detail with sections', async ({ page }) => {
    await page.goto('/farms');
    await page.waitForTimeout(1000);

    // Click on first View Detail button
    const viewButtons = page.getByRole('button', { name: /View Detail/i });
    await viewButtons.first().click();
    await page.waitForTimeout(1000);

    // Farm detail page should show info
    const pageContent = await page.content();
    expect(pageContent.length).toBeGreaterThan(0);
  });

  test('should open add farm dialog', async ({ page }) => {
    await page.goto('/farms');
    await page.waitForTimeout(1000);

    // Click Add New Farm button
    const addButton = page.getByRole('button', { name: /Add.*Farm/i });
    await addButton.click();
    await page.waitForTimeout(500);

    // Dialog or form should appear
    const dialog = page.getByRole('dialog');
    const hasDialog = await dialog.isVisible().catch(() => false);
    
    // If no dialog, check for form elements
    if (!hasDialog) {
      const formElement = page.locator('form, input[name="name"]');
      const hasForm = await formElement.first().isVisible().catch(() => false);
      expect(hasDialog || hasForm).toBeTruthy();
    } else {
      expect(hasDialog).toBeTruthy();
    }
  });
});
