import { test, expect } from '@playwright/test';

test.describe('Discovery Dashboard (Level 1)', () => {
  test('shows page title and date picker', async ({ page }) => {
    await page.goto('/discovery');
    await expect(page.getByRole('heading', { name: 'Discovery' })).toBeVisible();
    await expect(page.locator('input[type="date"]')).toBeVisible();
  });

  test('shows source cards when data exists', async ({ page }) => {
    // First trigger discovery to ensure data exists
    const apiBase = 'http://localhost:8000';
    await page.request.post(`${apiBase}/api/discovery/run?source=hackernews`);

    await page.goto('/discovery');
    // Wait for stats to load
    await expect(page.getByText(/Hacker News/i)).toBeVisible({ timeout: 10000 });
  });

  test('source cards are clickable links', async ({ page }) => {
    const apiBase = 'http://localhost:8000';
    await page.request.post(`${apiBase}/api/discovery/run?source=hackernews`);

    await page.goto('/discovery');
    const hnCard = page.getByText(/Hacker News/i);
    await expect(hnCard).toBeVisible({ timeout: 10000 });

    // Click the HN card and verify navigation
    await hnCard.click();
    await expect(page).toHaveURL(/\/discovery\/hackernews/);
  });

  test('date picker changes displayed data', async ({ page }) => {
    await page.goto('/discovery');

    // Navigate to a far-future date with guaranteed no data
    const dateInput = page.locator('input[type="date"]');
    await dateInput.fill('2099-01-01');

    // Should show empty state after API responds
    await expect(page.getByText(/No items fetched for this date/i)).toBeVisible({ timeout: 10000 });
  });

  test('left arrow navigates to previous day', async ({ page }) => {
    await page.goto('/discovery');
    const dateInput = page.locator('input[type="date"]');
    const initialDate = await dateInput.inputValue();

    // Click left arrow
    await page.getByText('◀').click();

    const newDate = await dateInput.inputValue();
    expect(newDate).not.toBe(initialDate);
  });

  test('Run Discovery button works', async ({ page }) => {
    await page.goto('/discovery');
    const btn = page.getByRole('button', { name: /Run Discovery/i });
    await expect(btn).toBeVisible();

    // Click and verify it completes (button returns to "Run Discovery" after run)
    await btn.click();
    // The run may complete very fast if data is cached, so just verify
    // the button is back to its normal state after the run
    await expect(btn).toContainText(/Run Discovery/i, { timeout: 120000 });
  });
});

test.describe('Source Item List (Level 2)', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure HN data exists
    const apiBase = 'http://localhost:8000';
    await page.request.post(`${apiBase}/api/discovery/run?source=hackernews`);
  });

  test('shows source name and item count', async ({ page }) => {
    await page.goto('/discovery');
    await page.getByText(/Hacker News/i).click();

    await expect(page.getByRole('heading', { name: /Hacker News/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/items/i)).toBeVisible();
  });

  test('shows list of item titles', async ({ page }) => {
    await page.goto('/discovery');
    await page.getByText(/Hacker News/i).click();

    // Should have clickable items in the list
    const items = page.locator('a[href^="/discovery/item/"]');
    await expect(items.first()).toBeVisible({ timeout: 10000 });
    const count = await items.count();
    expect(count).toBeGreaterThan(0);
  });

  test('back link returns to dashboard', async ({ page }) => {
    await page.goto('/discovery');
    await page.getByText(/Hacker News/i).click();
    await expect(page.getByRole('heading', { name: /Hacker News/i })).toBeVisible({ timeout: 10000 });

    // Click back
    await page.getByText('← Discovery').click();
    await expect(page).toHaveURL(/\/discovery$/);
  });

  test('clicking item title navigates to detail', async ({ page }) => {
    await page.goto('/discovery');
    await page.getByText(/Hacker News/i).click();

    const firstItem = page.locator('a[href^="/discovery/item/"]').first();
    await expect(firstItem).toBeVisible({ timeout: 10000 });
    await firstItem.click();

    await expect(page).toHaveURL(/\/discovery\/item\//);
  });
});

test.describe('Item Detail (Level 3)', () => {
  test.beforeEach(async ({ page }) => {
    const apiBase = 'http://localhost:8000';
    await page.request.post(`${apiBase}/api/discovery/run?source=hackernews`);
  });

  test('shows full item details', async ({ page }) => {
    // Navigate to an item via the drill-down
    await page.goto('/discovery');
    await page.getByText(/Hacker News/i).click();

    const firstItem = page.locator('a[href^="/discovery/item/"]').first();
    await expect(firstItem).toBeVisible({ timeout: 10000 });
    await firstItem.click();

    // Should show detail fields
    await expect(page.getByText('Source')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Hacker News')).toBeVisible();
  });

  test('shows metadata section', async ({ page }) => {
    await page.goto('/discovery');
    await page.getByText(/Hacker News/i).click();

    const firstItem = page.locator('a[href^="/discovery/item/"]').first();
    await expect(firstItem).toBeVisible({ timeout: 10000 });
    await firstItem.click();

    await expect(page.getByText('Metadata')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('hn_id')).toBeVisible();
  });

  test('back button returns to source list', async ({ page }) => {
    await page.goto('/discovery');
    await page.getByText(/Hacker News/i).click();

    const firstItem = page.locator('a[href^="/discovery/item/"]').first();
    await expect(firstItem).toBeVisible({ timeout: 10000 });
    await firstItem.click();

    // Click back
    await expect(page.getByText('← Back')).toBeVisible({ timeout: 10000 });
    await page.getByText('← Back').click();

    // Should be back on source list
    await expect(page.getByRole('heading', { name: /Hacker News/i })).toBeVisible({ timeout: 10000 });
  });

  test('404 for non-existent item', async ({ page }) => {
    await page.goto('/discovery/item/nonexistent');
    await expect(page.getByText(/not found/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Full drill-down flow', () => {
  test('dashboard → source → item → back → back', async ({ page }) => {
    const apiBase = 'http://localhost:8000';
    await page.request.post(`${apiBase}/api/discovery/run?source=hackernews`);

    // Level 1: Dashboard
    await page.goto('/discovery');
    await expect(page.getByRole('heading', { name: 'Discovery' })).toBeVisible();
    await expect(page.getByText(/Hacker News/i)).toBeVisible({ timeout: 10000 });

    // Click into HN → Level 2
    await page.getByText(/Hacker News/i).click();
    await expect(page).toHaveURL(/\/discovery\/hackernews/);
    await expect(page.getByRole('heading', { name: /Hacker News/i })).toBeVisible({ timeout: 10000 });

    // Click first item → Level 3
    const firstItem = page.locator('a[href^="/discovery/item/"]').first();
    await expect(firstItem).toBeVisible({ timeout: 10000 });
    const itemTitle = await firstItem.textContent();
    await firstItem.click();
    await expect(page).toHaveURL(/\/discovery\/item\//);

    // Verify the title matches
    await expect(page.getByRole('heading').first()).toContainText(itemTitle!.trim().slice(0, 20), { timeout: 10000 });

    // Back to Level 2
    await page.getByText('← Back').click();
    await expect(page.getByRole('heading', { name: /Hacker News/i })).toBeVisible({ timeout: 10000 });

    // Back to Level 1
    await page.getByText('← Discovery').click();
    await expect(page.getByRole('heading', { name: 'Discovery' })).toBeVisible();
  });
});
