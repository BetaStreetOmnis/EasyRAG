import { expect, test } from '@playwright/test';

test('主题切换：更新主题状态并保持界面渲染', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error));

  await page.goto('/');

  const themeToggle = page.locator('#theme-toggle');
  await expect(page.locator('body')).not.toHaveClass(/dark-theme/);
  await expect(themeToggle.locator('.bx-sun')).toBeVisible();

  await themeToggle.click();
  await expect(page.locator('body')).toHaveClass(/dark-theme/);
  await expect(themeToggle.locator('.bx-moon')).toBeVisible();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('theme'))).toBe('dark');

  const sidebar = page.locator('aside');
  await expect(sidebar).toBeVisible();
  await expect(page.getByRole('heading', { level: 2, name: 'EasyRAG' })).toBeVisible();

  await themeToggle.click();
  await expect(page.locator('body')).not.toHaveClass(/dark-theme/);
  await expect(themeToggle.locator('.bx-sun')).toBeVisible();
  await expect.poll(() => page.evaluate(() => localStorage.getItem('theme'))).toBe('light');

  await expect(sidebar).toBeVisible();
  expect(pageErrors).toHaveLength(0);
});

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

test('无后端降级冒烟：知识库列表请求失败不破坏界面', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error));

  const initialKbListFailure = page.waitForResponse(
    (response) => response.url().includes('/kb/list')
  );

  await page.goto('/');
  await initialKbListFailure;

  const kbManagementSection = page.locator('#kb-management');
  await expect(kbManagementSection).toBeVisible();
  await expect(kbManagementSection).toHaveClass(/(?:^|\s)active(?:\s|$)/);

  const failureRow = page.locator('#kb-list-table tbody tr');
  await expect(failureRow).toHaveCount(1);
  await expect(failureRow.locator('td')).toHaveText('加载知识库列表失败');

  const refreshKbListFailure = page.waitForResponse(
    (response) => response.url().includes('/kb/list')
  );
  await page.locator('#refresh-kb-list').click();
  await refreshKbListFailure;

  await expect(kbManagementSection).toBeVisible();
  await expect(failureRow).toHaveCount(1);
  await expect(failureRow.locator('td')).toHaveText('加载知识库列表失败');

  expect(pageErrors).toHaveLength(0);
});

test('无后端降级：上传表单缺知识库时仅 toast 提示且界面不破坏', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error));

  const initialKbListFailure = page.waitForResponse(
    (response) => response.url().includes('/kb/list')
  );

  await page.goto('/');
  await initialKbListFailure;

  await page.locator('.sidebar nav a[href="#file-management"]').click();

  const fileManagementSection = page.locator('#file-management');
  await expect(fileManagementSection).toBeVisible();
  await expect(fileManagementSection).toHaveClass(/(?:^|\s)active(?:\s|$)/);
  await expect(page.locator('#kb-management')).not.toHaveClass(/(?:^|\s)active(?:\s|$)/);

  await page.locator('#files-to-upload').setInputFiles({
    name: 'sample.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('easyrag step6')
  });
  await expect(page.locator('#upload-kb-select option')).toHaveCount(0);

  await page.locator('#upload-file-form').evaluate((form) => {
    form.noValidate = true;
  });
  await page.locator('#upload-file-form button[type="submit"]').click();
  await expect(page.locator('.toast.warning .toast-message')).toHaveText('请选择知识库和文件');

  await expect(page.locator('#upload-status')).toHaveText('');
  await expect(page.locator('#upload-progress-container')).toBeHidden();
  await expect(fileManagementSection).toBeVisible();
  await expect(fileManagementSection).toHaveClass(/(?:^|\s)active(?:\s|$)/);

  expect(pageErrors).toHaveLength(0);
});

test('无后端降级：创建知识库表单空名称仅 toast 提示且界面不破坏', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error));

  const initialKbListFailure = page.waitForResponse(
    (response) => response.url().includes('/kb/list')
  );

  await page.goto('/');
  await initialKbListFailure;

  const kbManagementSection = page.locator('#kb-management');
  const createKbForm = page.locator('#create-kb-form');
  const kbNameInput = page.locator('#kb-name');
  await expect(createKbForm).toBeVisible();
  await expect(kbNameInput).toBeVisible();
  await expect(kbNameInput).toHaveValue('');

  const createRequests = [];
  page.on('request', (request) => {
    if (request.url().includes('/kb/create')) {
      createRequests.push(request);
    }
  });

  await createKbForm.evaluate((form) => {
    form.noValidate = true;
  });
  await createKbForm.locator('button[type="submit"]').click();
  await expect(page.locator('.toast.warning .toast-message')).toHaveText('知识库名称不能为空');

  await expect(kbNameInput).toBeVisible();
  await expect(kbManagementSection).toBeVisible();
  await expect(kbManagementSection).toHaveClass(/(?:^|\s)active(?:\s|$)/);
  expect(createRequests).toHaveLength(0);
  expect(pageErrors).toHaveLength(0);
});

test('无后端降级：删除知识库未选择时仅 toast 提示且界面不破坏', async ({ page }) => {
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error));

  const initialKbListFailure = page.waitForResponse(
    (response) => response.url().includes('/kb/list')
  );

  await page.goto('/');
  await initialKbListFailure;

  const kbManagementSection = page.locator('#kb-management');
  const deleteKbSelect = page.locator('#delete-kb-select');
  await expect(deleteKbSelect).toBeVisible();
  await expect(deleteKbSelect).toHaveValue('');
  await expect(page.locator('#delete-kb-btn')).toBeVisible();

  const deleteRequests = [];
  page.on('request', (request) => {
    if (request.url().includes('/kb/delete')) {
      deleteRequests.push(request);
    }
  });

  await page.locator('#delete-kb-btn').click();
  await expect(page.locator('.toast.warning .toast-message')).toHaveText('请选择要删除的知识库');

  await expect(deleteKbSelect).toBeVisible();
  await expect(kbManagementSection).toBeVisible();
  await expect(kbManagementSection).toHaveClass(/(?:^|\s)active(?:\s|$)/);
  expect(deleteRequests).toHaveLength(0);
  expect(pageErrors).toHaveLength(0);
});
