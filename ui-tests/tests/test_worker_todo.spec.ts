import { test, expect } from './worker-account.fixture';
import { WorkerTodoPage } from '../pages/worker-todo.page';

const workerBaseUrl = (process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '');

function todoResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === '/worker-app/maintenance/list' &&
      response.request().method() === 'GET' &&
      url.searchParams.get('tab') === 'todo' &&
      !url.searchParams.has('status');
  });
}

test.describe('维修工端待抢工单', () => {
  test('WT-001: 未登录访问待抢工单时跳转登录页', async ({ page }) => {
    await test.step('操作：未登录直接打开待抢工单页', async () => {
      await page.goto(`${workerBaseUrl}/todo`);
    });
    await test.step('验证：受保护路由跳转维修工登录页', async () => {
      await expect(page).toHaveURL(`${workerBaseUrl}/login`);
      await expect(page.getByRole('heading', { name: '维修工端' })).toBeVisible();
      await expect(page.getByRole('textbox', { name: /用户名/ })).toBeVisible();
      await expect(page.getByRole('textbox', { name: /密码/ })).toBeVisible();
    });
  });

  test('WT-002: 待抢工单列表正确加载', async ({ page, workerAccount }) => {
    const worker = new WorkerTodoPage(page);
    const responsePromise = todoResponse(page);
    await test.step('准备：创建的临时维修工登录并打开待抢列表', async () => {
      await worker.login(workerAccount.username, workerAccount.password);
    });

    await test.step('验证：列表请求成功，页面呈现本次响应中的记录或空状态', async () => {
      const response = await responsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      expect(Array.isArray(body.data)).toBe(true);
      await expect(page.getByRole('heading', { name: '待抢工单' })).toBeVisible();

      if (body.data.length === 0) {
        await expect(worker.emptyState()).toBeVisible();
        await expect(worker.orderCards()).toHaveCount(0);
      } else {
        await expect(worker.orderCards()).toHaveCount(body.data.length);
        for (let index = 0; index < body.data.length; index += 1) {
          await expect(worker.orderCards().nth(index).locator('.maintenance-title')).toHaveText(body.data[index].title);
        }
      }
    });
  });
});
