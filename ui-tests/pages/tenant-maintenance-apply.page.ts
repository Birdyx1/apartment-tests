import { expect, type Page } from '@playwright/test';

/** 租客 H5“申请维修”表单的登录、输入和提交操作。 */
export class TenantMaintenanceApplyPage {
  private readonly baseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(phone: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /账号/ }).fill(phone);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/home`);
  }

  async openApply() {
    await this.page.goto(`${this.baseUrl}/maintenance/apply`);
    await expect(this.page).toHaveURL(`${this.baseUrl}/maintenance/apply`);
  }

  async fillRequest(title: string, description: string) {
    await this.page.getByRole('textbox', { name: /工单标题/ }).fill(title);
    await this.page.getByRole('textbox', { name: '问题描述' }).fill(description);
  }

  async selectUrgency(label: '普通' | '紧急' | '非常紧急') {
    await this.page.getByRole('option', { name: label, exact: true }).click();
  }

  async submit() {
    await this.page.getByRole('button', { name: '提交申请' }).click();
  }
}
