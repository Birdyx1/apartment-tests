import path from 'node:path';

/** UI 登录态只保存在本机或 Jenkins 工作区的忽略目录中。 */
export function getAuthStatePath(): string {
  const configuredPath = process.env.PW_STORAGE_STATE;
  return configuredPath
    ? path.resolve(process.cwd(), configuredPath)
    : path.resolve(__dirname, 'tests/.auth/admin.json');
}
