import { expect, test } from './tenant-maintenance-list-data.fixture';
import { TenantMaintenanceListPage } from '../pages/tenant-maintenance-list.page';

function maintenanceListResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/maintenance/list' &&
    response.request().method() === 'GET');
}

test.describe('租客 H5 维修工单列表', () => {
  test('TML-001: 租客查看自己的待处理工单', async ({ page, tenantAccount, tenantMaintenanceOrder }) => {
    const maintenancePage = new TenantMaintenanceListPage(page);
    await test.step('准备：登录有在住记录和专属工单的租客', async () => {
      await maintenancePage.login(tenantAccount.phone, tenantAccount.password);
    });

    const listResponsePromise = maintenanceListResponse(page);
    await maintenancePage.openList();

    await test.step('验证：页面和列表接口展示工单内容及状态', async () => {
      const response = await listResponsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      const order = body.data.find((item: { id: number }) => item.id === tenantMaintenanceOrder.id);
      expect(order).toMatchObject({
        tenantId: tenantAccount.id,
        title: tenantMaintenanceOrder.title,
        description: tenantMaintenanceOrder.description,
        urgency: 2,
        status: 0,
        roomNo: tenantMaintenanceOrder.roomNo,
      });

      const card = maintenancePage.orderCard(tenantMaintenanceOrder.title);
      await expect(page.getByRole('heading', { name: '维修工单' })).toBeVisible();
      await expect(card).toBeVisible();
      await expect(card).toContainText(tenantMaintenanceOrder.description);
      await expect(card).toContainText(tenantMaintenanceOrder.roomNo);
      await expect(card).toContainText('紧急');
      await expect(card).toContainText('待处理');
      await expect(card.getByRole('button', { name: '取消' })).toBeVisible();
      await expect(page.getByText('暂无工单', { exact: true })).toHaveCount(0);
    });
  });

  test('TML-002: 无工单时显示空状态', async ({ page, tenantAccount }) => {
    const maintenancePage = new TenantMaintenanceListPage(page);
    await test.step('准备：登录没有入住和工单的新租客', async () => {
      await maintenancePage.login(tenantAccount.phone, tenantAccount.password);
    });

    const listResponsePromise = maintenanceListResponse(page);
    await maintenancePage.openList();

    await test.step('验证：接口返回空数组且页面显示空状态', async () => {
      const response = await listResponsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      expect(body.data).toEqual([]);
      await expect(page.getByText('暂无工单', { exact: true })).toBeVisible();
      await expect(page.getByRole('heading', { name: '维修工单' })).toBeVisible();
      await expect(page.getByRole('button', { name: '+' })).toBeVisible();
    });
  });
});
