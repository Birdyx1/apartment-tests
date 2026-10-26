# 租客 H5“申请维修”页：测试矩阵与探索报告

## 页面范围与数据原则

- 起始 URL：`http://localhost:3001/tenant-h5/maintenance/apply`，租客 H5 申请维修表单。
- 预期依据：`tenant-h5/src/pages/Maintenance/Apply/index.tsx`、`tenant-h5/src/api/maintenance.ts`、后端 `TenantAppMaintenanceController.create`。
- 有效提交场景使用本用例专属租客和在住房间；无入住场景使用专属空租客。只操作本轮测试创建的数据。
- 成功创建的工单结束时必须先取消并核对已取消状态，再退房清理住房数据。

## 测试矩阵

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---|---|---|---|---|
| TMA-001 | 租客成功提交紧急维修申请 | 专属租客有有效入住 | 填写标题和描述，选择“非常紧急”，提交 | 创建接口成功；跳转工单列表；新工单可见，状态待处理、紧急程度非常紧急，房间号正确 |
| TMA-002 | 工单标题必填 | 专属已登录租客 | 标题留空并提交 | 页面提示“请输入工单标题”；不调用创建接口，仍停留在申请页 |
| TMA-003 | 无入住时不能提交维修申请 | 专属租客没有入住记录 | 填写标题后提交 | 创建接口业务码 500，提示“您当前没有在住记录，无法申请工单”；页面不离开申请表单 |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| TMA-001 | `test('TMA-001: 租客成功提交紧急维修申请')` |
| TMA-002 | `test('TMA-002: 工单标题必填')` |
| TMA-003 | `test('TMA-003: 无入住时不能提交维修申请')` |

## CLI 探索和执行记录

- headed Playwright CLI 已登录专属在住租客并打开表单。实际地址为 `http://localhost:3001/tenant-h5/maintenance/apply`；快照为 `tenant-maintenance-apply-snapshot.md`，空表单校验快照为 `tenant-maintenance-apply-validation-snapshot.md`，截图为 `tenant-maintenance-apply-step1.png`。
- 页面 locator：标题 textbox（名称含“工单标题”）、描述 textbox（“问题描述”）、`option` 角色的“紧急/非常紧急”、按钮“提交申请”。空表单点击提交后页面仍留在申请表单，出现“请输入工单标题”；没有发出创建工单请求。项目当前未为表单控件提供 `data-testid`。
- 实际接口：`POST /tenant-app/maintenance/create`。后端无在住记录时返回 HTTP 200、业务码 400、消息“您当前没有在住记录，无法申请工单”；前端 API 拦截器会显示此消息并保留表单。
- 用例映射：TMA-001 → `test('TMA-001: 租客成功提交紧急维修申请')`；TMA-002 → `test('TMA-002: 工单标题必填')`；TMA-003 → `test('TMA-003: 无入住时不能提交维修申请')`。
- 已新增租客申请页 Page Object、用于登记成功创建工单并在退房前取消的 fixture，以及三条独立用例。
- 定向回归 **3 passed（3.0s）**。三条用例均生成截图、视频和 Trace；成功测试工单已取消并确认终态，租客、房间和入住数据已清理。HTML 报告已在 Codex 中打开：`http://127.0.0.1:9336`。未修改产品代码。
