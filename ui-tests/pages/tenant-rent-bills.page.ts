import { expect, type Locator, type Page } from '@playwright/test';

/** 租客 H5账单列表与详情页的登录、导航和账单定位。 */
export class TenantRentBillsPage {
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
    await this.page.goto(`${this.baseUrl}/rent/list`);
    await expect(this.page).toHaveURL(`${this.baseUrl}/rent/list`);
  }

  async openDetail(billId: number) {
    await this.page.goto(`${this.baseUrl}/rent/detail/${billId}`);
    await expect(this.page).toHaveURL(`${this.baseUrl}/rent/detail/${billId}`);
  }

  billCard(month: string, amount: number): Locator {
    return this.page.locator('.apple-card').filter({ hasText: `${month} 房租 · ¥${amount}` });
  }

  detailRow(label: string): Locator {
    return this.page.locator('.kv-row').filter({
      has: this.page.locator('.kv-label', { hasText: label }),
    });
  }
}
