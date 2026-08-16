import { expect, test } from '@playwright/test';

test('switches between knowledge base search and management sections', async ({ page }) => {
    await page.goto('/');

    await page.locator('a[href="#kb-search"]').click();
    await expect(page.locator('#kb-search')).toBeVisible();
    await expect(page.locator('#kb-management')).toBeHidden();

    await page.locator('a[href="#kb-management"]').click();
    await expect(page.locator('#kb-management')).toBeVisible();
    await expect(page.locator('#kb-search')).toBeHidden();
});

test('renders the knowledge base management forms', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('#create-kb-form')).toBeVisible();
    await expect(page.locator('#kb-name')).toHaveAttribute('required', '');
    await expect(page.locator('#kb-list-table')).toContainText('知识库名称');
    await expect(page.locator('#upload-file-form #upload-kb-select')).toHaveCount(1);
    await expect(page.locator('#files-to-upload')).toHaveAttribute('multiple', '');
});

test('keeps the page stable after refreshing the knowledge base list', async ({ page }) => {
    const pageErrors = [];
    page.on('pageerror', (error) => pageErrors.push(error));

    await page.goto('/');
    await page.locator('#refresh-kb-list').click();

    await expect(page.locator('.container')).toBeAttached();
    await expect(page.locator('#kb-list-table')).toBeVisible();
    expect(pageErrors).toEqual([]);
});
