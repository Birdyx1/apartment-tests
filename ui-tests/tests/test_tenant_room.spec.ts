import { expect, test } from './tenant-home-data.fixture';
import { TenantRoomPage } from '../pages/tenant-room.page';

function roomResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/my/room' &&
    response.request().method() === 'GET');
}

function historyResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/my/room/history' &&
    response.request().method() === 'GET');
}

test.describe('租客 H5 我的房间', () => {
  test('TR-001: 在住租客查看房间与租约详情', async ({ page, tenantAccount, tenantHome }) => {
    const roomPage = new TenantRoomPage(page);
    await test.step('准备：登录本用例专属在住租客并打开房间页', async () => {
      await roomPage.login(tenantAccount.phone, tenantAccount.password);
    });

    const currentResponsePromise = roomResponse(page);
    const historyResponsePromise = historyResponse(page);
    await roomPage.openRoom();

    await test.step('验证：页面信息与当前房间及租约接口一致', async () => {
      const [currentResponse, historyResponseValue] = await Promise.all([
        currentResponsePromise,
        historyResponsePromise,
      ]);
      expect(currentResponse.status()).toBe(200);
      const currentBody = await currentResponse.json();
      expect(currentBody.code).toBe(200);
      expect(currentBody.data.roomId).toBe(tenantHome.roomId);
      expect(currentBody.data.apartmentId).toBe(tenantHome.apartmentId);
      expect(currentBody.data.apartmentName).toBe(tenantHome.apartmentName);
      expect(currentBody.data.roomNo).toBe(tenantHome.roomNo);
      expect(currentBody.data.floor).toBe(tenantHome.floor);
      expect(currentBody.data.layout).toBe(tenantHome.layout);
      expect(Number(currentBody.data.area)).toBe(tenantHome.area);
      expect(currentBody.data.apartmentAddress).toBe(tenantHome.apartmentAddress);
      expect(currentBody.data.apartmentContact).toBe(tenantHome.apartmentContact);
      expect(currentBody.data.apartmentPhone).toBe(tenantHome.apartmentPhone);
      expect(currentBody.data.deposit).toBe(tenantHome.deposit);
      expect(currentBody.data.monthlyRent).toBe(tenantHome.monthlyRent);

      expect(historyResponseValue.status()).toBe(200);
      const historyBody = await historyResponseValue.json();
      expect(historyBody.code).toBe(200);
      expect(historyBody.data).toEqual([]);

      await expect(page.getByRole('heading', { name: '我的房间' })).toBeVisible();
      await expect(page.getByText(`${tenantHome.apartmentName} · ${tenantHome.roomNo}`, { exact: true })).toBeVisible();
      await expect(roomPage.roomRow('楼层')).toContainText(`${tenantHome.floor}层`);
      await expect(roomPage.roomRow('户型')).toContainText(tenantHome.layout);
      await expect(roomPage.roomRow('面积')).toContainText(`${tenantHome.area}㎡`);
      await expect(roomPage.roomRow('地址')).toContainText(tenantHome.apartmentAddress);
      await expect(roomPage.roomRow('联系人')).toContainText(tenantHome.apartmentContact);
      await expect(roomPage.roomRow('电话')).toContainText(tenantHome.apartmentPhone);
      await expect(roomPage.roomRow('入住时间')).toContainText(tenantHome.checkInTime.slice(0, 10));
      await expect(roomPage.roomRow('押金')).toContainText(`¥${tenantHome.deposit}`);
      await expect(roomPage.roomRow('月租')).toContainText(`¥${tenantHome.monthlyRent}`);
      await expect(page.getByText('暂无房间信息', { exact: true })).toHaveCount(0);
    });
  });

  test('TR-002: 无房间记录时显示空状态', async ({ page, tenantAccount }) => {
    const roomPage = new TenantRoomPage(page);
    await test.step('准备：登录没有入住记录的本用例专属租客', async () => {
      await roomPage.login(tenantAccount.phone, tenantAccount.password);
    });

    const currentResponsePromise = roomResponse(page);
    const historyResponsePromise = historyResponse(page);
    await roomPage.openRoom();

    await test.step('验证：后端无房间记录，页面显示空状态', async () => {
      const [currentResponse, historyResponseValue] = await Promise.all([
        currentResponsePromise,
        historyResponsePromise,
      ]);
      expect(currentResponse.status()).toBe(200);
      const currentBody = await currentResponse.json();
      expect(currentBody.code).toBe(500);
      expect(currentBody.message).toBe('当前没有在住记录');

      expect(historyResponseValue.status()).toBe(200);
      const historyBody = await historyResponseValue.json();
      expect(historyBody.code).toBe(200);
      expect(historyBody.data).toEqual([]);

      await expect(page.getByText('暂无房间信息', { exact: true })).toBeVisible();
      await expect(page.getByRole('heading', { name: '我的房间' })).toHaveCount(0);
    });
  });
});
