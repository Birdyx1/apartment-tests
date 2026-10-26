import { expect, type Page } from '@playwright/test';

/** 租客 H5“维修工单”列表页的登录与页面入口。 */
export class TenantMaintenanceListPage {
  private readonly baseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(phone: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /账号/ }).fill(phone);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/home`);
  }

  async openList() {
    await this.page.goto(`${this.baseUrl}/maintenance/list`);
    await expect(this.page).toHaveURL(`${this.baseUrl}/maintenance/list`);
  }

  orderCard(title: string) {
    return this.page.locator('.apple-card').filter({ hasText: title });
  }
}
