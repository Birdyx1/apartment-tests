import { expect, type Locator, type Page } from '@playwright/test';

/** 维修工 H5 个人中心及退出登录操作。 */
export class WorkerProfilePage {
  private readonly baseUrl = (process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(username: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /用户名/ }).fill(username);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/todo`);
  }

  async openFromNavigation() {
    await this.page.getByText('我的', { exact: true }).click();
    await expect(this.page).toHaveURL(`${this.baseUrl}/profile`);
  }

  profileRow(label: string): Locator {
    return this.page.locator('.kv-row').filter({
      has: this.page.locator('.kv-label', { hasText: label }),
    });
  }

  async logout() {
    await this.page.getByText('退出登录', { exact: true }).click();
    await expect(this.page).toHaveURL(`${this.baseUrl}/login`);
  }

  async openProtectedProfile() {
    await this.page.goto(`${this.baseUrl}/profile`);
  }
}
