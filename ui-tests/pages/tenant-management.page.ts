import { expect, type Locator, type Page } from '@playwright/test';

export type TenantForm = {
  name: string;
  gender: '男' | '女';
  phone: string;
  idCard: string;
  remark: string;
};

/** 管理端租客列表的表单、搜索和清理操作。 */
export class TenantManagementPage {
  constructor(private readonly page: Page) {}

  async open() {
    await this.page.goto('/tenants');
    await expect(this.page.getByRole('columnheader', { name: '姓名' })).toBeVisible();
  }

  row(name: string): Locator {
    return this.page.getByRole('row').filter({ hasText: name });
  }

  async create(tenant: TenantForm) {
    await this.page.getByRole('button', { name: /新增租客/ }).click();
    const dialog = this.page.getByRole('dialog', { name: '新增租客' });
    await this.fillForm(dialog, tenant);
    await dialog.getByRole('button', { name: /确\s*定/ }).click();
    await expect(this.page.getByText('创建成功', { exact: true })).toBeVisible();
    await expect(this.row(tenant.name)).toBeVisible();
  }

  async search(name: string) {
    await this.page.getByRole('textbox', { name: '姓名 :' }).fill(name);
    await this.page.getByRole('button', { name: /搜索/ }).click();
    await expect(this.row(name)).toBeVisible();
  }

  async edit(name: string, updatedName: string, gender: '男' | '女') {
    const row = this.row(name);
    await expect(row).toBeVisible();
    await row.getByRole('button', { name: /编辑/ }).click();

    const dialog = this.page.getByRole('dialog', { name: '编辑租客' });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('textbox', { name: '* 姓名' })).toHaveValue(name);
    await dialog.getByRole('textbox', { name: '* 姓名' }).fill(updatedName);
    await this.selectGender(dialog, gender);
    await dialog.getByRole('button', { name: /确\s*定/ }).click();
    await expect(this.page.getByText('更新成功', { exact: true })).toBeVisible();
    await expect(this.row(updatedName)).toBeVisible();
  }

  async deleteByName(name: string) {
    await this.search(name);
    const row = this.row(name);
    await row.getByRole('button', { name: /删除/ }).click();
    const confirm = this.page.getByRole('dialog', { name: '确认删除该租客？' });
    await confirm.getByRole('button', { name: /确\s*定/ }).click();
    await expect(this.page.getByText('删除成功', { exact: true })).toBeVisible();
    await expect(row).toHaveCount(0);
  }

  async cleanup(...names: string[]) {
    for (const name of names) {
      await this.open();
      await this.page.getByRole('textbox', { name: '姓名 :' }).fill(name);
      await this.page.getByRole('button', { name: /搜索/ }).click();
      const row = this.row(name);
      if (await row.count()) {
        await row.getByRole('button', { name: /删除/ }).click();
        const confirm = this.page.getByRole('dialog', { name: '确认删除该租客？' });
        await confirm.getByRole('button', { name: /确\s*定/ }).click();
        await expect(row).toHaveCount(0);
      }
    }
  }

  private async fillForm(dialog: Locator, tenant: TenantForm) {
    await dialog.getByRole('textbox', { name: '* 姓名' }).fill(tenant.name);
    await this.selectGender(dialog, tenant.gender);
    // 手机号和身份证输入框在页面快照中没有可访问名称；限定在对应表单项后使用 CSS + textbox。
    await this.formItem(dialog, '手机号').getByRole('textbox').fill(tenant.phone);
    await this.formItem(dialog, '身份证').getByRole('textbox').fill(tenant.idCard);
    await dialog.getByRole('textbox', { name: '备注' }).fill(tenant.remark);
  }

  private formItem(dialog: Locator, label: string): Locator {
    return dialog.locator('.ant-form-item').filter({ hasText: label });
  }

  private async selectGender(dialog: Locator, gender: '男' | '女') {
    // 编辑态 role=combobox 输入焦点点击会等待超时；CLI 探索确认点击可见的 Ant Design selector 容器可稳定展开。
    await dialog.locator('.ant-select-selector').click();
    const option = this.page.locator(`.ant-select-dropdown:visible .ant-select-item-option[title="${gender}"]`);
    await expect(option).toBeVisible();
    await option.click();
  }
}
