import { createAdminApi } from './worker-account.fixture';
import { expect, test } from './tenant-maintenance-detail-data.fixture';
import { TenantMaintenanceDetailPage } from '../pages/tenant-maintenance-detail.page';

function orderDetailResponse(page: import('@playwright/test').Page, orderId: number) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === `/tenant-app/maintenance/${orderId}` &&
    response.request().method() === 'GET');
}

test.describe('租客 H5 工单详情', () => {
  test('TMD-001: 租客查看本人待处理工单详情', async ({ page, tenantAccount, tenantMaintenanceOrder }) => {
    const detailPage = new TenantMaintenanceDetailPage(page);
    await test.step('准备：登录工单所属租客', async () => {
      await detailPage.login(tenantAccount.phone, tenantAccount.password);
    });

    const responsePromise = orderDetailResponse(page, tenantMaintenanceOrder.id);
    await detailPage.openDetail(tenantMaintenanceOrder.id);

    await test.step('验证：接口数据、页面详情及创建处理记录一致', async () => {
      const response = await responsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      expect(body.data).toMatchObject({
        id: tenantMaintenanceOrder.id,
        tenantId: tenantAccount.id,
        title: tenantMaintenanceOrder.title,
        description: tenantMaintenanceOrder.description,
        urgency: tenantMaintenanceOrder.urgency,
        status: tenantMaintenanceOrder.status,
      });
      expect(body.data.logs).toEqual(expect.arrayContaining([
        expect.objectContaining({ action: 'create', toStatus: 0 }),
      ]));

      await expect(page.getByText('工单详情', { exact: true })).toBeVisible();
      await expect(page.getByText(tenantMaintenanceOrder.title, { exact: true })).toBeVisible();
      await expect(detailPage.infoRow('状态')).toContainText('待处理');
      await expect(detailPage.infoRow('紧急程度')).toContainText('紧急');
      await expect(detailPage.infoRow('描述')).toContainText(tenantMaintenanceOrder.description);
      await expect(detailPage.infoRow('申请时间')).toContainText(body.data.createTime);
      await expect(page.getByText('处理记录', { exact: true })).toBeVisible();
      const logItems = page.locator('.log-item');
      await expect(logItems).toHaveCount(body.data.logs.length);
      await expect(logItems.first()).toContainText('create');
      await expect(page.getByRole('button', { name: '取消工单' })).toBeVisible();
    });
  });

  test('TMD-002: 租客不能查看他人工单', async ({ page, otherTenantAccount, tenantMaintenanceOrder }) => {
    const detailPage = new TenantMaintenanceDetailPage(page);
    await test.step('准备：使用另一个独立租客账号登录', async () => {
      await detailPage.login(otherTenantAccount.phone, otherTenantAccount.password);
    });

    const responsePromise = orderDetailResponse(page, tenantMaintenanceOrder.id);
    await detailPage.openDetail(tenantMaintenanceOrder.id);

    await test.step('验证：越权接口拒绝访问且页面返回工单列表', async () => {
      const response = await responsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(403);
      expect(body.message).toBe('无权访问该工单');
      await detailPage.expectListPage();
      await expect(page.getByText(tenantMaintenanceOrder.title, { exact: true })).toHaveCount(0);
    });
  });

  test('TMD-003: 租客取消本人待处理工单', async ({ page, tenantAccount, tenantMaintenanceOrder }) => {
    const detailPage = new TenantMaintenanceDetailPage(page);
    await detailPage.login(tenantAccount.phone, tenantAccount.password);
    const detailResponsePromise = orderDetailResponse(page, tenantMaintenanceOrder.id);
    await detailPage.openDetail(tenantMaintenanceOrder.id);
    const detailResponse = await detailResponsePromise;
    expect(detailResponse.status()).toBe(200);
    expect((await detailResponse.json()).code).toBe(200);

    const cancelResponsePromise = page.waitForResponse((response) =>
      new URL(response.url()).pathname === `/tenant-app/maintenance/${tenantMaintenanceOrder.id}/cancel` &&
      response.request().method() === 'PUT');
    await detailPage.cancel();

    await test.step('验证：取消成功返回列表且后端状态变为已取消', async () => {
      const cancelResponse = await cancelResponsePromise;
      expect(cancelResponse.status()).toBe(200);
      const cancelBody = await cancelResponse.json();
      expect(cancelBody.code).toBe(200);
      expect(cancelBody.data).toBe(true);
      await detailPage.expectListPage();

      const adminApi = await createAdminApi();
      try {
        const detail = await adminApi.get(`/maintenance-order/${tenantMaintenanceOrder.id}`);
        const detailBody = await detail.json();
        expect(detail.status()).toBe(200);
        expect(detailBody.code).toBe(200);
        expect(detailBody.data.status).toBe(3);
      } finally {
        await adminApi.dispose();
      }
    });
  });
});
