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

test('导航冒烟：切换主导航区块', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error));

  await page.goto('/');

  const navigationCases = [
    { linkName: '文件管理', sectionId: 'file-management' },
    { linkName: '知识库检索', sectionId: 'kb-search' },
    { linkName: '应用管理', sectionId: 'app-management' },
  ];

  for (const { linkName, sectionId } of navigationCases) {
    await page.getByRole('link', { name: linkName }).click();

    const activeSection = page.locator(`#${sectionId}`);
    await expect(activeSection).toHaveClass(/(?:^|\s)active(?:\s|$)/);
    await expect(activeSection).toBeVisible();
    await expect(page.locator('#kb-management')).not.toHaveClass(/(?:^|\s)active(?:\s|$)/);
  }

  expect(pageErrors).toHaveLength(0);
});
