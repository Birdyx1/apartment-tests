import { expect, type Locator, type Page } from '@playwright/test';

/** 租客 H5维修工单详情页的登录、路由、详情字段和取消操作。 */
export class TenantMaintenanceDetailPage {
  private readonly baseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(phone: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /账号/ }).fill(phone);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/home`);
  }

  async openDetail(orderId: number) {
    await this.page.goto(`${this.baseUrl}/maintenance/detail/${orderId}`);
  }

  async cancel() {
    await this.page.getByRole('button', { name: '取消工单' }).click();
  }

  infoRow(label: string): Locator {
    return this.page.locator('.kv-row').filter({
      has: this.page.locator('.kv-label', { hasText: label }),
    });
  }

  async expectListPage() {
    await expect(this.page).toHaveURL(`${this.baseUrl}/maintenance/list`);
  }
}
