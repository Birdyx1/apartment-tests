import { expect, type Locator, type Page } from '@playwright/test';

/** 维修工 H5“我的工单”页与登录页的浏览器操作。 */
export class WorkerMyOrdersPage {
  private readonly baseUrl = (process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async gotoMyOrders() {
    await this.page.goto(`${this.baseUrl}/mine`);
  }

  async openMyOrders() {
    await this.gotoMyOrders();
    await expect(this.page.getByRole('heading', { name: '我的工单' })).toBeVisible();
  }

  async login(username: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /用户名/ }).fill(username);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/todo`);
    await this.openMyOrders();
  }

  tab(name: '处理中' | '已完成' | '全部'): Locator {
    return this.page.getByRole('tab', { name });
  }

  emptyState(): Locator {
    return this.page.getByText('暂无工单', { exact: true });
  }
}
