import { expect, type Locator, type Page } from '@playwright/test';

/** 租客 H5 首页登录、当前房间卡和快捷入口。 */
export class TenantHomePage {
  private readonly baseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(phone: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /账号/ }).fill(phone);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/home`);
    await expect(this.page.getByRole('heading')).toContainText('你好，');
  }

  currentRoomCard(): Locator {
    return this.page.locator('.apple-card').filter({ hasText: '当前房间' });
  }
}
