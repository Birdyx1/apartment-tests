# 租客 H5“我的”个人中心：测试矩阵与探索报告

## 页面范围与数据原则

- 页面 URL：`http://localhost:3001/tenant-h5/profile`，从底部“我的”导航进入。
- 预期依据：`tenant-h5/src/pages/Profile/index.tsx`、`tenant-h5/src/api/profile.ts` 和后端 `TenantAppProfileController`。
- 每条用例使用独立临时租客，不编辑资料；退出登录用例只清理本次认证状态，fixture 最后删除专属租客。

## 测试用例矩阵

| 用例 ID | 场景 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| TPF-001 | 个人中心显示本人资料 | 临时租客账号可登录 | 登录并打开“我的” | 页面姓名、性别、手机号、脱敏身份证与 `GET /tenant-app/profile` 和当前测试账号一致 |
| TPF-002 | 退出后不能访问个人中心 | 临时租客账号已登录 | 点击退出登录，再直接访问 `/tenant-h5/profile` | 返回租客登录页；无登录态不能停留在个人中心 |

## 用例与代码映射

| ID | 测试名称 |
|---|---|
| TPF-001 | `test('TPF-001: 个人中心展示当前租客资料')` |
| TPF-002 | `test('TPF-002: 退出登录后个人中心需要重新认证')` |

## Playwright CLI 探索记录

- 用 headed Playwright CLI 登录独立临时租客，从首页底部“我的”进入 `/tenant-h5/profile`。页面快照和截图见 `tenant-profile-page-snapshot.md`、`tenant-profile-page-step1.png`。
- 页面调用 `GET /tenant-app/profile`（HTTP 200），展示姓名、性别、手机号和脱敏身份证；接口数据与测试租客账号一致。退出登录调用 `POST /tenant-app/auth/logout`（HTTP 200），随后访问 `/tenant-h5/profile` 会重定向到 `/tenant-h5/login`；退出和未登录快照见 `tenant-profile-logout-snapshot.md`、`tenant-profile-unauth-snapshot.md`。
- 底部“我的”和“退出登录”在快照中是可点击文本节点，没有 `data-testid` 或可访问按钮名称；使用精确文本定位。资料字段使用 `.kv-row` + `.kv-label` 精确定位。当前无需为只读流程改产品代码。
- 自动化代码映射：TPF-001 → `test('TPF-001: 个人中心展示当前租客资料')`；TPF-002 → `test('TPF-002: 退出登录后个人中心需要重新认证')`，位于 `tests/test_tenant_profile.spec.ts`；导航和资料行封装在 `pages/tenant-profile.page.ts`。
- 用例分别创建并清理独立租客账号，不修改资料和业务数据。定向回归 **2 passed（1.7s）**；每条均生成截图、视频和 Trace。HTML 报告已在 Codex 中打开：`http://127.0.0.1:9341`。
