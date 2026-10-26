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
| TPF-003 | 编辑并保存个人资料 | 本用例专属临时租客已登录并进入个人中心 | 打开编辑表单，修改姓名、性别和手机号并保存 | 保存请求成功；个人中心及重新读取的 `GET /tenant-app/profile` 返回新值；其他身份证等资料保持不变 |

## 用例与代码映射

| ID | 测试名称 |
|---|---|
| TPF-001 | `test('TPF-001: 个人中心展示当前租客资料')` |
| TPF-002 | `test('TPF-002: 退出登录后个人中心需要重新认证')` |
| TPF-003 | `test('TPF-003: 编辑个人资料并保存')` |

## Playwright CLI 探索记录

- 用 headed Playwright CLI 登录独立临时租客，从首页底部“我的”进入 `/tenant-h5/profile`。页面快照和截图见 `tenant-profile-page-snapshot.md`、`tenant-profile-page-step1.png`。
- 页面调用 `GET /tenant-app/profile`（HTTP 200），展示姓名、性别、手机号和脱敏身份证；接口数据与测试租客账号一致。退出登录调用 `POST /tenant-app/auth/logout`（HTTP 200），随后访问 `/tenant-h5/profile` 会重定向到 `/tenant-h5/login`；退出和未登录快照见 `tenant-profile-logout-snapshot.md`、`tenant-profile-unauth-snapshot.md`。
- TPF-003 使用有头 CLI 打开“编辑个人信息”表单，快照在 `tenant-profile-edit-form-snapshot.md`，截图在 `tenant-profile-edit-form-step1.png`。表单有姓名文本框、性别 Selector（未知/男/女）、手机号文本框及取消/保存按钮；无 `data-testid`，按可访问名称和 option role 定位。保存调用 `PUT /tenant-app/profile`，随后重新读取 GET，页面和接口均展示更新后的姓名、性别与手机号，身份证保持原值。
- 底部“我的”和“退出登录”在快照中是可点击文本节点，没有 `data-testid` 或可访问按钮名称；使用精确文本定位。资料行使用 `.kv-row` + `.kv-label`，编辑框使用可访问名称定位。自动化代码映射 TPF-001 至 TPF-003 均在 `tests/test_tenant_profile.spec.ts`，导航、表单操作和资料行封装在 `pages/tenant-profile.page.ts`。
- 用例分别创建并清理独立租客账号；TPF-003 更新本用例账号后再删除。四模块联合定向回归中个人中心 **3 条全部通过**，均生成截图、视频和 Trace；HTML 报告已更新并重新打开。
