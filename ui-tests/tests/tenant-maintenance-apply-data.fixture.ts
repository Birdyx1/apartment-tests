import { test as tenantTest } from './tenant-home-data.fixture';
import { createAdminApi } from './worker-account.fixture';

export type ApplyOrderRegistry = { add: (orderId: number) => void };

async function call(api: Awaited<ReturnType<typeof createAdminApi>>, method: string, url: string, payload?: unknown) {
  const response = await api.fetch(url, {
    method,
    ...(payload === undefined ? {} : { data: payload }),
  });
  const body = await response.json();
  if (!response.ok() || body.code !== 200) {
    throw new Error(`${method} ${url} 失败（HTTP ${response.status()}，业务码 ${body.code}）`);
  }
  return body.data;
}

/** 跟踪页面创建的工单；teardown 先将工单取消，再允许入住 fixture 退房清理。 */
export const test = tenantTest.extend<{ applyOrderRegistry: ApplyOrderRegistry }>({
  applyOrderRegistry: async ({ tenantHome }, use) => {
    const orderIds: number[] = [];
    await use({ add: (orderId) => orderIds.push(orderId) });

    if (orderIds.length === 0) return;
    const api = await createAdminApi();
    const cleanupErrors: string[] = [];
    try {
      for (const orderId of orderIds) {
        try {
          const detail = await call(api, 'GET', `/maintenance-order/${orderId}`);
          if (detail.status === 0 || detail.status === 1) {
            await call(api, 'PUT', `/maintenance-order/${orderId}/cancel`);
            const canceled = await call(api, 'GET', `/maintenance-order/${orderId}`);
            if (canceled.status !== 3) throw new Error('取消后的工单状态不是已取消');
          } else if (detail.status !== 2 && detail.status !== 3) {
            throw new Error(`工单状态 ${detail.status} 不是可清理的终态`);
          }
        } catch (error) {
          cleanupErrors.push(`清理工单 ${orderId} 失败：${error instanceof Error ? error.message : String(error)}`);
        }
      }
    } finally {
      await api.dispose();
    }
    if (cleanupErrors.length) throw new Error(cleanupErrors.join('；'));
  },
});

export { expect } from './tenant-home-data.fixture';
