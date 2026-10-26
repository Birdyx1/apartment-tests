import { test, expect } from './worker-account.fixture';
import { WorkerProfilePage } from '../pages/worker-profile.page';

test.describe('维修工端个人中心', () => {
  test('WP-001: 个人中心显示当前维修工账号信息', async ({ page, workerAccount }) => {
    const profile = new WorkerProfilePage(page);
    await test.step('准备：使用本用例专属维修工登录', async () => {
      await profile.login(workerAccount.username, workerAccount.password);
    });

    const profileResponse = await test.step('操作：点击底部“我的”并读取个人资料', async () => {
      const responsePromise = page.waitForResponse((response) =>
        new URL(response.url()).pathname === '/worker-app/profile' &&
        response.request().method() === 'GET');
      await profile.openFromNavigation();
      return responsePromise;
    });

    await test.step('验证：页面账号和手机号与个人资料接口一致', async () => {
      expect(profileResponse.status()).toBe(200);
      const body = await profileResponse.json();
      expect(body.code).toBe(200);
      expect(body.data.username).toBe(workerAccount.username);
      expect(body.data.phone).toBe(workerAccount.phone);

      await expect(page.locator('.profile-name')).toHaveText(workerAccount.username);
      await expect(profile.profileRow('账号')).toContainText(workerAccount.username);
      await expect(profile.profileRow('手机')).toContainText(workerAccount.phone);
      await expect(page.getByText('退出登录', { exact: true })).toBeVisible();
    });
  });

  test('WP-002: 退出登录后个人中心受登录保护', async ({ page, workerAccount }) => {
    const profile = new WorkerProfilePage(page);
    await test.step('准备：登录并打开个人中心', async () => {
      await profile.login(workerAccount.username, workerAccount.password);
      await profile.openFromNavigation();
    });

    await test.step('操作：退出登录后再次直接访问个人中心', async () => {
      await profile.logout();
      await profile.openProtectedProfile();
    });

    await test.step('验证：未登录状态被重定向到登录页', async () => {
      await expect(page).toHaveURL(`${(process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '')}/login`);
      await expect(page.getByRole('heading', { name: '维修工端' })).toBeVisible();
      await expect(page.getByRole('textbox', { name: /用户名/ })).toBeVisible();
    });
  });
});
