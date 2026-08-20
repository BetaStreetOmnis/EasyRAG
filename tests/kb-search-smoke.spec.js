import { expect, test } from '@playwright/test';

const mockKnowledgeBaseRoute = async (page) => {
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
                    vector_count: 2
                }
            })
        });
    });
};

test('renders the knowledge base search form', async ({ page }) => {
    await mockKnowledgeBaseRoute(page);
    await page.goto('/');

    await page.locator('a[href="#kb-search"]').click();

    await expect(page.locator('#search-form')).toBeVisible();
    await expect(page.locator('#search-kb-select')).toBeVisible();
    await expect(page.locator('#search-kb-select option')).toHaveCount(2);
    await expect(page.locator('#search-query')).toBeVisible();
    await expect(page.locator('#search-form button[type="submit"]')).toBeVisible();
    await expect(page.locator('#search-form button[type="submit"]')).toContainText('检索');
});

test('searches the selected knowledge base and renders results', async ({ page }) => {
    await mockKnowledgeBaseRoute(page);
    const searchRequests = [];
    await page.route('**/kb/search', async (route) => {
        searchRequests.push(route.request().postDataJSON());
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                data: [
                    {
                        content: 'EasyRAG 使用向量检索找到相关知识。',
                        score: 0.9876,
                        metadata: { source: 'easyrag-guide.md' }
                    },
                    {
                        text: '知识库支持文件上传和分片管理。',
                        score: 0.8421,
                        metadata: { source: 'kb-operations.md' }
                    }
                ]
            })
        });
    });

    await page.goto('/');
    await page.locator('a[href="#kb-search"]').click();
    await page.locator('#search-kb-select').selectOption('project-docs');
    await page.locator('#search-query').fill('EasyRAG 如何检索知识？');
    await page.locator('#top-k').fill('2');
    await page.locator('#use-rerank').uncheck();
    await page.locator('#search-form button[type="submit"]').click();

    await expect(page.locator('#search-results .result-item')).toHaveCount(2);
    await expect(page.locator('#search-results .result-item').first()).toContainText('easyrag-guide.md');
    await expect(page.locator('#search-results .result-item').first()).toContainText('相关度: 0.988');
    await expect(page.locator('#search-results .result-item').first()).toContainText('EasyRAG 使用向量检索找到相关知识。');
    await expect(page.locator('#search-results .result-item').nth(1)).toContainText('kb-operations.md');
    await expect(page.locator('#search-results .result-item').nth(1)).toContainText('相关度: 0.842');
    await expect(page.locator('#search-results .result-item').nth(1)).toContainText('知识库支持文件上传和分片管理。');
    expect(searchRequests).toEqual([
        {
            kb_name: 'project-docs',
            query: 'EasyRAG 如何检索知识？',
            top_k: 2,
            use_rerank: false
        }
    ]);
});

test('shows an empty result message when search returns no data', async ({ page }) => {
    await mockKnowledgeBaseRoute(page);
    await page.route('**/kb/search', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ data: [] })
        });
    });

    await page.goto('/');
    await page.locator('a[href="#kb-search"]').click();
    await page.locator('#search-kb-select').selectOption('project-docs');
    await page.locator('#search-query').fill('不存在的文档内容');
    await page.locator('#search-form button[type="submit"]').click();

    await expect(page.locator('#search-results')).toHaveText('未找到相关内容。');
});

test('shows a warning and does not call the search API with an empty query', async ({ page }) => {
    await mockKnowledgeBaseRoute(page);
    let searchRequestCount = 0;
    await page.route('**/kb/search', async (route) => {
        searchRequestCount += 1;
        await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    });

    await page.goto('/');
    await page.locator('a[href="#kb-search"]').click();
    await page.locator('#search-kb-select').selectOption('project-docs');
    await page.locator('#search-form button[type="submit"]').click();

    await expect(page.locator('.toast .toast-message')).toHaveText('请选择知识库并输入问题');
    await expect(page.locator('#search-results')).toHaveText('');
    expect(searchRequestCount).toBe(0);
});
