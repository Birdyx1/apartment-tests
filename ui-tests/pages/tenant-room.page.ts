import { expect, type Locator, type Page } from '@playwright/test';

/** 租客 H5“我的房间”页面的登录、导航与房间/租约字段定位。 */
export class TenantRoomPage {
  private readonly baseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(phone: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /账号/ }).fill(phone);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/home`);
  }

  async openRoom() {
    await this.page.goto(`${this.baseUrl}/room`);
    await expect(this.page).toHaveURL(`${this.baseUrl}/room`);
  }

  roomRow(label: string): Locator {
    return this.page.locator('.kv-row').filter({
      has: this.page.locator('.kv-label', { hasText: label }),
    });
  }
}
