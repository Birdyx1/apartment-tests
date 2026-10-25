import { expect, test } from '@playwright/test';
import { MaintenanceManagementPage } from '../pages/maintenance-management.page';

function listResponse(page: import('@playwright/test').Page, params: Record<string, string>) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === '/maintenance-order/list' &&
      response.request().method() === 'GET' &&
      Object.entries(params).every(([key, value]) => url.searchParams.get(key) === value);
  });
}

test.describe('管理员维修工单管理', () => {
  test.beforeEach(async ({ page }) => {
    await new MaintenanceManagementPage(page).open();
  });

  test('MM-001: 工单管理列表与筛选控件加载', async ({ page }) => {
    await test.step('验证：工单列、筛选项和刷新入口可见', async () => {
      for (const name of ['房间', '租客', '标题', '描述', '紧急程度', '状态', '指派', '处理备注', '申请时间', '操作']) {
        await expect(page.getByRole('columnheader', { name })).toBeVisible();
      }
      await expect(page.getByRole('combobox', { name: '状态 :' })).toBeVisible();
      await expect(page.getByRole('combobox', { name: '紧急程度 :' })).toBeVisible();
      await expect(page.getByRole('button', { name: /刷新/ })).toBeVisible();
    });
  });

  test('MM-002: 按工单状态筛选已取消记录', async ({ page }) => {
    const orders = new MaintenanceManagementPage(page);
    await test.step('操作：选择已取消并搜索', async () => {
      await orders.chooseStatus('已取消');
      const response = listResponse(page, { status: '3' });
      await orders.search();
      await response;
    });
    await test.step('验证：请求状态参数正确，返回行均为已取消', async () => {
      await expect(orders.statusSelection()).toHaveText('已取消');
      for (const row of await orders.dataRows().all()) {
        await expect(row).toContainText('已取消');
      }
    });
  });

  test('MM-003: 按紧急程度筛选紧急工单', async ({ page }) => {
    const orders = new MaintenanceManagementPage(page);
    await test.step('操作：选择紧急并搜索', async () => {
      await orders.chooseUrgency('紧急');
      const response = listResponse(page, { urgency: '2' });
      await orders.search();
      await response;
    });
    await test.step('验证：请求紧急程度参数正确，返回行均为紧急', async () => {
      await expect(orders.urgencySelection()).toHaveText('紧急');
      for (const row of await orders.dataRows().all()) {
        await expect(row).toContainText('紧急');
      }
    });
  });

  test('MM-004: 重置状态和紧急程度筛选条件', async ({ page }) => {
    const orders = new MaintenanceManagementPage(page);
    await orders.chooseStatus('已取消');
    await orders.chooseUrgency('紧急');
    const filteredResponse = listResponse(page, { status: '3', urgency: '2' });
    await orders.search();
    await filteredResponse;

    await test.step('操作与验证：重置后字段清空且请求不带筛选参数', async () => {
      const response = listResponse(page, {});
      await orders.reset();
      await response;
      await expect(orders.statusSelection()).toHaveCount(0);
      await expect(orders.urgencySelection()).toHaveCount(0);
    });
  });

  test('MM-005: 刷新列表时保留当前状态筛选', async ({ page }) => {
    const orders = new MaintenanceManagementPage(page);
    await orders.chooseStatus('已取消');
    const searchResponse = listResponse(page, { status: '3' });
    await orders.search();
    await searchResponse;

    await test.step('操作与验证：刷新仍按已取消状态请求', async () => {
      const response = listResponse(page, { status: '3' });
      await orders.refresh();
      await response;
      await expect(orders.statusSelection()).toHaveText('已取消');
    });
  });
});
