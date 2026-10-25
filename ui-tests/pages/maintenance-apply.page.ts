import { expect, type Locator, type Page } from '@playwright/test';

/** 管理端维修工单申请页的列表和申请表单操作。 */
export class MaintenanceApplyPage {
  constructor(private readonly page: Page) {}

  async open() {
    await this.page.goto('/maintenance-order/apply');
    await expect(this.page.getByRole('columnheader', { name: '房间' })).toBeVisible();
  }

  async openForm() {
    await this.page.getByRole('button', { name: /申请维修工单/ }).click();
    await expect(this.dialog()).toBeVisible();
  }

  dialog(): Locator {
    return this.page.getByRole('dialog', { name: '申请维修工单' });
  }

  titleInput(): Locator {
    return this.dialog().getByRole('textbox', { name: '* 工单标题' });
  }

  urgencyInput(): Locator {
    return this.dialog().getByRole('combobox', { name: '* 紧急程度' });
  }

  urgencySelection(): Locator {
    return this.dialog().locator('.ant-form-item').filter({ hasText: '紧急程度' }).locator('.ant-select-selection-item');
  }

  async chooseUrgency(label: string) {
    await this.urgencyInput().click();
    await this.visibleUrgencyOption(label).click();
  }

  async submit() {
    await this.dialog().getByRole('button', { name: '确 定' }).click();
  }

  async closeForm() {
    await this.dialog().getByRole('button', { name: '取 消' }).click();
    await expect(this.dialog()).toBeHidden();
  }

  async refresh() {
    await this.page.getByRole('button', { name: /刷新/ }).click();
  }

  visibleUrgencyOption(label: string): Locator {
    // Ant Design 会保留隐藏的 option 节点，只从当前可见下拉层选择。
    return this.page.locator(`.ant-select-dropdown:visible .ant-select-item-option[title="${label}"]`);
  }
}
