import { expect, test } from './tenant-home-data.fixture';
import { TenantHomePage } from '../pages/tenant-home.page';
import { createAdminApi } from './worker-account.fixture';

const tenantBaseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

function currentRoomResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/my/room' &&
    response.request().method() === 'GET');
}

function rentResponse(page: import('@playwright/test').Page, pathname: string) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === pathname && response.request().method() === 'GET');
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

  test('TH-003: 收到催租消息后首页房租入口显示提醒', async ({ page, tenantAccount, tenantHome }) => {
    const homePage = new TenantHomePage(page);
    const initialBillsPromise = rentResponse(page, '/tenant-app/rent/bills');
    let targetBillId = 0;

    await test.step('准备：登录有待缴账单的专属租客', async () => {
      await homePage.login(tenantAccount.phone, tenantAccount.password);
      const initialBills = await initialBillsPromise;
      expect(initialBills.status()).toBe(200);
      const body = await initialBills.json();
      expect(body.code).toBe(200);
      const bill = body.data.find((item: { leaseId: number }) => item.leaseId === tenantHome.leaseId);
      expect(bill).toBeTruthy();
      targetBillId = bill.id;
      expect([0, 2]).toContain(bill.status);

      const adminApi = await createAdminApi();
      try {
        const remindResponse = await adminApi.post(`/rent/bills/${bill.id}/remind`);
        expect(remindResponse.status()).toBe(200);
        const remindBody = await remindResponse.json();
        expect(remindBody.code).toBe(200);
      } finally {
        await adminApi.dispose();
      }
    });

    await test.step('操作：刷新首页重新读取催租消息', async () => {
      const messagesPromise = rentResponse(page, '/tenant-app/rent/messages');
      const billsPromise = rentResponse(page, '/tenant-app/rent/bills');
      await page.reload();
      const [messagesResponse, billsResponse] = await Promise.all([messagesPromise, billsPromise]);
      expect(messagesResponse.status()).toBe(200);
      expect(billsResponse.status()).toBe(200);
      const messagesBody = await messagesResponse.json();
      const billsBody = await billsResponse.json();
      expect(messagesBody.code).toBe(200);
      expect(messagesBody.data.unreadCount).toBeGreaterThan(0);
      expect(messagesBody.data.records).toContainEqual(expect.objectContaining({
        billId: targetBillId,
        readFlag: 0,
      }));
      const bill = billsBody.data.find((item: { leaseId: number }) => item.leaseId === tenantHome.leaseId);
      expect(bill.status).not.toBe(1);
    });

    await test.step('验证：首页房租账单快捷入口显示提醒标记', async () => {
      const rentEntry = page.locator('.quick-item').filter({ hasText: '房租账单' });
      await expect(rentEntry).toBeVisible();
      await expect(rentEntry.locator('.quick-badge')).toBeVisible();
    });
  });
});
