import { test, expect } from './worker-detail-data.fixture';
import { WorkerOrderDetailPage } from '../pages/worker-order-detail.page';

const workerBaseUrl = (process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '');

test.describe('维修工端工单详情', () => {
  test('WD-001: 维修工从待抢列表打开工单详情', async ({ page, workerAccount, pendingWorkOrder }) => {
    const detailPage = new WorkerOrderDetailPage(page);
    await test.step('准备：登录本用例专属维修工', async () => {
      await detailPage.login(workerAccount.username, workerAccount.password);
    });

    await test.step('操作：从待抢列表打开本次创建的唯一工单', async () => {
      const response = page.waitForResponse((candidate) => {
        const url = new URL(candidate.url());
        return url.pathname === `/worker-app/maintenance/${pendingWorkOrder.id}` &&
          candidate.request().method() === 'GET';
      });
      await detailPage.openOrder(pendingWorkOrder.title);
      expect(page.url()).toBe(`${workerBaseUrl}/detail/${pendingWorkOrder.id}`);
      expect((await response).status()).toBe(200);
    });

    await test.step('验证：详情字段与本次测试数据一致，抢单按钮仅展示不点击', async () => {
      await expect(page.getByText(pendingWorkOrder.title, { exact: true })).toBeVisible();
      await expect(detailPage.detailRow('房间')).toContainText(`${pendingWorkOrder.apartmentName} · ${pendingWorkOrder.roomNo}`);
      await expect(detailPage.detailRow('租客')).toContainText(pendingWorkOrder.tenantName);
      await expect(detailPage.detailRow('紧急')).toContainText('紧急');
      await expect(detailPage.detailRow('状态')).toContainText('待处理');
      await expect(detailPage.detailRow('指派')).toContainText('未派（可抢）');
      await expect(detailPage.detailRow('描述')).toContainText(pendingWorkOrder.description);
      await expect(page.getByRole('button', { name: '抢单' })).toBeVisible();
    });

    await test.step('验证：返回操作回到待抢列表', async () => {
      await detailPage.backToList();
      await expect(page.getByText(pendingWorkOrder.title, { exact: true })).toBeVisible();
    });
  });
});
