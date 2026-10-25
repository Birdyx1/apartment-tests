import { expect, type Locator, type Page } from '@playwright/test';

/** 维修工 H5“待抢工单”页。页面只读，不主动抢单。 */
export class WorkerTodoPage {
  private readonly baseUrl = (process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async openTodo() {
    await this.page.goto(`${this.baseUrl}/todo`);
    await expect(this.page.getByRole('heading', { name: '待抢工单' })).toBeVisible();
  }

  async login(username: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /用户名/ }).fill(username);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/todo`);
    await expect(this.page.getByRole('heading', { name: '待抢工单' })).toBeVisible();
  }

  emptyState(): Locator {
    return this.page.getByText('暂无可抢工单', { exact: true });
  }

  orderCards(): Locator {
    // 当前卡片没有 testId，按页面语义类名统计列表项并核对其标题。
    return this.page.locator('.apple-card');
  }
}
