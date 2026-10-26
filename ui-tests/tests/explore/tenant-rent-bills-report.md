# 租客 H5“房租账单”页：测试矩阵与探索报告

## 页面范围与数据原则

- 列表起始 URL：`http://localhost:3001/tenant-h5/rent/list`；详情 URL：`/tenant-h5/rent/detail/{id}`。
- 预期依据：`tenant-h5/src/pages/Rent/List/index.tsx`、`tenant-h5/src/pages/Rent/Detail/index.tsx`、`tenant-h5/src/api/rent.ts` 和后端 `TenantAppRentController`。
- 有账单场景使用专属租客及测试入住；入住接口会自动按当月房租生成唯一测试账单。无账单场景使用没有入住记录的专属租客。
- 本轮只验证列表、详情和支付入口展示，不提交支付，也不改变账单支付状态。

## 测试矩阵

| 用例 ID | 场景 | 前置条件 | 操作 | 预期结果 |
|---|---|---|---|---|
| TRB-001 | 账单列表显示完整账单信息 | 专属租客有入住记录和当月账单 | 打开账单列表 | 列表接口和卡片显示账期、金额、应缴日期、公寓/房间和状态 |
| TRB-002 | 打开账单详情 | 专属租客有入住记录和当月账单 | 在列表点击账单卡片 | 详情接口与测试数据一致，展示应缴日期、房间、金额和支付入口；不实际发起支付 |
| TRB-003 | 无账单时显示空状态 | 专属租客无入住记录 | 打开账单列表 | 列表接口返回空数组，页面显示“暂无账单” |

## 用例与代码映射

| ID | 计划测试名称 |
|---|---|
| TRB-001 | `test('TRB-001: 账单列表显示完整账单信息')` |
| TRB-002 | `test('TRB-002: 打开账单详情')` |
| TRB-003 | `test('TRB-003: 无账单时显示空状态')` |

## CLI 探索和执行记录

- headed Playwright CLI 实际入口为 `/tenant-h5/rent/list`；列表快照和截图为 `tenant-rent-bills-list-snapshot.md`、`tenant-rent-bills-list-step1.png`。点击账单卡进入 `/tenant-h5/rent/detail/945`（探索数据 ID），详情快照和截图为 `tenant-rent-bills-detail-snapshot.md`、`tenant-rent-bills-detail-step1.png`。
- 真实请求 `GET /tenant-app/rent/bills` 与 `GET /tenant-app/rent/bills/{id}` 均 HTTP 200。列表返回的账单对象中 `apartmentName` 和 `roomNo` 为 `null`，所以列表卡片显示为“应缴 2026-10-01 ·”且房间信息缺失；详情接口可返回测试公寓名和房间号，详情页也正确展示。
- 用例映射：TRB-001 → `test('TRB-001: 账单列表显示完整账单信息')`；TRB-002 → `test('TRB-002: 打开账单详情')`；TRB-003 → `test('TRB-003: 无账单时显示空状态')`。
- 新增 `pages/tenant-rent-bills.page.ts` 和 `tests/test_tenant_rent_bills.spec.ts`。账单 setup 使用租客入住生成当月账单，测试只读取账单，不发起支付；无账单测试不创建入住。
- 初次回归发现 TRB-001 失败：`RentBillServiceImpl.listTenantBills` 直接查询账单实体，列表接口的 `apartmentName`、`roomNo` 为 `null`，导致页面房间描述缺失；TRB-002 详情和支付入口、TRB-003 空状态均通过。
- 经用户同意修复：`RentBillMapper` 新增 `selectTenantBills` 查询，复用账单详情中的列别名与账单/租客/房间/公寓关联关系，并支持可选状态筛选；`RentBillServiceImpl.listTenantBills` 改为调用该查询。
- 使用 Docker 构建本地后端成功（Maven `BUILD SUCCESS`），并重建 `raina-backend:local-user-permission-fix`、重启本地容器。修复后租客账单 UI 回归 **3 passed（3.1s）**；三条用例均生成截图、视频和 Trace。HTML 报告已在 Codex 中打开：`http://127.0.0.1:9339`。
- 测试限制：入住会自动生成账单；当前管理接口没有删除/作废账单的入口。fixture 会退房并软删除临时租客/住房，但生成的账单业务记录仍留在本地数据库中，关联已软删除的测试租客。未触发支付或更改账单状态。
