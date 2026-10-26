import { expect, test } from './worker-detail-data.fixture';
import { createAdminApi } from './worker-account.fixture';
import { MaintenanceManagementPage } from '../pages/maintenance-management.page';

test.describe('管理员工单派单 UI', () => {
  test('MM-006: 管理员为待处理工单派单', async ({ page, pendingWorkOrder, workerAccount }) => {
    const managementPage = new MaintenanceManagementPage(page);

    await test.step('准备：打开含本用例专属待处理工单的管理列表', async () => {
      await managementPage.open();
      await expect(managementPage.orderRow(pendingWorkOrder.title)).toBeVisible();
      await expect(managementPage.orderRow(pendingWorkOrder.title)).toContainText('待处理');
      await expect(managementPage.orderRow(pendingWorkOrder.title)).toContainText('未派');
    });

    await test.step('操作：选择本用例临时维修工并确认派单', async () => {
      const assignResponsePromise = page.waitForResponse((response) =>
        new URL(response.url()).pathname === `/maintenance-order/${pendingWorkOrder.id}/assign` &&
        response.request().method() === 'PUT');
      await managementPage.assignOrder(pendingWorkOrder.title, workerAccount.username);
      const assignResponse = await assignResponsePromise;
      expect(assignResponse.status()).toBe(200);
      const assignBody = await assignResponse.json();
      expect(assignBody.code).toBe(200);
      expect(assignBody.data).toBe(true);
    });

    await test.step('验证：列表和管理员接口显示派单人，工单仍待处理', async () => {
      const row = managementPage.orderRow(pendingWorkOrder.title);
      await expect(row).toContainText(workerAccount.username);
      await expect(row).toContainText('待处理');

      const api = await createAdminApi();
      try {
        const detailResponse = await api.get(`/maintenance-order/${pendingWorkOrder.id}`);
        expect(detailResponse.status()).toBe(200);
        const detailBody = await detailResponse.json();
        expect(detailBody.code).toBe(200);
        expect(detailBody.data).toMatchObject({
          status: 0,
          assigneeId: workerAccount.id,
        });
      } finally {
        await api.dispose();
      }
    });
  });
});
