import { expect, test } from '@playwright/test';

test('页面冒烟：标题与主导航渲染', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error));

  await page.goto('/');

  await expect(page).toHaveTitle('FluidGen AI - 知识库管理系统');
  await expect(page.getByRole('heading', { level: 2, name: 'EasyRAG' })).toBeVisible();
  await expect(page.locator('aside').getByText('知识库管理', { exact: true })).toBeVisible();
  expect(pageErrors).toHaveLength(0);
});
