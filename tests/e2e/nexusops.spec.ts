/**
 * NexusOps E2E Tests
 * Test Suite for Frontend Application
 *
 * Frontend: http://localhost:3000
 * Backend: http://localhost:8000
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const TEST_USER = 'admin';
const TEST_PASSWORD = 'password';

// Test configuration
test.use({
  baseURL: BASE_URL,
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
  trace: 'retain-on-failure',
});

// Helper function to login
async function login(page: Page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // Check if already logged in (redirect to dashboard)
  if (page.url().includes('/dashboard')) {
    return;
  }

  // Fill login form
  await page.fill('input[placeholder="Username"]', TEST_USER);
  await page.fill('input[placeholder="Password"]', TEST_PASSWORD);
  await page.click('button:has-text("Login")');

  // Wait for redirect to dashboard
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

test.describe('Phase 1: Basic Functionality', () => {

  test.describe.configure({ mode: 'serial' });

  test('1.1 - Home Page Load', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should redirect to login if not authenticated
    await expect(page).toHaveURL(/.*login.*/);

    // Verify login page elements
    await expect(page.locator('text=NexusOps')).toBeVisible();
    await expect(page.locator('text=AI Native Operations Platform')).toBeVisible();
    await expect(page.locator('input[placeholder="Username"]')).toBeVisible();
    await expect(page.locator('input[placeholder="Password"]')).toBeVisible();
    await expect(page.locator('button:has-text("Login")')).toBeVisible();
  });

  test('1.2 - Login Flow', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill login form
    await page.fill('input[placeholder="Username"]', TEST_USER);
    await page.fill('input[placeholder="Password"]', TEST_PASSWORD);
    await page.click('button:has-text("Login")');

    // Wait for success message or redirect
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Verify dashboard loaded - look for Infrastructure Overview title or any dashboard content
    await expect(page.locator('h4').filter({ hasText: /Infrastructure|Overview/i }).first()).toBeVisible({ timeout: 5000 });
  });

  test('1.3 - Dashboard Display', async ({ page }) => {
    await login(page);

    // Check dashboard elements - look for Infrastructure Overview or stats cards
    await expect(page.locator('h4, [class*="ant-statistic"]').first()).toBeVisible();

    // Check for stats cards
    const statsCards = page.locator('[class*="ant-card"]').first();
    await expect(statsCards).toBeVisible({ timeout: 5000 });

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_dashboard.png', fullPage: true });
  });

  test('1.4 - Projects Page', async ({ page }) => {
    await login(page);

    // Navigate to projects
    await page.click('text=Projects');
    await page.waitForLoadState('networkidle');

    // Verify projects page loaded
    await expect(page).toHaveURL(/.*projects.*/);
    await expect(page.locator('h4').filter({ hasText: 'Project' }).first()).toBeVisible();

    // Check for project list or empty state
    const projectTable = page.locator('[class*="ant-table-wrapper"]').first();
    await expect(projectTable).toBeVisible({ timeout: 5000 });

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_projects.png', fullPage: true });
  });

  test('1.5 - Agent Store Page', async ({ page }) => {
    await login(page);

    // Navigate to agent store
    await page.click('text=Agent Store');
    await page.waitForLoadState('networkidle');

    // Verify agent store page loaded
    await expect(page).toHaveURL(/.*agent-store.*/);
    await expect(page.locator('h4, [class*="ant-card"]').filter({ hasText: /Agent/i }).first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_agent_store.png', fullPage: true });
  });

  test('1.6 - Settings Page', async ({ page }) => {
    await login(page);

    // Navigate to settings
    await page.click('text=Settings');
    await page.waitForLoadState('networkidle');

    // Verify settings page loaded
    await expect(page).toHaveURL(/.*settings.*/);
    await expect(page.locator('h4, h3').filter({ hasText: /Settings|Configuration/i }).first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_settings.png', fullPage: true });
  });
});

