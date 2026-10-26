import { type Page, expect } from '@playwright/test';

/** 租客首页公告详情的登录、入口和页面导航。 */
export class TenantNoticePage {
  private readonly baseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(phone: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /账号/ }).fill(phone);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/home`);
  }

  async openNoticeFromHome(title: string) {
    await this.page.getByText(title, { exact: true }).click();
    await expect(this.page).toHaveURL(/\/notices\/\d+$/);
  }

  async openNotice(noticeId: number) {
    await this.page.goto(`${this.baseUrl}/notices/${noticeId}`);
  }

  async goBack() {
    // 导航栏返回按钮没有可访问名称；使用 UI 组件自身的稳定 class 定位。
    await this.page.locator('.adm-nav-bar-back').click();
  }

  homeUrl() {
    return `${this.baseUrl}/home`;
  }
}
