import { expect, type Locator, type Page } from '@playwright/test';

export type ApartmentForm = {
  name: string;
  address: string;
  contactName: string;
  contactPhone: string;
  description: string;
};

/** 公寓列表页面的常用操作，统一维护稳定定位方式。 */
export class ApartmentListPage {
  constructor(private readonly page: Page) {}

  async open() {
    await this.page.goto('/apartment/list');
    await expect(this.page.getByRole('columnheader', { name: '名称' })).toBeVisible();
    await expect(this.page.getByRole('row').nth(1)).toBeVisible();
  }

  row(name: string): Locator {
    return this.page.getByRole('row').filter({ hasText: name });
  }

  async create(apartment: ApartmentForm) {
    await this.page.getByTestId('apartment-management-create-button').click();
    const dialog = this.page.getByRole('dialog', { name: '新增公寓' });
    await dialog.getByTestId('apartment-management-field-name').fill(apartment.name);
    await dialog.getByTestId('apartment-management-field-address').fill(apartment.address);
    await dialog.getByTestId('apartment-management-field-contact-name').fill(apartment.contactName);
    await dialog.getByTestId('apartment-management-field-contact-phone').fill(apartment.contactPhone);
    await dialog.getByTestId('apartment-management-field-description').fill(apartment.description);
    await dialog.getByTestId('apartment-management-modal-ok').click();
    await expect(this.row(apartment.name)).toBeVisible();
  }

  async searchByName(name: string) {
    await this.page.getByRole('textbox', { name: '名称 :' }).fill(name);
    await this.page.getByRole('button', { name: /搜索/ }).click();
    await expect(this.row(name)).toBeVisible();
  }

  async deleteByName(name: string) {
    await this.searchByName(name);
    const row = this.row(name);
    await row.getByTestId('apartment-management-delete-button').click();
    const dialog = this.page.getByRole('dialog', { name: '确认删除该公寓？' });
    await dialog.getByRole('button', { name: '确 定' }).click();
    await expect(this.row(name)).toHaveCount(0);
  }

  async cleanup(name: string) {
    // 用例断言失败时也尽量清理本用例创建的数据。
    await this.page.getByRole('button', { name: /重\s*置/ }).click();
    const row = this.row(name);
    if (await row.count()) {
      await this.deleteByName(name);
    }
  }
}
