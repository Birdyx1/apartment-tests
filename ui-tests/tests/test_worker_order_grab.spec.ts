import { createAdminApi } from './worker-account.fixture';
import { expect, test } from './worker-detail-data.fixture';
import { WorkerOrderDetailPage } from '../pages/worker-order-detail.page';

test.describe('维修工端抢单状态流转', () => {
  test.beforeEach(async ({ page, workerAccount, pendingWorkOrder }) => {
    const detailPage = new WorkerOrderDetailPage(page);
    await detailPage.login(workerAccount.username, workerAccount.password);
    await detailPage.openOrder(pendingWorkOrder.title);
  });

  test('WG-001: 取消确认后工单保持待抢状态', async ({ page, workerAccount, pendingWorkOrder }) => {
    const detailPage = new WorkerOrderDetailPage(page);
    await test.step('准备：登录专属维修工并打开本次待处理工单', async () => {
      await expect(detailPage.detailRow('状态')).toContainText('待处理');
    });

    await test.step('操作：打开抢单确认框并选择取消', async () => {
      const dialog = await detailPage.openGrabConfirmation();
      await expect(dialog).toContainText('确认抢此工单？');
      await detailPage.cancelGrab();
    });

    await test.step('验证：页面和后端状态仍为待抢', async () => {
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await expect(detailPage.detailRow('状态')).toContainText('待处理');
      await expect(detailPage.detailRow('指派')).toContainText('未派（可抢）');
      await expect(page.getByRole('button', { name: '抢单' })).toBeVisible();

      const adminApi = await createAdminApi();
      try {
        const response = await adminApi.get(`/maintenance-order/${pendingWorkOrder.id}`);
        const body = await response.json();
        expect(response.status()).toBe(200);
        expect(body.code).toBe(200);
        expect(body.data.status).toBe(0);
        expect(body.data.assigneeId).toBeFalsy();
      } finally {
        await adminApi.dispose();
      }
    });
  });

  test('WG-002: 确认抢单后工单进入处理中', async ({ page, workerAccount, pendingWorkOrder }) => {
    const detailPage = new WorkerOrderDetailPage(page);
    await test.step('准备：登录专属维修工并打开本次待处理工单', async () => {
      await expect(detailPage.detailRow('状态')).toContainText('待处理');
    });

    const grabResponse = await test.step('操作：在确认框中确认抢单', async () => {
      const dialog = await detailPage.openGrabConfirmation();
      await expect(dialog).toContainText('确认抢此工单？');
      const responsePromise = page.waitForResponse((response) =>
        new URL(response.url()).pathname === `/worker-app/maintenance/${pendingWorkOrder.id}/grab` &&
        response.request().method() === 'PUT');
      await detailPage.confirmGrab();
      return responsePromise;
    });

    await test.step('验证：页面和后端均记录当前维修工已抢单', async () => {
      expect(grabResponse.status()).toBe(200);
      const grabBody = await grabResponse.json();
      expect(grabBody.code).toBe(200);
      expect(grabBody.data).toBe(true);

      await expect(detailPage.detailRow('状态')).toContainText('处理中');
      await expect(detailPage.detailRow('指派')).toContainText(workerAccount.username);
      await expect(page.getByRole('button', { name: '完成工单' })).toBeVisible();

      const adminApi = await createAdminApi();
      try {
        const response = await adminApi.get(`/maintenance-order/${pendingWorkOrder.id}`);
        const body = await response.json();
        expect(response.status()).toBe(200);
        expect(body.code).toBe(200);
        expect(body.data.status).toBe(1);
        expect(body.data.assigneeId).toBe(workerAccount.id);
        expect(body.data.handlerId).toBe(workerAccount.id);
      } finally {
        await adminApi.dispose();
      }
    });
  });
});
