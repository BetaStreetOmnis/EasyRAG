import { expect, test } from '@playwright/test';

const uploadRoutes = [
    '**/api/knowledge-bases/*/upload',
    '**/kb/upload'
];

const mockUploadRoute = async (page, status, payload) => {
    for (const route of uploadRoutes) {
        await page.route(route, async (interceptedRoute) => {
            await interceptedRoute.fulfill({
                status,
                contentType: 'application/json',
                body: JSON.stringify(payload)
            });
        });
    }
};

const mockKnowledgeBaseRoutes = async (page) => {
    await page.route('**/kb/list', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ data: ['project-docs'] })
        });
    });
    await page.route('**/kb/info/*', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                data: {
                    kb_name: 'project-docs',
                    dimension: 768,
                    index_type: 'HNSW',
                    vector_count: 0
                }
            })
        });
    });
    await page.route('**/apps/**', async (route) => {
        await route.fulfill({ status: 204 });
    });
};

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

test('uploads a single file successfully', async ({ page }) => {
    await mockKnowledgeBaseRoutes(page);
    await mockUploadRoute(page, 200, {
        status: 'success',
        message: '成功添加 1 个文档到知识库 project-docs'
    });

    await page.goto('/');
    await page.locator('a[href="#file-management"]').click();
    await page.locator('#upload-kb-select').selectOption('project-docs');
    await page.locator('#files-to-upload').setInputFiles({
        name: 'single.md',
        mimeType: 'text/markdown',
        buffer: Buffer.from('# Single file')
    });
    await page.locator('#upload-file-form button[type="submit"]').click();

    await expect(page.locator('#upload-status')).toHaveText(
        '成功添加 1 个文档到知识库 project-docs'
    );
    await expect(page.locator('#upload-progress-bar')).toHaveAttribute('style', expect.stringContaining('100%'));
    await expect(page.locator('#files-to-upload')).toHaveValue('');
});

test('uploads multiple files successfully', async ({ page }) => {
    await mockKnowledgeBaseRoutes(page);
    await mockUploadRoute(page, 200, {
        status: 'success',
        message: '成功添加 2 个文档到知识库 project-docs'
    });

    await page.goto('/');
    await page.locator('a[href="#file-management"]').click();
    await page.locator('#upload-kb-select').selectOption('project-docs');
    await page.locator('#files-to-upload').setInputFiles([
        {
            name: 'first.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# First file')
        },
        {
            name: 'second.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Second file')
        }
    ]);
    await page.locator('#upload-file-form button[type="submit"]').click();

    await expect(page.locator('#upload-status')).toHaveText(
        '成功添加 2 个文档到知识库 project-docs'
    );
    await expect(page.locator('#upload-progress-bar')).toHaveAttribute('style', expect.stringContaining('100%'));
    await expect(page.locator('#files-to-upload')).toHaveValue('');
});

test('shows an error message when upload fails', async ({ page }) => {
    await mockKnowledgeBaseRoutes(page);
    await mockUploadRoute(page, 500, {
        detail: '服务器处理上传失败'
    });

    await page.goto('/');
    await page.locator('a[href="#file-management"]').click();
    await page.locator('#upload-kb-select').selectOption('project-docs');
    await page.locator('#files-to-upload').setInputFiles({
        name: 'invalid.md',
        mimeType: 'text/markdown',
        buffer: Buffer.from('# Invalid file')
    });
    await page.locator('#upload-file-form button[type="submit"]').click();

    await expect(page.locator('#upload-status')).toHaveText('上传失败: 服务器处理上传失败');
    await expect(page.locator('#upload-progress-bar')).toHaveAttribute('style', expect.stringContaining('0%'));
    await expect(page.locator('#files-to-upload')).toHaveValue('C:\\fakepath\\invalid.md');
});
