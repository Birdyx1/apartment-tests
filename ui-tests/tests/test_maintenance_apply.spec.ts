import { expect, test, type Page } from '@playwright/test';
import { MaintenanceApplyPage } from '../pages/maintenance-apply.page';

function listResponse(page: Page) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === '/maintenance-order/apply/list' && response.request().method() === 'GET';
  });
}

test.describe('管理员维修工单申请', () => {
  test.beforeEach(async ({ page }) => {
    await new MaintenanceApplyPage(page).open();
  });

  test('MA-001: 维修工单申请列表加载', async ({ page }) => {
    for (const name of ['房间', '租客', '标题', '描述', '紧急程度', '状态', '处理备注', '申请时间', '操作']) {
      await expect(page.getByRole('columnheader', { name })).toBeVisible();
    }
    await expect(page.getByRole('button', { name: /申请维修工单/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /刷新/ })).toBeVisible();
  });

  test('MA-002: 管理员打开申请表单', async ({ page }) => {
    const apply = new MaintenanceApplyPage(page);
    await apply.openForm();

    await expect(apply.dialog().getByRole('combobox', { name: '* 租客' })).toBeVisible();
    await expect(apply.titleInput()).toBeVisible();
    await expect(apply.dialog().getByRole('textbox', { name: '问题描述' })).toBeVisible();
    await expect(apply.urgencyInput()).toBeVisible();
    await expect(apply.dialog().getByText('现场照片（最多6张）')).toBeVisible();
  });

  test('MA-003: 申请表单必填校验且不发送创建请求', async ({ page }) => {
    const apply = new MaintenanceApplyPage(page);
    await apply.openForm();
    const createRequests: string[] = [];
    page.on('request', (request) => {
      if (new URL(request.url()).pathname === '/maintenance-order/create') createRequests.push(request.method());
    });

    await apply.submit();

    for (const message of ['请选择租客', '请输入工单标题', '请选择紧急程度']) {
      await expect(apply.dialog().getByText(message, { exact: true })).toBeVisible();
    }
    expect(createRequests).toHaveLength(0);
  });

  test('MA-004: 紧急程度选项正确', async ({ page }) => {
    const apply = new MaintenanceApplyPage(page);
    await apply.openForm();
    await apply.urgencyInput().click();

    for (const label of ['普通', '紧急', '非常紧急']) {
      await expect(apply.visibleUrgencyOption(label)).toBeVisible();
    }
  });

  test('MA-005: 关闭申请表单会重置输入', async ({ page }) => {
    const apply = new MaintenanceApplyPage(page);
    await apply.openForm();
    await apply.titleInput().fill('自动化校验临时标题');
    await apply.chooseUrgency('紧急');
    await apply.closeForm();

    await apply.openForm();
    await expect(apply.titleInput()).toHaveValue('');
    await expect(apply.urgencySelection()).toHaveCount(0);
  });

  test('MA-006: 刷新申请列表', async ({ page }) => {
    const apply = new MaintenanceApplyPage(page);
    const response = listResponse(page);
    await apply.refresh();
    expect((await response).status()).toBe(200);
  });
});
