import { randomUUID } from 'node:crypto';
import { request } from '@playwright/test';
import { createAdminApi } from './worker-account.fixture';
import { test as tenantTest } from './tenant-home-data.fixture';

export type TenantMaintenanceOrder = {
  id: number;
  title: string;
  description: string;
  urgency: number;
  status: number;
  roomNo: string;
  tenantId: number;
};

async function assertApiSuccess(response: import('@playwright/test').APIResponse, method: string, url: string) {
  const body = await response.json();
  if (!response.ok() || body.code !== 200) {
    throw new Error(`${method} ${url} 失败（HTTP ${response.status()}，业务码 ${body.code}）`);
  }
  return body.data;
}

/** 建立专属在住租客工单；teardown 顺序确保先取消工单，再由 tenantHome 退房。 */
export const test = tenantTest.extend<{ tenantMaintenanceOrder: TenantMaintenanceOrder }>({
  tenantMaintenanceOrder: async ({ tenantAccount, tenantHome }, use) => {
    const baseURL = process.env.API_BASE_URL ?? 'http://localhost:8080';
    const tenantApi = await request.newContext({ baseURL });
    const adminApi = await createAdminApi();
    let orderId: number | undefined;
    const suffix = randomUUID().replaceAll('-', '').slice(0, 8);
    const order = {
      title: `UI租客工单-${suffix}`,
      description: `列表验证专用描述-${suffix}`,
      urgency: 2,
      status: 0,
      roomNo: tenantHome.roomNo,
      tenantId: tenantAccount.id,
    };

    try {
      const loginResponse = await tenantApi.post('/tenant-app/auth/login', {
        data: { account: tenantAccount.phone, password: tenantAccount.password },
      });
      const loginData = await assertApiSuccess(loginResponse, 'POST', '/tenant-app/auth/login');
      const tenantToken = loginData.accessToken as string | undefined;
      if (!tenantToken) throw new Error('租客登录响应缺少 accessToken');

      const createResponse = await tenantApi.post('/tenant-app/maintenance/create', {
        headers: { Authorization: `Bearer ${tenantToken}` },
        data: { title: order.title, description: order.description, urgency: order.urgency, imageKeys: [] },
      });
      const created = await assertApiSuccess(createResponse, 'POST', '/tenant-app/maintenance/create');
      orderId = created.id;

      await use({ id: orderId, ...order });
    } finally {
      const cleanupErrors: string[] = [];
      if (orderId !== undefined) {
        try {
          const detailResponse = await adminApi.get(`/maintenance-order/${orderId}`);
          const detail = await assertApiSuccess(detailResponse, 'GET', `/maintenance-order/${orderId}`);
          if (detail.status === 0 || detail.status === 1) {
            const cancelResponse = await adminApi.put(`/maintenance-order/${orderId}/cancel`);
            await assertApiSuccess(cancelResponse, 'PUT', `/maintenance-order/${orderId}/cancel`);
            const canceledResponse = await adminApi.get(`/maintenance-order/${orderId}`);
            const canceled = await assertApiSuccess(canceledResponse, 'GET', `/maintenance-order/${orderId}`);
            if (canceled.status !== 3) throw new Error('取消后的工单状态不是已取消');
          } else if (detail.status !== 2 && detail.status !== 3) {
            throw new Error(`工单状态 ${detail.status} 不是可清理的终态`);
          }
        } catch (error) {
          cleanupErrors.push(`清理工单失败：${error instanceof Error ? error.message : String(error)}`);
        }
      }
      await Promise.all([tenantApi.dispose(), adminApi.dispose()]);
      if (cleanupErrors.length) throw new Error(cleanupErrors.join('；'));
    }
  },
});

export { expect } from './tenant-home-data.fixture';
