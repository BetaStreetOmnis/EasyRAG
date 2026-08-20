import { expect, test } from '@playwright/test';

const defaultApps = [
    {
        name: '文档生成',
        icon: 'bx-book-content',
        url: 'http://example.com/document-generator',
        description: '强大的文档生成工具，用于生成高质量的文档。'
    },
    {
        name: '智能问答',
        icon: 'bx-bot',
        url: 'http://example.com/qa',
        description: '智能问答工具，用于回答各种问题。'
    }
];

const mockKnowledgeBaseRoute = async (page) => {
    await page.route('**/kb/list', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ data: ['project-docs'] })
        });
    });
};

const mockDefaultAppsRoute = async (page) => {
    await page.route('**/config/default_apps.json', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(defaultApps)
        });
    });
};

test('switches to the app management section and renders default apps', async ({ page }) => {
    await mockKnowledgeBaseRoute(page);
    await mockDefaultAppsRoute(page);
    await page.goto('/');

    await page.locator('a[href="#app-management"]').click();

    await expect(page.locator('#app-management')).toBeVisible();
    await expect(page.locator('#app-management h2')).toContainText('应用管理');
    await expect(page.locator('#add-app-btn')).toBeVisible();
    await expect(page.locator('#reset-apps-btn')).toBeVisible();
    await expect(page.locator('#app-grid .app-card')).toHaveCount(2);
    await expect(page.locator('#app-grid .app-card').first()).toContainText('文档生成');
});

test('adds an application through the form', async ({ page }) => {
    await mockKnowledgeBaseRoute(page);
    await mockDefaultAppsRoute(page);
    await page.goto('/');
    await page.locator('a[href="#app-management"]').click();

    await page.locator('#add-app-btn').click();
    await expect(page.locator('#add-app-form-container')).toBeVisible();
    await expect(page.locator('#app-name')).toBeVisible();
    await expect(page.locator('#app-name')).toHaveAttribute('required', '');
    await expect(page.locator('#app-icon')).toBeVisible();
    await expect(page.locator('#app-url')).toBeVisible();
    await expect(page.locator('#app-url')).toHaveAttribute('required', '');
    await expect(page.locator('#app-description')).toBeVisible();

    await page.locator('#app-name').fill('测试应用');
    await page.locator('#app-icon').selectOption('bx-rocket');
    await page.locator('#app-url').fill('https://example.com/new-app');
    await page.locator('#app-description').fill('用于冒烟测试的新应用');
    await page.locator('#add-app-form button[type="submit"]').click();

    await expect(page.locator('#app-grid .app-card')).toHaveCount(3);
    await expect(page.locator('#app-grid .app-card').nth(2)).toContainText('测试应用');
    await expect(page.locator('#app-grid .app-card').nth(2)).toContainText('用于冒烟测试的新应用');
    await expect(page.locator('#add-app-form-container')).toBeHidden();
    await expect(page.locator('#toast-container .toast')).toContainText('应用添加成功');
});

test('cancels adding an application and resets the app list', async ({ page }) => {
    await mockKnowledgeBaseRoute(page);
    await mockDefaultAppsRoute(page);
    const defaultAppsRequests = [];
    await page.route('**/config/default_apps.json', async (route) => {
        defaultAppsRequests.push(route.request().url());
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(defaultApps)
        });
    });

    await page.goto('/');
    await page.locator('a[href="#app-management"]').click();

    await page.locator('#add-app-btn').click();
    await page.locator('#app-name').fill('将被取消的应用');
    await page.locator('#app-url').fill('https://example.com/cancelled');
    await page.locator('#cancel-add-app').click();

    await expect(page.locator('#add-app-form-container')).toBeHidden();
    await expect(page.locator('#app-name')).toHaveValue('');
    await expect(page.locator('#app-url')).toHaveValue('');

    page.once('dialog', (dialog) => {
        expect(dialog.message()).toContain('确定要重置为默认应用列表吗？');
        void dialog.accept();
    });
    await page.locator('#reset-apps-btn').click();

    await expect(page.locator('#app-grid .app-card')).toHaveCount(2);
    await expect(page.locator('#toast-container .toast')).toContainText('已重置为默认应用列表');
    expect(defaultAppsRequests).toHaveLength(2);
});
