import { createAdminApi } from './worker-account.fixture';
import { test as base, type PendingWorkOrder } from './worker-detail-data.fixture';

/** 在专属待处理工单上预置管理员派单状态，供维修工 H5 接单流程使用。 */
export const test = base.extend<{ assignedWorkOrder: PendingWorkOrder }>({
  assignedWorkOrder: async ({ workerAccount, pendingWorkOrder }, use) => {
    const api = await createAdminApi();
    try {
      const response = await api.put(`/maintenance-order/${pendingWorkOrder.id}/assign`, {
        data: { assigneeId: workerAccount.id },
      });
      const body = await response.json();
      if (!response.ok() || body.code !== 200 || body.data !== true) {
        throw new Error(`管理员派单失败（HTTP ${response.status()}，业务码 ${body.code}）`);
      }
      await use(pendingWorkOrder);
    } finally {
      await api.dispose();
    }
  },
});

export { expect } from './worker-detail-data.fixture';
