# 维修工端抢单状态测试：用例矩阵与探索报告

## 范围与测试数据

- 页面：维修工 H5 工单详情 `/worker-h5/detail/{id}`，从待抢列表 `/worker-h5/todo` 进入。
- 数据：每条用例各自创建临时维修工、临时公寓/房间/租客/入住关系及唯一待处理工单。
- 清理：管理员取消工单并验证状态 3；再退房、验证房间空置，清理临时房间/公寓/租客和维修工账号。工单与退房记录保留为历史。
- 依据：维修工端 `Detail/index.tsx` 与后端 `WorkerAppMaintenanceController.grab`、`MaintenanceOrderServiceImpl.grabOrder/cancelByAdmin`。

## 测试用例矩阵

| 用例 ID | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| WG-001 | 取消抢单确认时工单保持待抢状态 | 专属维修工已登录；有唯一待处理、未指派工单 | 进入详情，点击“抢单”，在确认框选择取消 | 确认框关闭；详情仍为“待处理”“未派（可抢）”；“抢单”按钮仍可见；后端仍为 status=0、无 assignee |
| WG-002 | 确认抢单后工单进入处理中 | 专属维修工已登录；有唯一待处理、未指派工单 | 进入详情，点击“抢单”，确认操作 | 成功提示；后端 status=1 且 assignee/handler 为当前维修工；详情展示处理中与维修工姓名，并显示“完成工单”按钮 |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| WG-001 | `test('WG-001: 取消确认后工单保持待抢状态')` |
| WG-002 | `test('WG-002: 确认抢单后工单进入处理中')` |

## CLI 探索和执行记录

- headed CLI 从维修工待抢列表打开本轮专属工单详情；抢单前详情为“待处理”“未派（可抢）”，操作入口为 `button[name="抢单"]`。
- 点击后出现可访问对话框“确认抢此工单？”，其中有“取消”和“确定”按钮。取消路径不发抢单请求，页面状态不变；确认路径发出 `PUT /worker-app/maintenance/{id}/grab`（HTTP 200），随后 `GET /worker-app/maintenance/{id}` 刷新（HTTP 200）。
- 确认后的真实页面显示“处理中”、维修工账号和“完成工单”按钮；快照见 `worker-order-grab-claimed-snapshot.md`。弹窗和确认后的截图分别是 `worker-order-grab-step1.png`、`worker-order-grab-step2.png`。
- 新增 `tests/test_worker_order_grab.spec.ts`，WG-001 与 WG-002 各自创建独立账号和业务数据；测试用管理员查询工单详情，断言 status、assigneeId、handlerId。fixture 收尾取消工单并核验状态，再退房、核验房间空置并清理临时依赖和账号。
- 定向回归 **2 passed（4.0s）**；每条测试都有 HTML 报告截图、视频和 Trace。测试结果目录为 `test-results/`。
- 探索数据清理已核验：专属工单取消、入住退房完成、房间空置，临时房间/公寓/租客/维修工账号已清理；取消工单和退房记录保留为业务历史。
