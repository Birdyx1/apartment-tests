import { expect, type Locator, type Page } from '@playwright/test';

/** 维修工 H5 待抢列表到工单详情的只读浏览。 */
export class WorkerOrderDetailPage {
  private readonly baseUrl = (process.env.WORKER_H5_URL ?? 'http://localhost:3002/worker-h5').replace(/\/$/, '');

  constructor(private readonly page: Page) {}

  async login(username: string, password: string) {
    await this.page.goto(`${this.baseUrl}/login`);
    await this.page.getByRole('textbox', { name: /用户名/ }).fill(username);
    await this.page.getByRole('textbox', { name: /密码/ }).fill(password);
    await this.page.getByRole('button', { name: '登录' }).click();
    await this.page.waitForURL(`${this.baseUrl}/todo`);
  }

  async openOrder(title: string) {
    await this.page.getByText(title, { exact: true }).click();
  }

  detailRow(label: string): Locator {
    // 详情字段没有独立 accessible name/testId，使用页面已有 kv-row/kv-label 结构。
    return this.page.locator('.kv-row').filter({ has: this.page.locator('.kv-label', { hasText: label }) });
  }

  async openGrabConfirmation() {
    await this.page.getByRole('button', { name: '抢单' }).click();
    return this.page.getByRole('dialog');
  }

  async cancelGrab() {
    await this.page.getByRole('dialog').getByRole('button', { name: '取消' }).click();
  }

  async confirmGrab() {
    await this.page.getByRole('dialog').getByRole('button', { name: '确定' }).click();
  }

  async openAcceptConfirmation() {
    await this.page.getByRole('button', { name: '接单' }).click();
    return this.page.getByRole('dialog');
  }

  async cancelAccept() {
    await this.page.getByRole('dialog').getByRole('button', { name: '取消' }).click();
  }

  async confirmAccept() {
    await this.page.getByRole('dialog').getByRole('button', { name: '确定' }).click();
  }

  async grabForCompletion() {
    await this.page.getByRole('button', { name: '抢单' }).click();
    await this.page.getByRole('dialog').getByRole('button', { name: '确定' }).click();
    await expect(this.detailRow('状态')).toContainText('处理中');
  }

  async openCompletionForm() {
    await this.page.getByRole('button', { name: '完成工单' }).click();
    await expect(this.page.getByPlaceholder('请填写处理结果（必填）')).toBeVisible();
  }

  async uploadCompletionImage(path: string) {
    const chooserPromise = this.page.waitForEvent('filechooser');
    await this.page.getByRole('button', { name: '上传' }).last().click();
    const chooser = await chooserPromise;
    await chooser.setFiles(path);
  }

  async backToList() {
    // 探索发现 Ant Design Mobile 返回控件没有可访问名称，使用其语义明确的返回类。
    await this.page.locator('.adm-nav-bar-back').click();
    await expect(this.page).toHaveURL(`${this.baseUrl}/todo`);
  }
}
