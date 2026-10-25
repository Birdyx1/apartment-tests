# 维修工端“我的工单”页：测试矩阵与探索报告

## 范围与前置条件

- 起始 URL：`http://localhost:3002/mine`；页面属于维修工 H5，不是管理端。
- 每条已登录用例使用独立临时维修工账号：通过本地管理员登录态调用角色/用户接口创建，登录后仅读取该维修工的“我的工单”列表，结束时通过管理员接口删除账号。
- 新账号没有历史接单记录；不创建、指派、抢单、完成或取消工单，不修改现有维修业务数据。
- 预期依据：`worker-h5/src/pages/MyOrders/index.tsx`、`worker-h5/src/router/index.tsx`、`worker-h5/src/api/maintenance.ts` 和后端 `WorkerAppMaintenanceController.list`。

## 测试用例矩阵

| 用例 ID | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| WM-001 | 未登录访问我的工单时跳转登录页 | 浏览器无维修工登录态 | 直接打开 `/mine` | 跳转 `/login`，显示维修工端登录表单 |
| WM-002 | 维修工默认查看处理中工单 | 新建临时维修工并登录 | 打开“我的工单”页 | 处理中 tab 默认选中；请求 mine + status=1；新账号显示暂无工单 |
| WM-003 | 查看已完成工单 | 新建临时维修工并登录 | 点击“已完成” | 请求 mine + status=2；新账号显示暂无工单 |
| WM-004 | 查看全部本人工单 | 新建临时维修工并登录 | 点击“全部” | 请求 mine 且不带 status；新账号显示暂无工单 |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| WM-001 | `test('WM-001: 未登录访问我的工单时跳转登录页')` |
| WM-002 | `test('WM-002: 维修工默认查看处理中工单')` |
| WM-003 | `test('WM-003: 查看已完成工单')` |
| WM-004 | `test('WM-004: 查看全部本人工单')` |

## CLI 探索和执行记录

- 有头 Playwright CLI 实际入口：`http://localhost:3002/worker-h5/`（H5 部署 base path 为 `/worker-h5/`）。直接访问 `/login` 会 404；正确登录路径为 `/worker-h5/login`。未登录打开 `/worker-h5/mine` 后实际跳转 `/worker-h5/login`。
- 快照：`worker-my-orders-login-snapshot.md`、`worker-my-orders-unauth-snapshot.md`、`worker-my-orders-snapshot.md`、`worker-my-orders-completed-snapshot.md`、`worker-my-orders-all-snapshot.md`。未登录页截图：`worker-my-orders-unauth.png`。
- 登录表单 locator：`getByRole('textbox', { name: /用户名/ })`、`getByRole('textbox', { name: /密码/ })`、`getByRole('button', { name: '登录' })`。列表页 locator：`getByRole('heading', { name: '我的工单' })`、`getByRole('tab', { name })`、`getByText('暂无工单')`。
- CLI 真实网络记录：登录 `POST /worker-app/auth/login` 返回 200；默认处理中请求 `GET /worker-app/maintenance/list?tab=mine&status=1` 返回 200；已完成筛选增加 `status=2`；全部筛选为 `tab=mine` 且不传 `status`，返回 200。
- 通过管理员登录态创建一个临时维修工用于 CLI 登录，页面只读；探索结束后已删除账号。没有创建或改变任何工单。
- 页面对象：`pages/worker-my-orders.page.ts`；临时账号生命周期 fixture：`tests/worker-account.fixture.ts`；用例文件：`tests/test_worker_my_orders.spec.ts`。WM-001 至 WM-004 一一映射至 4 个独立 test。初次运行发现 WM-001 页面对象把预期的登录重定向当成工单页加载失败，经确认后拆分导航和成功态断言；没有修改产品代码。
- 最终定向回归 **4 passed（2.3s）**；每条均生成截图、视频和 Trace。三条登录用例各创建一个唯一维修工账号并在 teardown 删除；WM-001 不创建账号。无业务工单写操作。
