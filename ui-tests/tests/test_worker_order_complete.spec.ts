import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createAdminApi } from './worker-account.fixture';
import { expect, test } from './worker-detail-data.fixture';
import { WorkerOrderDetailPage } from '../pages/worker-order-detail.page';

const completionImagePath = resolve(process.cwd(), 'tests/fixtures/completion-image.png');
const imagePreviewUrl = `data:image/png;base64,${readFileSync(completionImagePath).toString('base64')}`;

test.describe('维修工端完成工单表单', () => {
  test.beforeEach(async ({ page, workerAccount, pendingWorkOrder }, testInfo) => {
    const imageKey = `ui-test/${testInfo.testId}-completion.png`;
    // 上传接口单独由 API 自动化覆盖；Stub 防止 UI 回归向本地 MinIO 留下孤立图片。
    await page.route('**/worker-app/files/upload', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 200,
        message: '操作成功',
        data: { url: imagePreviewUrl, objectKey: imageKey },
        success: true,
      }),
    }));

    const detailPage = new WorkerOrderDetailPage(page);
    await detailPage.login(workerAccount.username, workerAccount.password);
    await detailPage.openOrder(pendingWorkOrder.title);
    await detailPage.grabForCompletion();
    await detailPage.openCompletionForm();
  });

  test('WC-001: 未填写处理备注时阻止完成工单', async ({ page, pendingWorkOrder }) => {
    await test.step('准备：确认专属工单处于处理中且表单已打开', async () => {
      await expect(page.getByPlaceholder('请填写处理结果（必填）')).toBeVisible();
    });

    await test.step('操作：不填写备注和图片，点击确认完成', async () => {
      await page.getByRole('button', { name: '确认完成' }).click();
    });

    await test.step('验证：提示备注必填且工单状态不变', async () => {
      await expect(page.getByText('请填写处理备注')).toBeVisible();
      await expect(page.getByPlaceholder('请填写处理结果（必填）')).toBeVisible();

      const api = await createAdminApi();
      try {
        const response = await api.get(`/maintenance-order/${pendingWorkOrder.id}`);
        const body = await response.json();
        expect(response.status()).toBe(200);
        expect(body.code).toBe(200);
        expect(body.data.status).toBe(1);
      } finally {
        await api.dispose();
      }
    });
  });

  test('WC-002: 未上传处理图片时阻止完成工单', async ({ page, pendingWorkOrder }) => {
    const remark = `处理结果-${Date.now()}`;
    await test.step('准备：确认专属工单处于处理中且表单已打开', async () => {
      await expect(page.getByPlaceholder('请填写处理结果（必填）')).toBeVisible();
    });

    await test.step('操作：填写备注但不选图片，点击确认完成', async () => {
      await page.getByPlaceholder('请填写处理结果（必填）').fill(remark);
      await page.getByRole('button', { name: '确认完成' }).click();
    });

    await test.step('验证：提示至少上传一张图片且工单状态不变', async () => {
      await expect(page.getByText('请至少上传一张处理图片')).toBeVisible();
      await expect(page.getByPlaceholder('请填写处理结果（必填）')).toHaveValue(remark);

      const api = await createAdminApi();
      try {
        const response = await api.get(`/maintenance-order/${pendingWorkOrder.id}`);
        const body = await response.json();
        expect(response.status()).toBe(200);
        expect(body.code).toBe(200);
        expect(body.data.status).toBe(1);
      } finally {
        await api.dispose();
      }
    });
  });

  test('WC-003: 提交处理备注和图片后完成工单', async ({ page, workerAccount, pendingWorkOrder }, testInfo) => {
    const remark = `已完成维修-${testInfo.testId}`;
    const imageKey = `ui-test/${testInfo.testId}-completion.png`;
    await test.step('准备：确认专属工单处于处理中且表单已打开', async () => {
      await expect(page.getByPlaceholder('请填写处理结果（必填）')).toBeVisible();
    });

    const [completeRequest, completeResponse] = await test.step('操作：填写备注、选择图片并提交', async () => {
      await page.getByPlaceholder('请填写处理结果（必填）').fill(remark);
      await new WorkerOrderDetailPage(page).uploadCompletionImage(completionImagePath);
      const requestPromise = page.waitForRequest((request) =>
        new URL(request.url()).pathname === `/worker-app/maintenance/${pendingWorkOrder.id}/complete` &&
        request.method() === 'PUT');
      const responsePromise = page.waitForResponse((response) =>
        new URL(response.url()).pathname === `/worker-app/maintenance/${pendingWorkOrder.id}/complete` &&
        response.request().method() === 'PUT');
      await page.getByRole('button', { name: '确认完成' }).click();
      return Promise.all([requestPromise, responsePromise]);
    });

    await test.step('验证：完成请求携带处理信息，工单进入已完成状态', async () => {
      expect(completeResponse.status()).toBe(200);
      const responseBody = await completeResponse.json();
      expect(responseBody.code).toBe(200);
      expect(responseBody.data).toBe(true);
      expect(completeRequest.postDataJSON()).toEqual({ handlerRemark: remark, imageKeys: [imageKey] });

      await expect(page.getByText('已完成', { exact: true })).toBeVisible();
      await expect(page.getByText(remark, { exact: true })).toBeVisible();
      await expect(page.getByRole('button', { name: '完成工单' })).toHaveCount(0);

      const api = await createAdminApi();
      try {
        const response = await api.get(`/maintenance-order/${pendingWorkOrder.id}`);
        const body = await response.json();
        expect(response.status()).toBe(200);
        expect(body.code).toBe(200);
        expect(body.data.status).toBe(2);
        expect(body.data.handlerId).toBe(workerAccount.id);
        expect(body.data.handlerRemark).toBe(remark);
        expect(body.data.completeImageUrls).toHaveLength(1);
      } finally {
        await api.dispose();
      }
    });
  });
});
