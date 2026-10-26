import { expect, test } from './tenant-home-data.fixture';
import { TenantRentBillsPage } from '../pages/tenant-rent-bills.page';

function rentBillsResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/rent/bills' &&
    response.request().method() === 'GET');
}

function rentBillDetailResponse(page: import('@playwright/test').Page, billId: number) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === `/tenant-app/rent/bills/${billId}` &&
    response.request().method() === 'GET');
}

const billStatusText: Record<number, string> = { 0: '待缴', 1: '已缴', 2: '逾期', 3: '已关闭' };

test.describe('租客 H5 房租账单', () => {
  test('TRB-001: 账单列表显示完整账单信息', async ({ page, tenantAccount, tenantHome }) => {
    const billsPage = new TenantRentBillsPage(page);
    await test.step('准备：登录有当月账单的专属在住租客', async () => {
      await billsPage.login(tenantAccount.phone, tenantAccount.password);
    });

    const billsResponsePromise = rentBillsResponse(page);
    await billsPage.openList();

    await test.step('验证：账单接口与列表卡片包含租客和房间账单信息', async () => {
      const response = await billsResponsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      const bill = body.data.find((item: { leaseId: number }) => item.leaseId === tenantHome.leaseId);
      expect(bill).toMatchObject({
        tenantId: tenantAccount.id,
        leaseId: tenantHome.leaseId,
        roomId: tenantHome.roomId,
        amount: tenantHome.monthlyRent,
        apartmentName: tenantHome.apartmentName,
        roomNo: tenantHome.roomNo,
      });

      const card = billsPage.billCard(bill.billMonth, bill.amount);
      await expect(page.getByRole('heading', { name: '房租账单' })).toBeVisible();
      await expect(card).toBeVisible();
      await expect(card).toContainText(bill.dueDate);
      await expect(card).toContainText(tenantHome.apartmentName);
      await expect(card).toContainText(tenantHome.roomNo);
      await expect(card).toContainText(billStatusText[bill.status]);
    });
  });

  test('TRB-002: 打开账单详情', async ({ page, tenantAccount, tenantHome }) => {
    const billsPage = new TenantRentBillsPage(page);
    await billsPage.login(tenantAccount.phone, tenantAccount.password);
    const listResponsePromise = rentBillsResponse(page);
    await billsPage.openList();
    const listResponse = await listResponsePromise;
    expect(listResponse.status()).toBe(200);
    const listBody = await listResponse.json();
    expect(listBody.code).toBe(200);
    const bill = listBody.data.find((item: { leaseId: number }) => item.leaseId === tenantHome.leaseId);
    expect(bill).toBeTruthy();

    const detailResponsePromise = rentBillDetailResponse(page, bill.id);
    await billsPage.billCard(bill.billMonth, bill.amount).click();

    await test.step('验证：详情字段与账单一致，支付入口显示但不发起支付', async () => {
      const detailResponse = await detailResponsePromise;
      expect(detailResponse.status()).toBe(200);
      const detailBody = await detailResponse.json();
      expect(detailBody.code).toBe(200);
      expect(detailBody.data).toMatchObject({
        id: bill.id,
        tenantId: tenantAccount.id,
        billMonth: bill.billMonth,
        amount: bill.amount,
        dueDate: bill.dueDate,
        status: bill.status,
        apartmentName: tenantHome.apartmentName,
        roomNo: tenantHome.roomNo,
      });

      await expect(page.getByText('账单详情', { exact: true })).toBeVisible();
      await expect(page.getByText(`${bill.billMonth} 房租`, { exact: true })).toBeVisible();
      await expect(page.getByText(`¥${bill.amount}`, { exact: true })).toBeVisible();
      await expect(page.getByText(billStatusText[bill.status], { exact: true })).toBeVisible();
      await expect(billsPage.detailRow('应缴日期')).toContainText(bill.dueDate);
      await expect(billsPage.detailRow('房间')).toContainText(`${tenantHome.apartmentName} ${tenantHome.roomNo}`);
      if (bill.status !== 1) {
        await expect(page.getByRole('button', { name: '支付宝支付' })).toBeVisible();
        await expect(page.getByRole('button', { name: '微信支付' })).toBeVisible();
      } else {
        await expect(page.getByRole('button', { name: '支付宝支付' })).toHaveCount(0);
        await expect(page.getByRole('button', { name: '微信支付' })).toHaveCount(0);
      }
    });
  });

  test('TRB-003: 无账单时显示空状态', async ({ page, tenantAccount }) => {
    const billsPage = new TenantRentBillsPage(page);
    await billsPage.login(tenantAccount.phone, tenantAccount.password);
    const billsResponsePromise = rentBillsResponse(page);
    await billsPage.openList();

    await test.step('验证：账单接口为空时页面展示空状态', async () => {
      const response = await billsResponsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
      expect(body.data).toEqual([]);
      await expect(page.getByText('暂无账单', { exact: true })).toBeVisible();
      await expect(page.getByRole('heading', { name: '房租账单' })).toBeVisible();
    });
  });
});
