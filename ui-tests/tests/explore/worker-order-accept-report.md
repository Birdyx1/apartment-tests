# 维修工 H5 已派工单接单测试

## 场景与前置条件

- 页面：维修工 H5 待抢工单列表 `/worker-h5/todo` 与工单详情 `/worker-h5/detail/{id}`。
- 每条用例由管理员 API 创建本轮专属维修工、在住租客及报修工单，再将工单派给该维修工；测试结束按“先取消工单、再退房”清理，避免污染现有数据。
- 派单接口：`PUT /maintenance-order/{id}/assign`，JSON `{ "assigneeId": workerId }`。接单接口：`PUT /worker-app/maintenance/{id}/accept`。

## 用例矩阵

| ID | 名称 | 前置 | 操作步骤 | 预期 |
|---|---|---|---|---|
| WA-001 | 取消接单确认后保持待处理 | 临时维修工登录；唯一工单已指派给该维修工且 status=0 | 打开待抢列表中的专属工单；点击“接单”；在确认框点击“取消” | 确认框关闭；详情仍显示“待处理”和当前指派维修工；“接单”按钮仍可见；管理员 API 查询 status=0、assigneeId 为当前维修工、handlerId 为空 |
| WA-002 | 确认接单后进入处理中 | 临时维修工登录；另一条独立唯一工单已指派给该维修工且 status=0 | 打开专属工单；点击“接单”；确认“确定” | 页面显示“处理中”、指派维修工及“完成工单”按钮；管理员 API 查询 status=1，assigneeId 与 handlerId 均为当前维修工 |

## 探索记录

- 使用 headed Playwright CLI 从 `/worker-h5/login` 登录本轮临时维修工，待抢列表显示该工单“待接单”，打开后地址为 `/worker-h5/detail/613`。
- 详情页面快照确认状态“待处理”、指派人为当前维修工，操作按钮为“接单”。点击后确认弹窗文案为“确认接此派单？”，按钮为“取消”和“确定”。
- 点击“取消”后弹窗关闭，页面仍为“待处理”，指派人不变，“接单”按钮仍显示。
- 再次确认接单后，页面刷新为“处理中”，出现“完成工单”操作。管理员只读查询 HTTP 200，业务码 200，status=1，assigneeId 与 handlerId 均为当前临时维修工 ID。
- 快照：`worker-order-accept-login-snapshot.md`、`worker-order-accept-todo-snapshot.md`、`worker-order-accept-detail-pending-snapshot.md`、`worker-order-accept-dialog-snapshot.md`、`worker-order-accept-cancelled-snapshot.md`、`worker-order-accept-detail-processing-snapshot.md`。
- 页面没有相应 `data-testid`；按钮和弹窗使用 role + accessible name（locator 优先级 2）；详情字段沿用已有 `.kv-row` / `.kv-label` 语义结构（CSS locator 优先级 4）。按钮和弹窗不存在可用的更高优先级 testId。
- CLI 截图命令等待字体后在 5 秒限制内超时；页面快照正常保存。测试运行会按 Playwright 配置为每条用例生成截图、视频和 Trace。
- 探索临时工单已取消并核对 status=3，随后退房并核对房间 status=0，已删除临时房间、公寓、租客和维修工。

## 用例到代码映射

| 用例 | 测试 |
|---|---|
| WA-001 | `test('WA-001: 取消接单确认后工单保持待处理')` |
| WA-002 | `test('WA-002: 确认接单后工单进入处理中')` |

## 代码定位与断言

- `WorkerOrderDetailPage.openAcceptConfirmation/cancelAccept/confirmAccept` 使用按钮与对话框的 role/name locator。
- WA-001 同时检查页面状态和管理员 API 返回的 status、assigneeId、handlerId，确保取消确认没有副作用。
- WA-002 观察 `PUT /worker-app/maintenance/{id}/accept`，核对 HTTP 与业务码，再检查处理中页面动作和后端状态/人员关联。
- 每条测试使用独立的动态租客入住链、工单与维修工；清理逻辑先取消工单，后退房并清理资源。

