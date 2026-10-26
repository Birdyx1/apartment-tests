import { expect, test } from './tenant-home-data.fixture';
import { TenantHomePage } from '../pages/tenant-home.page';

const tenantBaseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

function currentRoomResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/my/room' &&
    response.request().method() === 'GET');
}

test.describe('租客 H5 首页', () => {
  test('TH-001: 首页展示当前租客和房间信息', async ({ page, tenantAccount, tenantHome }) => {
    const homePage = new TenantHomePage(page);
    const roomResponse = currentRoomResponse(page);
    await test.step('准备：登录有有效入住记录的本用例专属租客', async () => {
      await homePage.login(tenantAccount.phone, tenantAccount.password);
    });

    await test.step('验证：欢迎语、房间卡和接口数据一致', async () => {
      const response = await roomResponse;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      expect(body.data.roomId).toBe(tenantHome.roomId);
      expect(body.data.apartmentName).toBe(tenantHome.apartmentName);
      expect(body.data.roomNo).toBe(tenantHome.roomNo);
      expect(body.data.layout).toBe(tenantHome.layout);
      expect(body.data.area).toBe(tenantHome.area);
      expect(body.data.floor).toBe(tenantHome.floor);

      await expect(page.getByRole('heading', { name: `你好，${tenantAccount.name}` })).toBeVisible();
      const roomCard = homePage.currentRoomCard();
      await expect(roomCard).toContainText(`${tenantHome.apartmentName} ${tenantHome.roomNo}`);
      await expect(roomCard).toContainText(`${tenantHome.layout} · ${tenantHome.area}㎡ · ${tenantHome.floor}层`);
      await expect(page.getByText('申请维修', { exact: true })).toBeVisible();
      await expect(page.getByText('我的工单', { exact: true })).toBeVisible();
      await expect(page.getByText('房租账单', { exact: true })).toBeVisible();
    });
  });

  test('TH-002: 无当前入住时首页仍显示欢迎语和快捷入口', async ({ page, tenantAccount }) => {
    const homePage = new TenantHomePage(page);
    const roomResponse = currentRoomResponse(page);
    await test.step('准备：登录没有入住记录的本用例专属租客', async () => {
      await homePage.login(tenantAccount.phone, tenantAccount.password);
    });

    await test.step('验证：房间接口无可展示数据时首页正常呈现', async () => {
      const response = await roomResponse;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(500);
      expect(body.message).toBe('当前没有在住记录');
      await expect(page.getByRole('heading', { name: `你好，${tenantAccount.name}` })).toBeVisible();
      await expect(homePage.currentRoomCard()).toHaveCount(0);
      await expect(page.getByText('申请维修', { exact: true })).toBeVisible();
      await expect(page.getByText('房租账单', { exact: true })).toBeVisible();
    });
  });
});
