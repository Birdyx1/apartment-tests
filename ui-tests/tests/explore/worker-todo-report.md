# 维修工端“待抢工单”页：测试矩阵与探索报告

## 范围与前置条件

- 起始 URL：`http://localhost:3002/worker-h5/todo`，属于维修工 H5。
- 登录用本地管理员登录态创建独立临时维修工账号，页面测试只读；测试结束由管理员接口删除该账号。
- 不点击抢单，不创建、接单、完成或取消工单。维修工端列表可能含其他测试/业务数据，因此只按本次接口响应核对当前页面，不修改或依赖某一固定工单。
- 预期依据：`worker-h5/src/pages/Todo/index.tsx`、`worker-h5/src/router/index.tsx`、`worker-h5/src/api/maintenance.ts` 和后端 `WorkerAppMaintenanceController.list`。

## 测试用例矩阵

| 用例 ID | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| WT-001 | 未登录访问待抢工单时跳转登录页 | 浏览器无维修工登录态 | 直接打开 `/worker-h5/todo` | 跳转 `/worker-h5/login`，显示维修工端登录表单 |
| WT-002 | 待抢工单列表正确加载 | 本用例专属临时维修工登录 | 打开待抢工单页；等待列表接口；根据本次响应核对列表或空状态 | `GET /worker-app/maintenance/list?tab=todo` 返回 HTTP 200；有数据时卡片与响应条数、标题一致；无数据时显示“暂无可抢工单” |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| WT-001 | `test('WT-001: 未登录访问待抢工单时跳转登录页')` |
| WT-002 | `test('WT-002: 待抢工单列表正确加载')` |

## CLI 探索和执行记录

- 有头 Playwright CLI 确认 H5 起始地址为 `http://localhost:3002/worker-h5/todo`；未登录直接访问后跳转至 `/worker-h5/login`。
- 页面标题为“待抢工单”，说明为“全平台可抢维修任务”；当前环境显示“暂无可抢工单”，底部导航为“抢单 / 我的工单 / 我的”。截图 `worker-todo-step1.png`；快照 `worker-todo-unauth-snapshot.md`、`worker-todo-snapshot.md`。
- CLI 真实网络记录：维修工登录 `POST /worker-app/auth/login` HTTP 200；列表 `GET /worker-app/maintenance/list?tab=todo` HTTP 200。当前响应列表为空。
- Locator 优先使用 role + accessible name：`getByRole('heading', { name: '待抢工单' })`、登录表单 textbox 与 button；卡片当前没有 testId，列表项用 `.apple-card`，标题用 `.maintenance-title`，并以运行时接口数据核对。
- 新增 `pages/worker-todo.page.ts` 和 `tests/test_worker_todo.spec.ts`，WT-001 至 WT-002 一一对应两个独立 test。WT-002 按接口实际返回逐条匹配卡片，若响应为空则验证空状态，不依赖某条外部种子工单。
- 临时维修工仅用于有头探索，已删除。最终回归 **2 passed（1.3s）**；没有抢单、创建或改变任何工单。两条用例均有 Playwright 截图、视频和 Trace；未修改产品代码。
