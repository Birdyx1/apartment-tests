import { randomUUID } from 'node:crypto';
import { test as base } from './tenant-home-data.fixture';
import { createAdminApi } from './worker-account.fixture';

export type TenantNotice = { id: number; title: string; content: string };

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

export const test = base.extend<{ tenantNotice: TenantNotice }>({
  tenantNotice: async ({}, use) => {
    const api = await createAdminApi();
    let noticeId: number | undefined;
    const suffix = randomUUID().replaceAll('-', '').slice(0, 8);
    const notice = {
      title: `UI自动化公告-${suffix}`,
      content: `公告详情正文-${suffix}\n第二行：用于校验换行内容完整展示。`,
    };

    try {
      noticeId = (await call(api, 'POST', '/notice', notice)).id;
      await call(api, 'PUT', `/notice/${noticeId}/publish`);
      await use({ id: noticeId, ...notice });
    } finally {
      if (noticeId !== undefined) await call(api, 'DELETE', `/notice/${noticeId}`);
      await api.dispose();
    }
  },
});

export { expect } from '@playwright/test';
