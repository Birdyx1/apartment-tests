# 维修工 H5“我的”个人中心测试

## 场景与前置条件

- 页面：维修工 H5 个人中心 `/worker-h5/profile`，通过底部“我的”导航进入。
- 每条用例创建本用例专属的临时维修工账号；账号没有工单和入住依赖，退出测试后删除账号。
- 个人资料接口：`GET /worker-app/profile`，返回当前用户的 id、username、realName、phone 与 apartments。

## 用例矩阵

| ID | 名称 | 前置 | 操作步骤 | 预期 |
|---|---|---|---|---|
| WP-001 | 打开个人中心并显示当前账号信息 | 本用例专属临时维修工已登录 | 等待个人资料请求；点击底部“我的” | 进入 `/worker-h5/profile`；头像/姓名显示当前账号；账号、手机字段与个人资料接口和临时维修工数据一致 |
| WP-002 | 退出登录后不能再次访问个人中心 | 本用例专属临时维修工已登录并位于个人中心 | 点击“退出登录”；随后直接访问 `/worker-h5/profile` | 退出后跳转 `/worker-h5/login`；直接访问受保护页面仍被重定向到登录页 |

## 探索记录

- 使用 headed Playwright CLI 登录本轮临时维修工，从待抢列表底部点击“我的”后进入 `/worker-h5/profile`。
- 个人中心展示头像首字母、用户名、账号信息、手机号和“退出登录”；临时账号无 realName 时，头像与名称回退显示 username。
- 接口 `GET /worker-app/profile` 返回当前维修工账号和手机号，页面展示值与临时账号数据一致。
- 点击“退出登录”后跳转 `/worker-h5/login`；在退出状态直接打开 `/worker-h5/profile` 仍停留在登录页。
- 快照：`worker-profile-login-snapshot.md`、`worker-profile-todo-snapshot.md`、`worker-profile-page-snapshot.md`。底部导航使用可见文本“我的”；个人信息行沿用 `.kv-row` / `.kv-label` 结构；退出项当前无 button role，按精确文本定位（文本 locator 优先级 2）。
- 探索账号已删除，无遗留测试业务数据。

## 用例到代码映射

| 用例 | 测试 |
|---|---|
| WP-001 | `test('WP-001: 个人中心显示当前维修工账号信息')` |
| WP-002 | `test('WP-002: 退出登录后个人中心受登录保护')` |

## 验证结果

- 个人中心定向回归：2 passed（1.7s），两条用例均生成截图、视频和 Trace。
- 由于 `worker-account.fixture.ts` 新增返回手机号以支持账号信息核对，又运行全部维修工 H5 用例回归：16 passed（18.5s）。
- 个人中心测试只创建临时维修工账号；fixture teardown 已删除账号。未创建或变更工单。

