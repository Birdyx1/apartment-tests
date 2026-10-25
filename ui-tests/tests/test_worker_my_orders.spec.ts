import { test, expect } from './worker-account.fixture';
import { WorkerMyOrdersPage } from '../pages/worker-my-orders.page';

const workerBaseUrl = (process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '');

function ordersResponse(page: import('@playwright/test').Page, status?: string) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === '/worker-app/maintenance/list' &&
      response.request().method() === 'GET' &&
      url.searchParams.get('tab') === 'mine' &&
      (status === undefined ? !url.searchParams.has('status') : url.searchParams.get('status') === status);
  });
}

test.describe('维修工端我的工单', () => {
  test('WM-001: 未登录访问我的工单时跳转登录页', async ({ page }) => {
    const worker = new WorkerMyOrdersPage(page);
    await test.step('操作：未登录直接打开我的工单', async () => {
      await worker.gotoMyOrders();
    });
    await test.step('验证：受保护路由返回维修工登录页', async () => {
      await expect(page).toHaveURL(`${workerBaseUrl}/login`);
      await expect(page.getByRole('heading', { name: '维修工端' })).toBeVisible();
      await expect(page.getByRole('textbox', { name: /用户名/ })).toBeVisible();
      await expect(page.getByRole('textbox', { name: /密码/ })).toBeVisible();
    });
  });

  test('WM-002: 维修工默认查看处理中工单', async ({ page, workerAccount }) => {
    const worker = new WorkerMyOrdersPage(page);
    await test.step('准备：使用本用例专属的临时维修工登录', async () => {
      await worker.login(workerAccount.username, workerAccount.password);
    });
    await test.step('验证：处理中为默认筛选并加载本人空列表', async () => {
      await expect(worker.tab('处理中')).toHaveAttribute('aria-selected', 'true');
      await expect(worker.emptyState()).toBeVisible();
    });
  });

  test('WM-003: 查看已完成工单', async ({ page, workerAccount }) => {
    const worker = new WorkerMyOrdersPage(page);
    await worker.login(workerAccount.username, workerAccount.password);
    await test.step('操作：选择已完成', async () => {
      const response = ordersResponse(page, '2');
      await worker.tab('已完成').click();
      expect((await response).status()).toBe(200);
    });
    await test.step('验证：已完成筛选选中且新账号没有历史工单', async () => {
      await expect(worker.tab('已完成')).toHaveAttribute('aria-selected', 'true');
      await expect(worker.emptyState()).toBeVisible();
    });
  });

  test('WM-004: 查看全部本人工单', async ({ page, workerAccount }) => {
    const worker = new WorkerMyOrdersPage(page);
    await worker.login(workerAccount.username, workerAccount.password);
    await test.step('操作：选择全部', async () => {
      const response = ordersResponse(page);
      await worker.tab('全部').click();
      expect((await response).status()).toBe(200);
    });
    await test.step('验证：全部筛选选中且请求不带状态参数', async () => {
      await expect(worker.tab('全部')).toHaveAttribute('aria-selected', 'true');
      await expect(worker.emptyState()).toBeVisible();
    });
  });
});
