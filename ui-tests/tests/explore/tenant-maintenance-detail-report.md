# 租客 H5“工单详情”页：测试矩阵与探索报告

## 页面范围与数据原则

- 起始 URL：`http://localhost:3001/tenant-h5/maintenance/detail/{id}`，租客 H5 维修工单详情页。
- 预期依据：`tenant-h5/src/pages/Maintenance/Detail/index.tsx`、`tenant-h5/src/api/maintenance.ts`、后端 `TenantAppMaintenanceController.detail/cancel`。
- 每条用例使用独立租客及专属待处理工单。越权场景由第二个临时租客访问该工单；所有临时租客和房间数据独立。
- 取消场景在 UI 内取消工单。teardown 校验终态后再退房，避免清理掉工单所依赖的住房。

## 测试矩阵

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---|---|---|---|---|
| TMD-001 | 租客查看本人待处理工单详情 | 本租客有在住记录并创建专属待处理工单 | 登录本人账号并打开详情页 | 详情接口与页面显示标题、状态、紧急程度、描述、申请时间；处理记录包含创建记录；显示取消按钮 |
| TMD-002 | 租客不能查看他人工单 | 工单属于租客 A；租客 B 是独立账号 | 租客 B 直接打开该工单详情 URL | 详情接口返回业务码 403 和“无权访问该工单”；页面提示并跳回工单列表 |
| TMD-003 | 租客取消本人待处理工单 | 本租客拥有待处理工单 | 在详情页点击“取消工单” | 取消接口成功，跳回列表；管理员接口核对工单状态为已取消（3） |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| TMD-001 | `test('TMD-001: 租客查看本人待处理工单详情')` |
| TMD-002 | `test('TMD-002: 租客不能查看他人工单')` |
| TMD-003 | `test('TMD-003: 租客取消本人待处理工单')` |

## CLI 探索和执行记录

- headed Playwright CLI 使用专属租客打开详情路由；页面快照为 `tenant-maintenance-detail-snapshot.md`，截图为 `tenant-maintenance-detail-step1.png`。详情请求 `GET /tenant-app/maintenance/{id}` 返回 200；处理记录显示 `create` 操作。
- 在探索数据上点击“取消工单”后，实际请求 `PUT /tenant-app/maintenance/{id}/cancel` 返回 200，随后列表请求返回 200 并留在工单列表。fixture 验证工单已取消后再退房清理。
- 用例映射：TMD-001 → `test('TMD-001: 租客查看本人待处理工单详情')`；TMD-002 → `test('TMD-002: 租客不能查看他人工单')`；TMD-003 → `test('TMD-003: 租客取消本人待处理工单')`。
- 新增详情 Page Object、独立第二租客 fixture 及三条用例。TMD-002 真实验证详情接口业务码 403、提示“无权访问该工单”并重定向列表；TMD-003 通过管理员接口核对数据库状态为 3。
- 定向回归 **3 passed（3.0s）**。三条用例均生成截图、视频和 Trace；成功取消后才退房清理，所有临时租客/房间数据已清理。HTML 报告已在 Codex 中打开：`http://127.0.0.1:9337`。未修改产品代码。
