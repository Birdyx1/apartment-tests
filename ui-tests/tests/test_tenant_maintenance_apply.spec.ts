import { expect, test } from './tenant-maintenance-apply-data.fixture';
import { TenantMaintenanceApplyPage } from '../pages/tenant-maintenance-apply.page';

const tenantBaseUrl = (process.env.TENANT_H5_URL ?? 'http://localhost:3001/tenant-h5').replace(/\/$/, '');

function createOrderResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/maintenance/create' &&
    response.request().method() === 'POST');
}

test.describe('租客 H5 申请维修', () => {
  test('TMA-001: 租客成功提交紧急维修申请', async ({ page, tenantAccount, tenantHome, applyOrderRegistry }) => {
    const applyPage = new TenantMaintenanceApplyPage(page);
    await test.step('准备：登录有当前入住记录的租客并打开申请表单', async () => {
      await applyPage.login(tenantAccount.phone, tenantAccount.password);
      await applyPage.openApply();
    });

    const title = `UI申请维修-${Date.now()}`;
    const description = '自动化验证厨房水龙头漏水，请安排维修。';
    const [createResponse, listResponsePromise] = await test.step('操作：填写问题并选择非常紧急后提交', async () => {
      await applyPage.fillRequest(title, description);
      await applyPage.selectUrgency('非常紧急');
      const responsePromise = createOrderResponse(page);
      const nextListResponse = page.waitForResponse((response) =>
        new URL(response.url()).pathname === '/tenant-app/maintenance/list' &&
        response.request().method() === 'GET');
      await applyPage.submit();
      return Promise.all([responsePromise, Promise.resolve(nextListResponse)]);
    });

    await test.step('验证：工单创建成功并出现在列表', async () => {
      expect(createResponse.status()).toBe(200);
      const body = await createResponse.json();
      expect(body.code).toBe(200);
      const orderId = body.data.id as number;
      applyOrderRegistry.add(orderId);
      expect(orderId).toBeTruthy();

      await expect(page).toHaveURL(`${tenantBaseUrl}/maintenance/list`);
      const listResponse = await listResponsePromise;
      expect(listResponse.status()).toBe(200);
      const listBody = await listResponse.json();
      const createdOrder = listBody.data.find((item: { id: number }) => item.id === orderId);
      expect(createdOrder).toMatchObject({
        tenantId: tenantAccount.id,
        title,
        description,
        urgency: 3,
        status: 0,
        roomNo: tenantHome.roomNo,
      });

      const card = page.locator('.apple-card').filter({ hasText: title });
      await expect(card).toBeVisible();
      await expect(card).toContainText(description);
      await expect(card).toContainText(tenantHome.roomNo);
      await expect(card).toContainText('非常紧急');
      await expect(card).toContainText('待处理');
    });
  });

  test('TMA-002: 工单标题必填', async ({ page, tenantAccount }) => {
    const applyPage = new TenantMaintenanceApplyPage(page);
    await test.step('准备：登录租客并打开空白申请表单', async () => {
      await applyPage.login(tenantAccount.phone, tenantAccount.password);
      await applyPage.openApply();
    });

    let createRequestCount = 0;
    page.on('request', (request) => {
      if (new URL(request.url()).pathname === '/tenant-app/maintenance/create' && request.method() === 'POST') {
        createRequestCount += 1;
      }
    });
    await test.step('操作：标题留空并提交', async () => {
      await applyPage.submit();
    });

    await test.step('验证：提示标题必填，不发送创建请求', async () => {
      await expect(page.getByText('请输入工单标题', { exact: true })).toBeVisible();
      await expect(page).toHaveURL(`${tenantBaseUrl}/maintenance/apply`);
      expect(createRequestCount).toBe(0);
    });
  });

  test('TMA-003: 无入住时不能提交维修申请', async ({ page, tenantAccount }) => {
    const applyPage = new TenantMaintenanceApplyPage(page);
    await test.step('准备：登录没有当前入住记录的租客并打开申请表单', async () => {
      await applyPage.login(tenantAccount.phone, tenantAccount.password);
      await applyPage.openApply();
    });

    await applyPage.fillRequest(`无入住申请-${Date.now()}`, '验证没有在住记录时的提交限制');
    const responsePromise = createOrderResponse(page);
    await applyPage.submit();

    await test.step('验证：后端拒绝创建，页面显示业务提示并保留表单', async () => {
      const response = await responsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(400);
      expect(body.message).toBe('您当前没有在住记录，无法申请工单');
      await expect(page.getByText('您当前没有在住记录，无法申请工单', { exact: true })).toBeVisible();
      await expect(page).toHaveURL(`${tenantBaseUrl}/maintenance/apply`);
      await expect(page.getByRole('textbox', { name: /工单标题/ })).toHaveValue(/无入住申请-/);
    });
  });
});
