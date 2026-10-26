# 维修工单管理：测试矩阵与探索报告

## 输入与范围

- 起始 URL：`http://localhost:3000/maintenance-order/manage`。
- 前置条件：现有管理员登录态有效，具备 `maintenance:list` 与 `maintenance:handle` 权限。
- MM-001 至 MM-005 覆盖管理员工单列表与筛选；MM-006 使用本用例专属待处理工单和临时维修工验证派单，不修改任何现有工单。
- 后端没有删除维修工单接口；创建后的临时工单需要取消并保留为终态记录。因此本组初版优先用只读/筛选验证，不依赖共享测试订单。
- 预期来源：前端 `MaintenanceOrder/Management.tsx` 表格列、状态/紧急程度枚举与查询表单；后端 `MaintenanceOrderController.list` 查询参数契约。实际页面状态、可访问名称和请求参数仍待 CLI 确认。

## 测试用例矩阵

| 用例 ID | 用例名称 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| MM-001 | 工单管理列表与筛选控件加载 | 管理员登录态及列表权限 | 打开工单管理页，核对表头、筛选和刷新入口 | 显示房间、租客、标题、描述、紧急程度、状态、指派、处理备注、申请时间、操作；筛选控件可用 |
| MM-002 | 按工单状态筛选 | 管理员登录态 | 选择“已取消”，点击搜索 | 列表请求携带 `status=3`；若返回记录，每条状态均显示已取消 |
| MM-003 | 按紧急程度筛选 | 管理员登录态 | 选择“紧急”，点击搜索 | 列表请求携带 `urgency=2`；若返回记录，每条紧急程度均显示紧急 |
| MM-004 | 重置筛选条件 | 管理员登录态 | 设置状态和紧急程度筛选后搜索，点击重置 | 两个筛选项清空；后续列表请求不带这两个筛选参数 |
| MM-005 | 刷新工单列表 | 管理员登录态 | 点击刷新 | 重新请求工单列表，表格加载结束且筛选值保持不变 |
| MM-006 | 为待处理工单派单 | 本用例专属待处理工单和临时维修工账号；管理员有派单权限 | 在目标工单行点击“派单”，选择临时维修工并确认 | 派单请求成功；页面显示指派人；管理员 API 查询确认工单状态仍待处理且 assigneeId 正确；teardown 取消工单后清理依赖 |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| MM-001 | `test('MM-001: 工单管理列表与筛选控件加载')` |
| MM-002 | `test('MM-002: 按工单状态筛选')` |
| MM-003 | `test('MM-003: 按紧急程度筛选')` |
| MM-004 | `test('MM-004: 重置工单筛选条件')` |
| MM-005 | `test('MM-005: 刷新工单列表')` |
| MM-006 | `test('MM-006: 管理员为待处理工单派单')` |

## 探索记录

- 使用本机管理员登录态通过 `playwright-cli` 打开 `/maintenance-order/manage`。列表显示 10 列：房间、租客、标题、描述、紧急程度、状态、指派、处理备注、申请时间、操作；筛选项为房间、租客、状态和紧急程度，另有搜索、重置、刷新。
- 页面初始有两条历史已取消工单；仅查看，没有修改或取消。当前两条均为“普通”紧急程度。
- 状态过滤快照：`maintenance-management-status-filter-snapshot.md`。选择“已取消”后请求 `GET /maintenance-order/list?status=3`，页面返回两条已取消记录。
- 重置快照：`maintenance-management-reset-snapshot.md`。状态和紧急程度同时选择后，请求参数为 `status=3&urgency=2`；点击重置后发起无筛选参数的列表请求。
- CLI 的 request 检查只查看路径和查询参数，未读取授权信息或个人资料：`GET /maintenance-order/list`、`?status=3`、`?status=3&urgency=2`、重置后的无参请求均返回 HTTP 200。
- Locator 采用优先级 2 role + 可访问名称定位筛选、按钮、列头；Ant Design 下拉选项限定在可见 popup 中使用 title。选中标签通过表单项内 `.ant-select-selection-item` 检查；真实数据行限定为 `.ant-table-tbody > tr.ant-table-row`，排除也有 row/cell role 的“暂无数据”占位行。
- MM-006 用 headed CLI 创建并打开临时待处理工单的“派单”弹窗，快照分别为 `maintenance-dispatch-list-snapshot.md`、`maintenance-dispatch-modal-snapshot.md` 和 `maintenance-dispatch-worker-options-snapshot.md`，成功后截图为 `maintenance-dispatch-success-step1.png`。点击行内“派单”后，页面调用 `GET /maintenance-order/workers?apartmentId=...`，下拉选项包含本轮临时维修工；选择后点击“确定”调用 `PUT /maintenance-order/{id}/assign` HTTP 200，刷新列表显示指派维修工。
- 派单弹层由 Ant Design portal 渲染在 dialog 外。自动化将候选项限定为可见 `.ant-select-dropdown .ant-select-item-option`，并先断言选择框已显示目标账号，再确认提交；订单行用唯一标题定位。
- UI 用例映射：MM-001 至 MM-005 在 `tests/test_maintenance_management.spec.ts`；MM-006 在 `tests/test_maintenance_dispatch.spec.ts`；对应筛选、行定位和派单操作封装于 `pages/maintenance-management.page.ts`。派单用例结束时 fixture 取消测试工单并核验终态，再退房、核验房间空置、清理可删除依赖和临时维修工账号。测试工单作为已取消历史记录保留。

## 自动化执行结果

- 首轮因读取 Ant Design combobox 输入框作为选中值，及把“暂无数据”占位行识别成工单而失败；用户确认后按两轮以内完成 locator 修复，未修改产品代码。
- 列表筛选原有回归 **5 passed（4.6s）**；新增派单用例在四模块联合定向回归中通过。所有派单用例均生成截图、视频和 Trace；最新 HTML 报告包含本轮派单结果。
