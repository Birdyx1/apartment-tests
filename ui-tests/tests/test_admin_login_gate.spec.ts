import { expect, test } from '@playwright/test';

// 这个测试专门验证未登录边界，不能继承管理员的登录态。
test.use({ storageState: { cookies: [], origins: [] } });

test('AUTH-001: 未登录访问公寓列表时跳转登录页', async ({ page }) => {
  await test.step('准备：以未登录状态打开公寓列表', async () => {
    await page.goto('/apartment/list');
  });

  await test.step('验证：系统要求管理员先登录', async () => {
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole('heading', { name: '用户登录' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: '用户名' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: '密码' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: '验证码' })).toBeVisible();
    await expect(page.getByRole('button', { name: /登录/ })).toBeVisible();
  });
});
