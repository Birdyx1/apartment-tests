import { createAdminApi } from './worker-account.fixture';
import { expect, test } from './worker-assigned-order.fixture';
import { WorkerOrderDetailPage } from '../pages/worker-order-detail.page';

test.describe('维修工端已派工单接单状态流转', () => {
  test.beforeEach(async ({ page, workerAccount, assignedWorkOrder }) => {
    const detailPage = new WorkerOrderDetailPage(page);
    await detailPage.login(workerAccount.username, workerAccount.password);
    await detailPage.openOrder(assignedWorkOrder.title);
  });

  test('WA-001: 取消接单确认后工单保持待处理', async ({ page, workerAccount, assignedWorkOrder }) => {
    const detailPage = new WorkerOrderDetailPage(page);
    await test.step('准备：打开派给当前维修工的专属待处理工单', async () => {
      await expect(detailPage.detailRow('状态')).toContainText('待处理');
      await expect(detailPage.detailRow('指派')).toContainText(workerAccount.username);
    });

    await test.step('操作：打开接单确认框并取消', async () => {
      const dialog = await detailPage.openAcceptConfirmation();
      await expect(dialog).toContainText('确认接此派单？');
      await detailPage.cancelAccept();
    });

    await test.step('验证：页面和后端工单仍处于待处理状态', async () => {
      await expect(page.getByRole('dialog')).toHaveCount(0);
      await expect(detailPage.detailRow('状态')).toContainText('待处理');
      await expect(detailPage.detailRow('指派')).toContainText(workerAccount.username);
      await expect(page.getByRole('button', { name: '接单' })).toBeVisible();

      const api = await createAdminApi();
      try {
        const response = await api.get(`/maintenance-order/${assignedWorkOrder.id}`);
        const body = await response.json();
        expect(response.status()).toBe(200);
        expect(body.code).toBe(200);
        expect(body.data.status).toBe(0);
        expect(body.data.assigneeId).toBe(workerAccount.id);
        expect(body.data.handlerId).toBeFalsy();
      } finally {
        await api.dispose();
      }
    });
  });

  test('WA-002: 确认接单后工单进入处理中', async ({ page, workerAccount, assignedWorkOrder }) => {
    const detailPage = new WorkerOrderDetailPage(page);
    await test.step('准备：打开派给当前维修工的专属待处理工单', async () => {
      await expect(detailPage.detailRow('状态')).toContainText('待处理');
      await expect(detailPage.detailRow('指派')).toContainText(workerAccount.username);
    });

    const acceptResponse = await test.step('操作：确认接下管理员派发的工单', async () => {
      const dialog = await detailPage.openAcceptConfirmation();
      await expect(dialog).toContainText('确认接此派单？');
      const responsePromise = page.waitForResponse((response) =>
        new URL(response.url()).pathname === `/worker-app/maintenance/${assignedWorkOrder.id}/accept` &&
        response.request().method() === 'PUT');
      await detailPage.confirmAccept();
      return responsePromise;
    });

    await test.step('验证：请求成功，页面和后端均记录当前维修工开始处理', async () => {
      expect(acceptResponse.status()).toBe(200);
      const acceptBody = await acceptResponse.json();
      expect(acceptBody.code).toBe(200);
      expect(acceptBody.data).toBe(true);

      await expect(page.getByRole('dialog')).toHaveCount(0);
      await expect(detailPage.detailRow('状态')).toContainText('处理中');
      await expect(detailPage.detailRow('指派')).toContainText(workerAccount.username);
      await expect(page.getByRole('button', { name: '完成工单' })).toBeVisible();

      const api = await createAdminApi();
      try {
        const response = await api.get(`/maintenance-order/${assignedWorkOrder.id}`);
        const body = await response.json();
        expect(response.status()).toBe(200);
        expect(body.code).toBe(200);
        expect(body.data.status).toBe(1);
        expect(body.data.assigneeId).toBe(workerAccount.id);
        expect(body.data.handlerId).toBe(workerAccount.id);
      } finally {
        await api.dispose();
      }
    });
  });
});
