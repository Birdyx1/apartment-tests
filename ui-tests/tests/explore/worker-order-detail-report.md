# 维修工端工单详情：测试矩阵与探索报告

## 范围与测试数据

- 起始路径：维修工 H5 `http://localhost:3002/worker-h5/todo`。
- 使用独立临时维修工和临时业务链：公寓 → 房间 → 租客 → 入住 → 待处理维修工单。工单标题唯一，以便从待抢列表准确打开。
- 测试只读浏览待处理工单详情，不点击“抢单”。清理顺序：取消本次工单 → 退房 → 删除房间/公寓/租客 → 删除维修工账号。
- 后端没有维修工单物理删除接口；本次唯一测试工单会作为已取消历史记录保留。不得触碰其他工单。
- 预期依据：`worker-h5/src/pages/Todo/index.tsx`、`worker-h5/src/pages/Detail/index.tsx`、后端 `WorkerAppMaintenanceController` 和 `MaintenanceOrderController`。

## 测试用例矩阵

| 用例 ID | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| WD-001 | 维修工从待抢列表打开工单详情 | 专属维修工账号已登录；本用例专属租客已入住且存在唯一待处理工单 | 打开待抢列表；点击唯一工单卡片；核对详情并返回列表 | URL 为详情路由；标题、房间、租客、紧急程度、待处理状态、未派状态和描述与本次测试数据一致；页面显示抢单入口但不执行；返回后回到待抢列表 |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| WD-001 | `test('WD-001: 维修工从待抢列表打开工单详情')` |

## CLI 探索和执行记录

- 有头探索从 `/worker-h5/todo` 打开唯一测试工单，详情路由为 `/worker-h5/detail/{id}`；`GET /worker-app/maintenance/list?tab=todo` 和 `GET /worker-app/maintenance/{id}` 均返回 HTTP 200。
- 详情快照保存在 `worker-order-detail-snapshot.md`：页面展示标题、房间、公寓、租客、紧急程度、待处理状态、未派状态、描述、处理记录和“抢单”按钮。测试只读取按钮，不点击状态操作。
- 定位方式：工单卡片按唯一标题定位；详情字段用 `.kv-row` 内对应 `.kv-label` 定位；返回控件通过 `.adm-nav-bar-back` 定位。快照中无障碍名称的控件才使用 CSS 选择器。
- 新增 `pages/worker-order-detail.page.ts`、`tests/worker-detail-data.fixture.ts`、`tests/test_worker_order_detail.spec.ts`。fixture 创建临时维修工和完整入住报修链，退出时先取消工单并验证状态为 3，再退房并验证房间状态为 0，最后删除可删除的房间、公寓、租客和维修工账号。工单和退房记录按业务设计保留为历史。
- 定向详情回归 **1 passed（1.5s）**；共享维修工账号 fixture 的待抢列表回归 **2 passed（1.4s）**。详情用例有截图、视频和 Trace，保存在 `test-results/`。
- 清理核验：探索时的历史工单已取消；其专属租约退房成功、房间验证为空置，临时公寓/房间/租客及维修工账号清理完成。取消工单作为历史记录保留。
