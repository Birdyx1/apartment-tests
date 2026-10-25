import { randomUUID } from 'node:crypto';
import { test as base } from './worker-account.fixture';
import { createAdminApi } from './worker-account.fixture';

export type PendingWorkOrder = {
  id: number;
  title: string;
  apartmentName: string;
  roomNo: string;
  tenantName: string;
  description: string;
};

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

function localDateTime() {
  const local = new Date(Date.now() - new Date().getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 19).replace('T', ' ');
}

/** 创建一条完整但专属的在住报修数据；结束时取消工单、退房并清理所有可删依赖。 */
export const test = base.extend<{ pendingWorkOrder: PendingWorkOrder }>({
  pendingWorkOrder: async ({}, use) => {
    const api = await createAdminApi();
    const suffix = randomUUID().replaceAll('-', '').slice(0, 8);
    let apartmentId: number | undefined;
    let roomId: number | undefined;
    let tenantId: number | undefined;
    let leaseId: number | undefined;
    let orderId: number | undefined;
    let orderClosed = false;
    let checkedOut = false;

    try {
      const apartmentName = `UI详情公寓-${suffix}`;
      apartmentId = (await call(api, 'POST', '/apartment', { name: apartmentName })).id;
      const roomNo = `UI详情-${suffix}`;
      roomId = (await call(api, 'POST', '/room/create', {
        apartmentId, roomNo, floor: 1, layout: '一室一厅', area: 30, status: 0,
      })).id;
      const tenantName = `UI详情租客-${suffix}`;
      const phone = `199${String(Date.now()).slice(-8)}`;
      tenantId = (await call(api, 'POST', '/tenant/create', {
        name: tenantName,
        gender: 1,
        phone,
        idCard: `TEST${randomUUID().replaceAll('-', '').slice(0, 14)}`,
        password: 'Tenant123!',
      })).id;
      leaseId = (await call(api, 'POST', '/tenant/lease', {
        tenantId,
        roomId,
        checkInTime: localDateTime(),
        leaseMonths: 1,
        deposit: 500,
        monthlyRent: 1500,
        rentDueDay: 1,
      })).id;
      const title = `UI详情工单-${suffix}`;
      const description = '自动化测试专用描述：检查工单详情展示';
      orderId = (await call(api, 'POST', '/maintenance-order/create', {
        tenantId, title, description, urgency: 2, imageKeys: [],
      })).id;

      await use({ id: orderId, title, apartmentName, roomNo, tenantName, description });
    } finally {
      const cleanupErrors: string[] = [];
      try {
        if (orderId !== undefined) {
          const detail = await call(api, 'GET', `/maintenance-order/${orderId}`);
          if (detail.status === 0 || detail.status === 1) {
            await call(api, 'PUT', `/maintenance-order/${orderId}/cancel`);
            const canceled = await call(api, 'GET', `/maintenance-order/${orderId}`);
            if (canceled.status !== 3) throw new Error('取消后的工单状态不是已取消');
            orderClosed = true;
          } else if (detail.status === 2 || detail.status === 3) {
            // 已完成、已取消都是终态；保留业务历史后可以继续退房清理依赖。
            orderClosed = true;
          } else {
            throw new Error(`工单状态 ${detail.status} 不是可清理的终态`);
          }
        } else {
          orderClosed = true;
        }
      } catch (error) {
        cleanupErrors.push(`取消工单失败：${error instanceof Error ? error.message : String(error)}`);
      }

      // 住房被工单依赖：只有确认工单已取消后才退房及清理依赖资源。
      if (orderClosed && leaseId !== undefined) {
        try {
          await call(api, 'POST', '/tenant/lease/checkout', { leaseId, checkOutTime: localDateTime() });
          checkedOut = true;
          const room = await call(api, 'GET', `/room/${roomId}`);
          if (room.status !== 0) throw new Error('退房后房间状态未恢复为空置');
        } catch (error) {
          cleanupErrors.push(`退房失败：${error instanceof Error ? error.message : String(error)}`);
        }
      } else if (leaseId === undefined) {
        checkedOut = true;
      }

      if (checkedOut) {
        for (const [url, label] of [
          ...(roomId === undefined ? [] : [[`/room/delete/${roomId}`, '房间']]),
          ...(apartmentId === undefined ? [] : [[`/apartment/${apartmentId}`, '公寓']]),
          ...(tenantId === undefined ? [] : [[`/tenant/delete/${tenantId}`, '租客']]),
        ] as [string, string][]) {
          try {
            await call(api, 'DELETE', url);
          } catch (error) {
            cleanupErrors.push(`删除${label}失败：${error instanceof Error ? error.message : String(error)}`);
          }
        }
      }

      await api.dispose();
      if (cleanupErrors.length) throw new Error(cleanupErrors.join('；'));
    }
  },
});

export { expect } from './worker-account.fixture';
