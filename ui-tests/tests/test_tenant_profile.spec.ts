import { expect, test } from './tenant-home-data.fixture';
import { TenantProfilePage } from '../pages/tenant-profile.page';

function profileResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/profile' &&
    response.request().method() === 'GET');
}

test.describe('租客 H5 我的个人中心', () => {
  test('TPF-001: 个人中心展示当前租客资料', async ({ page, tenantAccount }) => {
    const profilePage = new TenantProfilePage(page);
    let profileData = { name: '', phone: '', gender: 0, idCard: '' };

    await test.step('准备：登录专属租客并进入我的页面', async () => {
      await profilePage.login(tenantAccount.phone, tenantAccount.password);
      const responsePromise = profileResponse(page);
      await profilePage.openProfile();
      const response = await responsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      expect(body.data).toMatchObject({
        name: tenantAccount.name,
        phone: tenantAccount.phone,
        gender: 1,
      });
      profileData = body.data;
    });

    await test.step('验证：页面资料与当前账号接口一致', async () => {
      await expect(page.getByText('个人信息', { exact: true })).toBeVisible();
      await expect(profilePage.infoRow('姓名')).toContainText(profileData.name);
      await expect(profilePage.infoRow('性别')).toContainText('男');
      await expect(profilePage.infoRow('手机号')).toContainText(profileData.phone);
      await expect(profilePage.infoRow('身份证')).toContainText(profileData.idCard);
      await expect(page.getByText('编辑个人信息', { exact: true })).toBeVisible();
      await expect(page.getByText('退出登录', { exact: true })).toBeVisible();
    });
  });

  test('TPF-002: 退出登录后个人中心需要重新认证', async ({ page, tenantAccount }) => {
    const profilePage = new TenantProfilePage(page);

    await test.step('准备：登录专属租客并进入我的页面', async () => {
      await profilePage.login(tenantAccount.phone, tenantAccount.password);
      const responsePromise = profileResponse(page);
      await profilePage.openProfile();
      const response = await responsePromise;
      expect(response.status()).toBe(200);
    });

    await test.step('操作：退出登录', async () => {
      const logoutResponsePromise = page.waitForResponse((response) =>
        new URL(response.url()).pathname === '/tenant-app/auth/logout' &&
        response.request().method() === 'POST');
      await profilePage.logout();
      const logoutResponse = await logoutResponsePromise;
      expect(logoutResponse.status()).toBe(200);
    });

    await test.step('验证：直接访问个人中心仍被重定向到登录页', async () => {
      await page.goto(profilePage.profileUrl());
      await expect(page).toHaveURL(profilePage.loginUrl());
      await expect(page.getByRole('heading', { name: '租客登录' })).toBeVisible();
    });
  });
});
