import { randomUUID } from 'node:crypto';
import { createAdminApi } from './worker-account.fixture';
import { test as tenantTest } from './tenant-maintenance-list-data.fixture';
import type { TenantAccount } from './tenant-home-data.fixture';

async function apiCall(api: Awaited<ReturnType<typeof createAdminApi>>, method: string, url: string, payload?: unknown) {
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

/** 创建仅用于验证工单归属隔离的临时第二租客。 */
export const test = tenantTest.extend<{ otherTenantAccount: TenantAccount }>({
  otherTenantAccount: async ({}, use) => {
    const api = await createAdminApi();
    let tenantId: number | undefined;
    const suffix = randomUUID().replaceAll('-', '').slice(0, 8);
    const account = {
      name: `UI越权验证租客-${suffix}`,
      phone: `199${Date.now().toString().slice(-8)}`,
      password: 'Tenant123!',
    };

    try {
      const created = await apiCall(api, 'POST', '/tenant/create', {
        name: account.name,
        gender: 1,
        phone: account.phone,
        idCard: `TEST${randomUUID().replaceAll('-', '').slice(0, 14)}`,
        password: account.password,
      });
      tenantId = created.id;
      await use({ id: tenantId, ...account });
    } finally {
      try {
        if (tenantId !== undefined) await apiCall(api, 'DELETE', `/tenant/delete/${tenantId}`);
      } finally {
        await api.dispose();
      }
    }
  },
});

export { expect } from './tenant-home-data.fixture';
