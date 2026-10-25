import fs from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { request, test as base } from '@playwright/test';
import { getAuthStatePath } from '../auth-state';

type WorkerAccount = { id: number; username: string; password: string };

/** 构造本地管理员 API 上下文；令牌只从被忽略的浏览器登录态文件读取，不输出。 */
export async function createAdminApi() {
  const storageState = JSON.parse(await fs.readFile(getAuthStatePath(), 'utf8'));
  const token = storageState.origins
    ?.flatMap((origin: { localStorage?: { name: string; value: string }[] }) => origin.localStorage ?? [])
    .find((entry: { name: string }) => entry.name === 'accessToken')?.value;
  if (!token) throw new Error('管理员登录态未找到 accessToken，无法创建隔离测试数据');

  return request.newContext({
    baseURL: process.env.API_BASE_URL ?? 'http://localhost:8080',
    extraHTTPHeaders: { Authorization: `Bearer ${token}` },
  });
}

/** 通过管理员登录态创建临时维修工；fixture 退出时删除，UI 测试只读本人工单。 */
export const test = base.extend<{ workerAccount: WorkerAccount }>({
  workerAccount: async ({}, use) => {
    const api = await createAdminApi();
    let workerId: number | undefined;
    try {
      const rolesResponse = await api.get('/system/role/enabled');
      const rolesBody = await rolesResponse.json();
      if (!rolesResponse.ok() || rolesBody.code !== 200) {
        throw new Error(`获取维修工角色失败（HTTP ${rolesResponse.status()}，业务码 ${rolesBody.code}）`);
      }
      const workerRole = rolesBody.data.find((role: { roleCode: string; status: number }) =>
        role.roleCode === 'MAINTENANCE_WORKER' && role.status === 1);
      if (!workerRole) throw new Error('没有找到启用的维修工角色');

      const suffix = randomUUID().replaceAll('-', '').slice(0, 10);
      const username = `auto_ui_worker_${suffix}`;
      const password = 'Worker123!';
      const created = await api.post('/system/user', {
        data: {
          username,
          password,
          email: `${username}@example.com`,
          phone: `199${Date.now().toString().slice(-8)}`,
          status: 1,
          roleIds: [workerRole.id],
        },
      });
      const createdBody = await created.json();
      if (!created.ok() || createdBody.code !== 200 || !createdBody.data?.id) {
        throw new Error(`创建临时维修工失败（HTTP ${created.status()}，业务码 ${createdBody.code}）`);
      }
      const createdWorkerId = createdBody.data.id as number;
      workerId = createdWorkerId;
      await use({ id: createdWorkerId, username, password });
    } finally {
      if (workerId !== undefined) {
        const deleted = await api.delete(`/system/user/${workerId}`);
        const deletedBody = await deleted.json();
        if (!deleted.ok() || deletedBody.code !== 200) {
          throw new Error(`清理临时维修工失败（HTTP ${deleted.status()}，业务码 ${deletedBody.code}）`);
        }
      }
      await api.dispose();
    }
  },
});

export { expect } from '@playwright/test';
