import { test, expect } from '@playwright/test';

// Helper function to ensure login
async function ensureLoggedIn(page: any) {
  await page.goto('/login');
  await page.waitForTimeout(1000);
  
  // Check if already logged in
  const currentUrl = page.url();
  if (!currentUrl.includes('/login')) {
    return; // Already logged in
  }
  
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
}

test.describe('Issue Tracking', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });

  test('should display Issues tab in house detail', async ({ page }) => {
    // Navigate directly to house detail page
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Check for Issues tab
    const issuesTab = page.getByRole('tab', { name: /Issues/i });
    await expect(issuesTab).toBeVisible({ timeout: 15000 });
  });

  test('should show issues content when tab clicked', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click Issues tab
    const issuesTab = page.getByRole('tab', { name: /Issues/i });
    await issuesTab.click();
    await page.waitForTimeout(1000);
    
    // Check for issues-related content
    const issuesContent = page.getByText(/(Issue Tracking|Issues|No issues)/i);
    await expect(issuesContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('should have Report Issue button in Issues tab', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click Issues tab
    const issuesTab = page.getByRole('tab', { name: /Issues/i });
    await issuesTab.click();
    await page.waitForTimeout(1000);
    
    // Check for Report Issue button
    const reportButton = page.getByText('Report Issue').first();
    await expect(reportButton).toBeVisible({ timeout: 5000 });
  });

  test('should open issue report dialog from button', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click Issues tab
    await page.getByRole('tab', { name: /Issues/i }).click();
    await page.waitForTimeout(1000);
    
    // Click Report Issue text button
    await page.getByText('Report Issue').first().click();
    await page.waitForTimeout(1000);
    
    // Check for dialog
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });
  });

  test('should show form fields in report dialog', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click Issues tab and open report dialog
    await page.getByRole('tab', { name: /Issues/i }).click();
    await page.waitForTimeout(1000);
    
    await page.getByText('Report Issue').first().click();
    await page.waitForTimeout(1000);
    
    // Check for form fields
    await expect(page.getByLabel(/Issue Title/i)).toBeVisible({ timeout: 3000 });
    await expect(page.getByLabel(/Description/i)).toBeVisible({ timeout: 3000 });
  });

  test('should show Quick Issue FAB button', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Look for floating action button with aria-label
    const fab = page.locator('button[aria-label="Report Issue"]');
    await expect(fab).toBeVisible({ timeout: 15000 });
  });

  test('should open dialog from FAB', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click floating action button
    const fab = page.locator('button[aria-label="Report Issue"]');
    await fab.click();
    await page.waitForTimeout(500);
    
    // Check for dialog
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });
  });

  test('should close dialog with close button', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click FAB to open dialog
    const fab = page.locator('button[aria-label="Report Issue"]');
    await fab.click();
    await page.waitForTimeout(500);
    
    // Find and click close button (X icon in dialog header)
    const closeButtons = page.locator('[data-testid="CloseIcon"]');
    if (await closeButtons.first().isVisible()) {
      await closeButtons.first().click();
    } else {
      // Try clicking by aria-label
      await page.locator('button').filter({ has: page.locator('svg') }).first().click();
    }
    await page.waitForTimeout(500);
    
    // Dialog should be closed
    const dialog = page.getByRole('dialog');
    await expect(dialog).not.toBeVisible({ timeout: 3000 });
  });
});

test.describe('Mortality Tracking', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });

  test('should display Mortality tab in house detail', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Check for Mortality tab
    const mortalityTab = page.getByRole('tab', { name: /Mortality/i });
    await expect(mortalityTab).toBeVisible({ timeout: 15000 });
  });

  test('should show mortality content when tab clicked', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click Mortality tab
    await page.getByRole('tab', { name: /Mortality/i }).click();
    await page.waitForTimeout(1000);
    
    // Check for mortality-related content
    const mortalityContent = page.getByText(/(Mortality Tracking|No flock|Record Mortality)/i);
    await expect(mortalityContent.first()).toBeVisible({ timeout: 5000 });
  });

  test('should have Record Mortality button or no-flock message', async ({ page }) => {
    await page.goto('/farms/1/houses/1');
    await page.waitForTimeout(2000);
    
    // Click Mortality tab
    await page.getByRole('tab', { name: /Mortality/i }).click();
    await page.waitForTimeout(1000);
    
    // Check for either the button or the no-flock message
    const recordButton = page.getByRole('button', { name: /Record Mortality/i });
    const noFlockMessage = page.getByText(/No flock/i);
    
    const buttonVisible = await recordButton.isVisible({ timeout: 3000 }).catch(() => false);
    const messageVisible = await noFlockMessage.isVisible({ timeout: 3000 }).catch(() => false);
    
    expect(buttonVisible || messageVisible).toBeTruthy();
  });
});
