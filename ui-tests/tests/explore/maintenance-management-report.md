# 维修工单管理：测试矩阵与探索报告

## 输入与范围

- 起始 URL：`http://localhost:3000/maintenance-order/manage`。
- 前置条件：现有管理员登录态有效，具备 `maintenance:list` 与 `maintenance:handle` 权限。
- 本轮先覆盖管理员工单列表与筛选交互，不在探索时修改工单状态或派单，避免改变现有数据。
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

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| MM-001 | `test('MM-001: 工单管理列表与筛选控件加载')` |
| MM-002 | `test('MM-002: 按工单状态筛选')` |
| MM-003 | `test('MM-003: 按紧急程度筛选')` |
| MM-004 | `test('MM-004: 重置工单筛选条件')` |
| MM-005 | `test('MM-005: 刷新工单列表')` |

## 探索记录

- 使用本机管理员登录态通过 `playwright-cli` 打开 `/maintenance-order/manage`。列表显示 10 列：房间、租客、标题、描述、紧急程度、状态、指派、处理备注、申请时间、操作；筛选项为房间、租客、状态和紧急程度，另有搜索、重置、刷新。
- 页面初始有两条历史已取消工单；仅查看，没有修改或取消。当前两条均为“普通”紧急程度。
- 状态过滤快照：`maintenance-management-status-filter-snapshot.md`。选择“已取消”后请求 `GET /maintenance-order/list?status=3`，页面返回两条已取消记录。
- 重置快照：`maintenance-management-reset-snapshot.md`。状态和紧急程度同时选择后，请求参数为 `status=3&urgency=2`；点击重置后发起无筛选参数的列表请求。
- CLI 的 request 检查只查看路径和查询参数，未读取授权信息或个人资料：`GET /maintenance-order/list`、`?status=3`、`?status=3&urgency=2`、重置后的无参请求均返回 HTTP 200。
- Locator 采用优先级 2 role + 可访问名称定位筛选、按钮、列头；Ant Design 下拉选项限定在可见 popup 中使用 title。选中标签通过表单项内 `.ant-select-selection-item` 检查；真实数据行限定为 `.ant-table-tbody > tr.ant-table-row`，排除也有 row/cell role 的“暂无数据”占位行。
- UI 用例映射为 `tests/test_maintenance_management.spec.ts` 中 MM-001 至 MM-005；页面操作封装在 `pages/maintenance-management.page.ts`。仅做列表和筛选测试，无新建工单，无测试数据清理需求。

## 自动化执行结果

- 首轮因读取 Ant Design combobox 输入框作为选中值，及把“暂无数据”占位行识别成工单而失败；用户确认后按两轮以内完成 locator 修复，未修改产品代码。
- 最终定向回归：`5 passed (4.6s)`，与矩阵 5 条一致。
- 每条用例均生成截图、视频和 Trace；HTML 报告位于 `playwright-report/`。本轮未运行全项目回归，也未向 Allure 目录追加 UI 结果。
