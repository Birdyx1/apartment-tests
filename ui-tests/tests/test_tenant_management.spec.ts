import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';
import { TenantManagementPage, type TenantForm } from '../pages/tenant-management.page';

function newTenant(): TenantForm {
  const suffix = randomUUID().replaceAll('-', '').slice(0, 14);
  const digits = randomUUID().replaceAll(/\D/g, '').padEnd(8, '7').slice(0, 8);
  return {
    name: `UI自动化租客-${suffix.slice(0, 8)}`,
    gender: '男',
    phone: `199${digits}`,
    idCard: `TEST${suffix}`,
    remark: 'Playwright 临时虚构资料',
  };
}

test.describe('管理员租客管理', () => {
  test.beforeEach(async ({ page }) => {
    await new TenantManagementPage(page).open();
  });

  test('TM-001: 租客列表展示主要列', async ({ page }) => {
    await test.step('验证：租客列表各列和新增入口可见', async () => {
      for (const name of ['姓名', '性别', '手机号', '身份证', '更新时间', '操作']) {
        await expect(page.getByRole('columnheader', { name })).toBeVisible();
      }
      await expect(page.getByRole('button', { name: /新增租客/ })).toBeVisible();
    });
  });

  test('TM-002: 新增租客成功且个人信息脱敏', async ({ page }) => {
    const tenants = new TenantManagementPage(page);
    const tenant = newTenant();
    try {
      await test.step('准备：填写并提交唯一虚构租客资料', async () => tenants.create(tenant));
      await test.step('验证：姓名、性别可见，手机号和证件号已脱敏', async () => {
        const row = tenants.row(tenant.name);
        await expect(row.getByRole('cell').nth(1)).toHaveText(tenant.gender);
        await expect(row.getByRole('cell').nth(2)).toHaveText(/^199\*{4}\d{4}$/);
        await expect(row.getByRole('cell').nth(3)).toContainText('****');
        await expect(row).not.toContainText(tenant.phone);
        await expect(row).not.toContainText(tenant.idCard);
      });
    } finally {
      await tenants.cleanup(tenant.name);
    }
  });

  test('TM-003: 按姓名搜索本次创建的租客', async ({ page }) => {
    const tenants = new TenantManagementPage(page);
    const tenant = newTenant();
    try {
      await test.step('准备：创建搜索目标', async () => tenants.create(tenant));
      await test.step('操作与验证：按姓名搜索并只显示目标记录', async () => {
        await tenants.search(tenant.name);
        await expect(page.getByRole('row').filter({ hasText: tenant.name })).toHaveCount(1);
      });
    } finally {
      await tenants.cleanup(tenant.name);
    }
  });

  test('TM-004: 重置租客搜索条件后恢复目标记录', async ({ page }) => {
    const tenants = new TenantManagementPage(page);
    const tenant = newTenant();
    try {
      await tenants.create(tenant);
      await tenants.search(tenant.name);
      // 精确区分筛选表单的“重 置”和每行的“重置密码”。
      await page.getByRole('button', { name: '重 置', exact: true }).click();

      await test.step('验证：姓名条件清空且本次数据回到默认列表', async () => {
        await expect(page.getByRole('textbox', { name: '姓名 :' })).toHaveValue('');
        await expect(tenants.row(tenant.name)).toBeVisible();
      });
    } finally {
      await tenants.cleanup(tenant.name);
    }
  });

  test('TM-005: 编辑租客姓名和性别成功', async ({ page }) => {
    const tenants = new TenantManagementPage(page);
    const tenant = newTenant();
    const updatedName = `${tenant.name}-已更新`;
    try {
      await tenants.create(tenant);
      await tenants.search(tenant.name);
      await test.step('操作：更新姓名和性别', async () => tenants.edit(tenant.name, updatedName, '女'));
      await test.step('验证：列表显示更新后的性别及脱敏证件信息', async () => {
        const row = tenants.row(updatedName);
        await expect(row.getByRole('cell').nth(1)).toHaveText('女');
        await expect(row.getByRole('cell').nth(3)).toContainText('****');
      });
    } finally {
      await tenants.cleanup(updatedName, tenant.name);
    }
  });

  test('TM-006: 新增租客表单校验必填字段', async ({ page }) => {
    await page.getByRole('button', { name: /新增租客/ }).click();
    const dialog = page.getByRole('dialog', { name: '新增租客' });
    await dialog.getByRole('button', { name: /确\s*定/ }).click();

    await test.step('验证：四个必填项均提示错误', async () => {
      for (const message of ['请输入姓名', '请选择性别', '请输入手机号', '请输入身份证号']) {
        await expect(dialog.locator('.ant-form-item-explain-error').filter({ hasText: message })).toBeVisible();
      }
    });
  });

  test('TM-007: 删除本次创建的租客成功', async ({ page }) => {
    const tenants = new TenantManagementPage(page);
    const tenant = newTenant();
    try {
      await tenants.create(tenant);
      await test.step('操作与验证：确认删除后目标记录消失', async () => tenants.deleteByName(tenant.name));
    } finally {
      await tenants.cleanup(tenant.name);
    }
  });
});
