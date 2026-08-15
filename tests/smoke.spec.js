import { expect, test } from '@playwright/test';

test('loads the application shell and chat input', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('.container')).toBeVisible();
    await expect(page.locator('.main-content')).toBeVisible();
    await expect(page.getByRole('heading', { level: 1, name: 'EasyRAG 知识库管理系统' })).toBeVisible();
    await expect(page.locator('#chat-window')).toBeAttached();
    await expect(page.locator('#chat-input-container')).toBeAttached();
    await expect(page.locator('#chat-input')).toBeAttached();
    await expect(page.locator('#chat-send-btn')).toBeAttached();
});
