# 租客 H5“维修工单”页：测试矩阵与探索报告

## 页面范围与数据原则

- 页面入口：`http://localhost:3001/tenant-h5/maintenance/list`，租客 H5 的“维修工单”列表。
- 预期依据：`tenant-h5/src/pages/Maintenance/List/index.tsx`、`tenant-h5/src/api/maintenance.ts`、后端 `TenantAppMaintenanceController.list`。
- 每个已登录场景使用独立临时租客；有工单场景创建独立公寓、房间、入住记录，再以该租客身份提交一条工单。结束时先取消工单，再退房并清理依赖数据。
- 不修改产品代码，不触碰既有租客或工单。

## 测试矩阵

| 用例 ID | 场景 | 前置条件 | 验证点 |
|---|---|---|---|
| TML-001 | 租客查看自己的待处理工单 | 专属租客有在住记录，并以租客身份创建一条紧急工单 | 列表接口返回该工单且只包含本租客数据；页面展示标题、描述、房间号、紧急程度和待处理状态 |
| TML-002 | 无工单时显示空状态 | 专属新租客没有入住和工单 | 列表接口返回空数组；页面显示“暂无工单” |

## CLI 探索和执行记录

- 用 Playwright Test fixture 创建专属租客、入住和维修工单后，以 headed Playwright CLI attach 浏览器；实际入口为 `http://localhost:3001/tenant-h5/maintenance/list`，页面标题为“租客端”。
- 可访问性快照：`tenant-maintenance-list-snapshot.md`；页面截图：`tenant-maintenance-list-step1.png`。页面结构确认有“维修工单”标题、描述、订单标题、状态、报修描述、房间号、紧急程度、创建时间、“取消”按钮和“+”入口。
- 真实网络记录：`POST /tenant-app/auth/login` 返回 200；登录后的 `GET /tenant-app/maintenance/list` 返回 200。页面请求该列表接口后展示测试租客自己的待处理工单。
- 定位策略：登录表单使用 role + accessible name；工单卡片使用 `.apple-card` + 唯一动态标题过滤，项目页面未提供对应 `data-testid`。
- 用例映射：TML-001 → `test('TML-001: 租客查看自己的待处理工单')`；TML-002 → `test('TML-002: 无工单时显示空状态')`。
- 新增 `pages/tenant-maintenance-list.page.ts`、`tests/tenant-maintenance-list-data.fixture.ts` 和 `tests/test_tenant_maintenance_list.spec.ts`。TML-001 通过专属租客身份创建测试工单，teardown 使用管理员 API 先取消并核对终态，随后由入住 fixture 退房和清理房间、公寓及租客；TML-002 只创建并清理临时租客。
- 定向回归 **2 passed（1.8s）**。两条用例均生成截图、视频和 Trace；测试创建的业务数据已按 fixture teardown 清理，未修改产品代码。HTML 报告已在 Codex 中打开：`http://127.0.0.1:9335`。
