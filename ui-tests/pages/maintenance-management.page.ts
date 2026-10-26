import { expect, type Locator, type Page } from '@playwright/test';

/** 管理端工单列表的导航、筛选和只读操作。 */
export class MaintenanceManagementPage {
  constructor(private readonly page: Page) {}

  async open() {
    await this.page.goto('/maintenance-order/manage');
    await expect(this.page.getByRole('columnheader', { name: '状态' })).toBeVisible();
  }

  statusFilter(): Locator {
    return this.page.getByRole('combobox', { name: '状态 :' });
  }

  urgencyFilter(): Locator {
    return this.page.getByRole('combobox', { name: '紧急程度 :' });
  }

  statusSelection(): Locator {
    return this.page.locator('.ant-form-item').filter({ hasText: '状态' }).locator('.ant-select-selection-item');
  }

  urgencySelection(): Locator {
    return this.page.locator('.ant-form-item').filter({ hasText: '紧急程度' }).locator('.ant-select-selection-item');
  }

  async chooseStatus(label: string) {
    await this.statusFilter().click();
    await this.visibleOption(label).click();
  }

  async chooseUrgency(label: string) {
    await this.urgencyFilter().click();
    await this.visibleOption(label).click();
  }

  async search() {
    await this.page.getByRole('button', { name: '搜索' }).click();
  }

  async reset() {
    await this.page.getByRole('button', { name: '重 置', exact: true }).click();
  }

  async refresh() {
    await this.page.getByRole('button', { name: /刷新/ }).click();
  }

  dataRows(): Locator {
    // Ant Design 的“暂无数据”占位行也有 row/cell role；仅统计真实记录行。
    return this.page.locator('.ant-table-tbody > tr.ant-table-row');
  }

  orderRow(title: string): Locator {
    return this.page.locator('.ant-table-tbody > tr.ant-table-row').filter({ hasText: title });
  }

  assignDialog(): Locator {
    return this.page.getByRole('dialog', { name: '派单' });
  }

  async assignOrder(title: string, workerUsername: string) {
    const row = this.orderRow(title);
    await row.getByRole('button', { name: '派单' }).click();
    const dialog = this.assignDialog();
    await dialog.getByRole('combobox', { name: '维修工' }).click();
    // Ant Design 的候选项渲染在 dialog 以外的 portal；限定可见弹层并核验选中值。
    const workerOption = this.page.locator('.ant-select-dropdown:visible .ant-select-item-option')
      .filter({ hasText: workerUsername });
    await workerOption.click();
    await expect(dialog.locator('.ant-select-selection-item')).toContainText(workerUsername);
    await dialog.getByRole('button', { name: '确 定' }).click();
  }

  private visibleOption(label: string): Locator {
    // Ant Design 可能保留隐藏 option；只在当前可见弹层中定位实际选项。
    return this.page.locator(`.ant-select-dropdown:visible .ant-select-item-option[title="${label}"]`);
  }
}
