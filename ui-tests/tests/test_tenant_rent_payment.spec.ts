import { expect, test } from './tenant-home-data.fixture';
import { TenantRentBillsPage } from '../pages/tenant-rent-bills.page';

function rentBillsResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/rent/bills' &&
    response.request().method() === 'GET');
}

function paymentResponse(page: import('@playwright/test').Page, billId: number) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === `/tenant-app/rent/bills/${billId}/pay` &&
    response.request().method() === 'POST');
}

function mockConfirmResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname.startsWith('/tenant-app/rent/payments/') &&
    new URL(response.url()).pathname.endsWith('/mock-confirm') &&
    response.request().method() === 'POST');
}

async function openTenantBill(
  page: import('@playwright/test').Page,
  billsPage: TenantRentBillsPage,
  tenantAccount: { phone: string; password: string },
  leaseId: number,
) {
  await billsPage.login(tenantAccount.phone, tenantAccount.password);
  const responsePromise = rentBillsResponse(page);
  await billsPage.openList();
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.code).toBe(200);
  const bill = body.data.find((item: { leaseId: number }) => item.leaseId === leaseId);
  expect(bill).toBeTruthy();
  expect([0, 2]).toContain(bill.status);
  await billsPage.openDetail(bill.id);
  return bill;
}

test.describe('租客 H5 房租账单支付', () => {
  test('TRP-001: 取消模拟支付后账单仍未缴', async ({ page, tenantAccount, tenantHome }) => {
    const billsPage = new TenantRentBillsPage(page);
    let mockConfirmRequested = false;
    let billId = 0;

    await test.step('准备：打开专属待缴账单详情', async () => {
      const bill = await openTenantBill(page, billsPage, tenantAccount, tenantHome.leaseId);
      billId = bill.id;
      page.on('request', (request) => {
        if (new URL(request.url()).pathname.endsWith('/mock-confirm')) mockConfirmRequested = true;
      });
    });

    await test.step('操作：选择微信支付并取消确认', async () => {
      const payResponsePromise = paymentResponse(page, billId);
      await page.getByRole('button', { name: '微信支付' }).click();
      const payResponse = await payResponsePromise;
      expect(payResponse.status()).toBe(200);
      const payBody = await payResponse.json();
      expect(payBody.code).toBe(200);
      expect(payBody.data.mode).toBe('MOCK');
      await expect(page.getByRole('dialog')).toContainText('模拟支付');
      await expect(page.getByRole('dialog')).toContainText('确认支付');
      await page.getByRole('button', { name: '取消' }).click();
    });

    await test.step('验证：仍在详情页，账单未缴且没有确认请求', async () => {
      await expect(page).toHaveURL(/\/rent\/detail\/\d+$/);
      await expect(page.getByText('待缴', { exact: true }).or(page.getByText('逾期', { exact: true }))).toBeVisible();
      await expect(page.getByRole('button', { name: '支付宝支付' })).toBeVisible();
      await expect(page.getByRole('button', { name: '微信支付' })).toBeVisible();
      expect(mockConfirmRequested).toBe(false);
    });
  });

  test('TRP-002: 确认模拟支付后账单变为已缴', async ({ page, tenantAccount, tenantHome }) => {
    const billsPage = new TenantRentBillsPage(page);
    let billId = 0;

    await test.step('准备：打开另一张专属待缴账单详情', async () => {
      const bill = await openTenantBill(page, billsPage, tenantAccount, tenantHome.leaseId);
      billId = bill.id;
    });

    await test.step('操作：发起支付宝 MOCK 支付并确认', async () => {
      const payResponsePromise = paymentResponse(page, billId);
      await page.getByRole('button', { name: '支付宝支付' }).click();
      const payResponse = await payResponsePromise;
      expect(payResponse.status()).toBe(200);
      const payBody = await payResponse.json();
      expect(payBody.code).toBe(200);
      expect(payBody.data.mode).toBe('MOCK');
      await expect(page.getByRole('dialog')).toContainText(`确认支付 ¥${tenantHome.monthlyRent} 吗？`);

      const confirmResponsePromise = mockConfirmResponse(page);
      await page.getByRole('button', { name: '确定' }).click();
      const confirmResponse = await confirmResponsePromise;
      expect(confirmResponse.status()).toBe(200);
      const confirmBody = await confirmResponse.json();
      expect(confirmBody.code).toBe(200);
      await expect(page).toHaveURL(/\/rent\/list$/);
      await expect(page.getByText('支付成功', { exact: true })).toBeVisible();
    });

    await test.step('验证：账单已缴，详情显示已缴时间并隐藏支付入口', async () => {
      const listResponsePromise = rentBillsResponse(page);
      // 支付成功后的列表会自动刷新；若响应已返回，则刷新一次确保断言读取最终状态。
      await page.reload();
      const listResponse = await listResponsePromise;
      expect(listResponse.status()).toBe(200);
      const listBody = await listResponse.json();
      expect(listBody.code).toBe(200);
      const paidBill = listBody.data.find((item: { id: number }) => item.id === billId);
      expect(paidBill).toMatchObject({ id: billId, status: 1 });
      expect(paidBill.paidTime).toBeTruthy();

      await billsPage.billCard(paidBill.billMonth, paidBill.amount).click();
      await expect(page.getByText('已缴时间', { exact: true })).toBeVisible();
      await expect(page.getByText('已缴', { exact: true })).toBeVisible();
      await expect(page.getByRole('button', { name: '支付宝支付' })).toHaveCount(0);
      await expect(page.getByRole('button', { name: '微信支付' })).toHaveCount(0);
    });
  });
});
