/** 为 Jenkins 容器中的浏览器转发前端内置的 localhost API 请求。 */
export function getBrowserLaunchArgs(): string[] {
  const localhostTarget = process.env.PW_LOCALHOST_TARGET?.trim();
  return localhostTarget
    ? [`--host-resolver-rules=MAP localhost ${localhostTarget}`]
    : [];
}
