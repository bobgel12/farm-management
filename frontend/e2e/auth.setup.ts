import { test as setup, expect } from '@playwright/test';

const authFile = 'e2e/.auth/user.json';

/**
 * Authentication setup for Playwright tests
 * This runs before all tests to ensure the user is logged in
 */
setup('authenticate', async ({ page }) => {
  // Navigate to login page
  await page.goto('/login');

  // Fill in login credentials
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for successful login - should redirect to dashboard
  await expect(page).toHaveURL(/\/(dashboard)?$/);

  // Verify we're logged in by checking for user menu or dashboard content
  await expect(page.locator('text=Dashboard').first()).toBeVisible({ timeout: 10000 });

  // Save authentication state
  await page.context().storageState({ path: authFile });
});

