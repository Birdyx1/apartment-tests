import { type Locator, type Page, expect } from '@playwright/test';

/** 租客个人中心的导航、资料行和退出登录操作。 */
export class TenantProfilePage {
  private readonly baseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(phone: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /账号/ }).fill(phone);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/home`);
  }

  async openProfile() {
    await this.page.getByText('我的', { exact: true }).click();
    await expect(this.page).toHaveURL(`${this.baseUrl}/profile`);
  }

  async logout() {
    await this.page.getByText('退出登录', { exact: true }).click();
    await expect(this.page).toHaveURL(`${this.baseUrl}/login`);
  }

  async openEdit() {
    await this.page.getByText('编辑个人信息', { exact: true }).click();
    await expect(this.page.getByText('编辑个人信息', { exact: true })).toBeVisible();
  }

  async fillEditForm(profile: { name: string; phone: string; gender: '男' | '女' | '未知' }) {
    await this.page.getByRole('textbox', { name: /姓名/ }).fill(profile.name);
    await this.page.getByRole('textbox', { name: /手机号/ }).fill(profile.phone);
    await this.page.getByRole('option', { name: profile.gender, exact: true }).click();
  }

  async saveEdit() {
    await this.page.getByRole('button', { name: '保存' }).click();
  }

  infoRow(label: string): Locator {
    return this.page.locator('.kv-row').filter({
      has: this.page.locator('.kv-label', { hasText: label }),
    });
  }

  profileUrl() {
    return `${this.baseUrl}/profile`;
  }

  loginUrl() {
    return `${this.baseUrl}/login`;
  }
}
