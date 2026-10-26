import { expect, test } from './tenant-notice-data.fixture';
import { TenantNoticePage } from '../pages/tenant-notice.page';

function noticeListResponse(page: import('@playwright/test').Page) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === '/tenant-app/notices' &&
    response.request().method() === 'GET');
}

function noticeDetailResponse(page: import('@playwright/test').Page, noticeId: number) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === `/tenant-app/notices/${noticeId}` &&
    response.request().method() === 'GET');
}

test.describe('租客 H5 公告详情', () => {
  test('TND-001: 首页公告卡片可打开完整公告详情', async ({ page, tenantAccount, tenantHome, tenantNotice }) => {
    const noticePage = new TenantNoticePage(page);
    let noticeData = { id: 0, title: '', content: '', updateTime: '' };

    await test.step('准备：登录有入住记录的租客并加载首页公告', async () => {
      const listResponsePromise = noticeListResponse(page);
      await noticePage.login(tenantAccount.phone, tenantAccount.password);
      expect(tenantHome.leaseId).toBeGreaterThan(0);
      const listResponse = await listResponsePromise;
      expect(listResponse.status()).toBe(200);
      const listBody = await listResponse.json();
      expect(listBody.code).toBe(200);
      noticeData = listBody.data.find((item: { id: number }) => item.id === tenantNotice.id);
      expect(noticeData).toBeTruthy();
      expect(noticeData.title).toBe(tenantNotice.title);
    });

    await test.step('操作：从首页点击本轮创建的公告', async () => {
      const detailResponsePromise = noticeDetailResponse(page, tenantNotice.id);
      await noticePage.openNoticeFromHome(tenantNotice.title);
      const detailResponse = await detailResponsePromise;
      expect(detailResponse.status()).toBe(200);
      const detailBody = await detailResponse.json();
      expect(detailBody.code).toBe(200);
      noticeData = detailBody.data;
    });

    await test.step('验证：详情标题、更新时间和正文与公告接口一致', async () => {
      await expect(page.getByRole('heading', { name: tenantNotice.title })).toBeVisible();
      await expect(page.locator('.notice-time')).toContainText(noticeData.updateTime ?? '');
      await expect(page.locator('.notice-content')).toContainText(tenantNotice.content.replace('\n', ' '));
      await expect(page.getByText('公告详情', { exact: true })).toBeVisible();
    });
  });

  test('TND-002: 无入住记录时公告详情返回首页', async ({ page, tenantAccount, tenantNotice }) => {
    const noticePage = new TenantNoticePage(page);

    await test.step('准备：登录没有入住记录的租客', async () => {
      await noticePage.login(tenantAccount.phone, tenantAccount.password);
    });

    await test.step('操作：直接访问已发布公告详情', async () => {
      const detailResponsePromise = noticeDetailResponse(page, tenantNotice.id);
      await noticePage.openNotice(tenantNotice.id);
      const detailResponse = await detailResponsePromise;
      expect(detailResponse.status()).toBe(200);
      const detailBody = await detailResponse.json();
      expect(detailBody.code).toBe(400);
      expect(detailBody.message).toContain('当前没有在住记录');
    });

    await test.step('验证：页面提示错误并返回首页', async () => {
      await expect(page).toHaveURL(noticePage.homeUrl());
      await expect(page.getByRole('heading')).toContainText('你好，');
    });
  });

  test('TND-003: 公告详情返回按钮回到首页', async ({ page, tenantAccount, tenantHome, tenantNotice }) => {
    const noticePage = new TenantNoticePage(page);
    expect(tenantHome.leaseId).toBeGreaterThan(0);
    await noticePage.login(tenantAccount.phone, tenantAccount.password);

    await test.step('操作：从首页打开本轮已发布公告', async () => {
      const detailResponsePromise = noticeDetailResponse(page, tenantNotice.id);
      await noticePage.openNoticeFromHome(tenantNotice.title);
      const response = await detailResponsePromise;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.code).toBe(200);
    });

    await test.step('操作：点击公告详情的返回导航', async () => {
      await noticePage.goBack();
    });

    await test.step('验证：路由回到首页并显示租客首页内容', async () => {
      await expect(page).toHaveURL(noticePage.homeUrl());
      await expect(page.getByRole('heading')).toContainText('你好，');
    });
  });
});
