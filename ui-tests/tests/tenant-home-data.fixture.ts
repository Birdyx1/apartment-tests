import { randomUUID } from 'node:crypto';
import { test as base } from '@playwright/test';
import { createAdminApi } from './worker-account.fixture';

export type TenantAccount = { id: number; name: string; phone: string; password: string };
export type TenantHomeData = {
  apartmentName: string;
  apartmentAddress: string;
  apartmentContact: string;
  apartmentPhone: string;
  roomNo: string;
  layout: string;
  area: number;
  floor: number;
  checkInTime: string;
  deposit: number;
  monthlyRent: number;
  apartmentId: number;
  roomId: number;
  leaseId: number;
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

/** 创建本用例独立租客；依赖的房间 fixture 会先于此 fixture 清理。 */
export const test = base.extend<{ tenantAccount: TenantAccount; tenantHome: TenantHomeData }>({
  tenantAccount: async ({}, use) => {
    const api = await createAdminApi();
    let tenantId: number | undefined;
    const suffix = randomUUID().replaceAll('-', '').slice(0, 8);
    const account: Omit<TenantAccount, 'id'> = {
      name: `UI首页租客-${suffix}`,
      phone: `199${Date.now().toString().slice(-8)}`,
      password: 'Tenant123!',
    };
    try {
      const created = await call(api, 'POST', '/tenant/create', {
        name: account.name,
        gender: 1,
        phone: account.phone,
        idCard: `TEST${randomUUID().replaceAll('-', '').slice(0, 14)}`,
        password: account.password,
      });
      tenantId = created.id;
      await use({ id: tenantId, ...account });
    } finally {
      if (tenantId !== undefined) await call(api, 'DELETE', `/tenant/delete/${tenantId}`);
      await api.dispose();
    }
  },

  tenantHome: async ({ tenantAccount }, use) => {
    const api = await createAdminApi();
    let apartmentId: number | undefined;
    let roomId: number | undefined;
    let leaseId: number | undefined;
    let checkedOut = false;
    const suffix = randomUUID().replaceAll('-', '').slice(0, 8);
    const home: Omit<TenantHomeData, 'apartmentId' | 'roomId' | 'leaseId'> = {
      apartmentName: `UI首页公寓-${suffix}`,
      apartmentAddress: `自动化测试地址-${suffix}`,
      apartmentContact: `测试联系人-${suffix}`,
      apartmentPhone: '020-12345678',
      roomNo: `UI首页-${suffix}`,
      layout: '一室一厅',
      area: 36,
      floor: 3,
      checkInTime: localDateTime(),
      deposit: 800,
      monthlyRent: 1800,
    };
    try {
      apartmentId = (await call(api, 'POST', '/apartment', {
        name: home.apartmentName,
        address: home.apartmentAddress,
        contactName: home.apartmentContact,
        contactPhone: home.apartmentPhone,
      })).id;
      roomId = (await call(api, 'POST', '/room/create', {
        apartmentId,
        roomNo: home.roomNo,
        floor: home.floor,
        layout: home.layout,
        area: home.area,
        status: 0,
      })).id;
      leaseId = (await call(api, 'POST', '/tenant/lease', {
        tenantId: tenantAccount.id,
        roomId,
        checkInTime: home.checkInTime,
        leaseMonths: 1,
        deposit: home.deposit,
        monthlyRent: home.monthlyRent,
        rentDueDay: 1,
      })).id;

      await use({ ...home, apartmentId, roomId, leaseId });
    } finally {
      const cleanupErrors: string[] = [];
      if (leaseId !== undefined) {
        try {
          await call(api, 'POST', '/tenant/lease/checkout', { leaseId, checkOutTime: localDateTime() });
          checkedOut = true;
          const room = await call(api, 'GET', `/room/${roomId}`);
          if (room.status !== 0) throw new Error('退房后房间状态不是空置');
        } catch (error) {
          cleanupErrors.push(`退房或核验房间失败：${error instanceof Error ? error.message : String(error)}`);
        }
      } else {
        checkedOut = true;
      }

      if (checkedOut) {
        for (const [url, label] of [
          ...(roomId === undefined ? [] : [[`/room/delete/${roomId}`, '房间']]),
          ...(apartmentId === undefined ? [] : [[`/apartment/${apartmentId}`, '公寓']]),
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

export { expect } from '@playwright/test';