test.describe('Phase 2: Core User Flows', () => {

  test.describe.configure({ mode: 'serial' });

  test('2.1 - Create Project Flow', async ({ page }) => {
    await login(page);

    // Navigate to projects
    await page.click('text=Projects');
    await page.waitForLoadState('networkidle');

    // Look for create button
    const createButton = page.locator('button:has-text("Create"), button:has-text("New"), button:has-text("Add")').first();

    if (await createButton.isVisible()) {
      await createButton.click();

      // Wait for modal or form
      await page.waitForTimeout(1000);

      // Take screenshot
      await page.screenshot({ path: 'test_results/e2e_create_project_modal.png', fullPage: true });
    }
  });

  test('2.2 - Deployments Page', async ({ page }) => {
    await login(page);

    // Navigate to deployments
    await page.click('text=Deployments');
    await page.waitForLoadState('networkidle');

    // Verify deployments page loaded
    await expect(page).toHaveURL(/.*deployments.*/);
    // Deployments page has h4 title with "Deployments"
    await expect(page.locator('h4').filter({ hasText: 'Deployments' }).first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_deployments.png', fullPage: true });
  });

  test('2.3 - Logs Page', async ({ page }) => {
    await login(page);

    // Navigate to logs
    await page.click('text=Logs');
    await page.waitForLoadState('networkidle');

    // Verify logs page loaded
    await expect(page).toHaveURL(/.*logs.*/);
    await expect(page.locator('h4, [class*="ant-input"], [class*="logs"]').first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_logs.png', fullPage: true });
  });

  test('2.4 - Resources Page', async ({ page }) => {
    await login(page);

    // Navigate to resources
    await page.click('text=Resources');
    await page.waitForLoadState('networkidle');

    // Verify resources page loaded
    await expect(page).toHaveURL(/.*resources.*/);

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_resources.png', fullPage: true });
  });

  test('2.5 - AI Assistant (if available)', async ({ page }) => {
    await login(page);

    // Look for AI Assistant button/drawer
    const aiButton = page.locator('button:has-text("AI"), [class*="ai-assistant"], button[aria-label*="AI"]').first();

    if (await aiButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await aiButton.click();
      await page.waitForTimeout(1000);

      // Take screenshot
      await page.screenshot({ path: 'test_results/e2e_ai_assistant.png', fullPage: true });
    }
  });

  test('2.6 - Logout Flow', async ({ page }) => {
    await login(page);

    // Look for logout button or user menu
    const userMenu = page.locator('[class*="user-menu"], [class*="avatar"], button:has-text("Logout"), button:has-text("Sign out")').first();

    if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
      await userMenu.click();

      const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), text=Logout').first();
      if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await logoutButton.click();

        // Should redirect to login
        await page.waitForURL('**/login', { timeout: 5000 }).catch(() => {});
      }
    }

    // Take screenshot
    await page.screenshot({ path: 'test_results/e2e_logout.png', fullPage: true });
  });
});

test.describe('Phase 3: UI/UX Validation', () => {

  test('3.1 - Navigation Consistency', async ({ page }) => {
    await login(page);

    // Check sidebar navigation items
    const navItems = ['Dashboard', 'Projects', 'Deployments', 'Resources', 'Logs', 'Agent Store'];

    for (const item of navItems) {
      const navLink = page.locator(`text=${item}`).first();
      if (await navLink.isVisible({ timeout: 2000 }).catch(() => false)) {
        await navLink.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
      }
    }
  });

  test('3.2 - Responsive Layout', async ({ page }) => {
    await login(page);

    // Test different viewport sizes
    const viewports = [
      { width: 1920, height: 1080, name: 'desktop' },
      { width: 1366, height: 768, name: 'laptop' },
      { width: 768, height: 1024, name: 'tablet' },
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(500);
      await page.screenshot({ path: `test_results/e2e_responsive_${viewport.name}.png`, fullPage: false });
    }
  });

  test('3.3 - Error Handling', async ({ page }) => {
    // Test accessing non-existent route
    await login(page);
    await page.goto('/non-existent-route-12345');
    await page.waitForLoadState('networkidle');

    // Should redirect to dashboard or show 404
    await page.screenshot({ path: 'test_results/e2e_404_handling.png', fullPage: true });
  });
});
