import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';
import { ApartmentListPage, type ApartmentForm } from '../pages/apartment-list.page';

function newApartment(): ApartmentForm {
  return {
    name: `UI自动化公寓-${randomUUID().slice(0, 8)}`,
    address: '本地自动化测试地址',
    contactName: '自动化联系人',
    contactPhone: '13800000000',
    description: 'Playwright 临时测试数据',
  };
}

test.describe('管理员公寓列表', () => {
  test.beforeEach(async ({ page }) => {
    await new ApartmentListPage(page).open();
  });

  test('AL-001: 公寓列表正常加载', async ({ page }) => {
    await test.step('验证列表表头和数据行可见', async () => {
      for (const name of ['名称', '地址', '联系人', '联系电话', '操作']) {
        await expect(page.getByRole('columnheader', { name })).toBeVisible();
      }
      await expect(page.getByRole('row').nth(1)).toBeVisible();
    });
  });

  test('AL-002: 按名称搜索本次创建的公寓', async ({ page }) => {
    const list = new ApartmentListPage(page);
    const apartment = newApartment();
    try {
      await test.step('准备：创建唯一的目标公寓', async () => list.create(apartment));
      await test.step('操作与验证：按名称搜索并只显示目标行', async () => {
        await list.searchByName(apartment.name);
        await expect(page.getByRole('row').filter({ hasText: apartment.name })).toHaveCount(1);
      });
    } finally {
      await list.cleanup(apartment.name);
    }
  });

  test('AL-003: 重置搜索条件后恢复默认列表', async ({ page }) => {
    const list = new ApartmentListPage(page);
    const apartment = newApartment();
    const initialRows = await page.getByRole('row').count();
    try {
      await list.create(apartment);
      await list.searchByName(apartment.name);
      await page.getByRole('button', { name: /重\s*置/ }).click();

      await test.step('验证搜索条件清空且列表恢复多条数据', async () => {
        await expect(page.getByRole('textbox', { name: '名称 :' })).toHaveValue('');
        await expect(page.getByRole('row')).toHaveCount(initialRows + 1);
      });
    } finally {
      await list.cleanup(apartment.name);
    }
  });

  test('AL-004: 新增公寓成功', async ({ page }) => {
    const list = new ApartmentListPage(page);
    const apartment = newApartment();
    try {
      await test.step('操作：填写并提交新增表单', async () => list.create(apartment));
      await test.step('验证：列表展示本次新增公寓及联系人信息', async () => {
        const row = list.row(apartment.name);
        await expect(row).toContainText(apartment.address);
        await expect(row).toContainText(apartment.contactName);
      });
    } finally {
      await list.cleanup(apartment.name);
    }
  });

  test('AL-005: 刷新后仍可查询到已创建公寓', async ({ page }) => {
    const list = new ApartmentListPage(page);
    const apartment = newApartment();
    try {
      await list.create(apartment);
      await page.getByTestId('apartment-management-refresh-button').click();
      await expect(list.row(apartment.name)).toBeVisible();
    } finally {
      await list.cleanup(apartment.name);
    }
  });

  test('AL-006: 编辑公寓地址成功', async ({ page }) => {
    const list = new ApartmentListPage(page);
    const apartment = newApartment();
    const updatedAddress = `${apartment.address}-已更新`;
    try {
      await list.create(apartment);
      await list.searchByName(apartment.name);
      await list.row(apartment.name).getByTestId('apartment-management-edit-button').click();
      const dialog = page.getByRole('dialog', { name: '编辑公寓' });
      await dialog.getByTestId('apartment-management-field-address').fill(updatedAddress);
      await dialog.getByTestId('apartment-management-modal-ok').click();

      await test.step('验证：列表行展示更新后的地址', async () => {
        await expect(list.row(apartment.name)).toContainText(updatedAddress);
      });
    } finally {
      await list.cleanup(apartment.name);
    }
  });

  test('AL-007: 删除公寓成功', async ({ page }) => {
    const list = new ApartmentListPage(page);
    const apartment = newApartment();
    await list.create(apartment);
    await test.step('操作与验证：确认删除后目标行消失', async () => {
      await list.deleteByName(apartment.name);
      await expect(list.row(apartment.name)).toHaveCount(0);
    });
  });
});
