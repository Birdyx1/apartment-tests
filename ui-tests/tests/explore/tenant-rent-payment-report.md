# 租客 H5“房租账单支付”页：测试矩阵与探索报告

## 测试范围与数据原则

- 起始页面：`http://localhost:3001/tenant-h5/rent/detail/{billId}`；通过账单详情页底部“支付宝支付”或“微信支付”进入模拟支付确认框。
- 预期依据：`tenant-h5/src/pages/Rent/Detail/index.tsx`、`tenant-h5/src/api/rent.ts`、后端 `TenantAppRentController` 与 `RentBillServiceImpl`。
- 每条用例使用单独创建的临时租客和入住账单。该项目使用本地 MOCK 支付，不调用真实支付渠道；确认成功会将账单永久标记为已缴，不能清理时保留测试业务记录。

## 测试用例矩阵

| 用例 ID | 场景 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| TRP-001 | 取消模拟支付 | 专属租客有待缴账单 | 打开详情，选择支付宝支付，在模拟支付确认框中取消 | 停留在账单详情；账单仍为待缴，支付按钮仍可见；不调用模拟确认接口 |
| TRP-002 | 确认模拟支付成功 | 专属租客有独立待缴账单 | 打开详情，选择微信支付并确认 | 显示支付成功并返回列表；账单状态变为已缴且有已缴时间；重新打开详情后不再显示支付按钮 |

## 用例与代码映射

| ID | 测试名称 |
|---|---|
| TRP-001 | `test('TRP-001: 取消模拟支付后账单保持待缴')` |
| TRP-002 | `test('TRP-002: 确认模拟支付后账单变为已缴')` |

## Playwright CLI 探索记录

- 使用 `tests/seed_tenant_rent_payment.spec.ts` 临时 seed，复用 `tenantHome` fixture 创建租客、入住和专属账单；headed CLI 登录后进入 `/tenant-h5/rent/detail/951`。临时 seed 在探索结束后删除，fixture 已执行退房并清理租客/住房。
- 详情页初始状态显示 2026-10 账单 ¥1800，因应缴日期为 2026-10-01、当前日期为 2026-10-26，状态展示“逾期”；逾期账单仍可用支付宝或微信发起 MOCK 支付。
- locator 按可访问角色定位：支付按钮 `getByRole('button', { name: '微信支付' })`，弹窗 `getByRole('dialog')`，取消和确定分别为 `getByRole('button', { name: '取消' })`、`getByRole('button', { name: '确定' })`。关键快照/截图为 `tenant-rent-payment-detail-snapshot.md` / `tenant-rent-payment-detail-step1.png`、`tenant-rent-payment-confirm-snapshot.md` / `tenant-rent-payment-confirm-step2.png`、`tenant-rent-payment-paid-list-snapshot.md` / `tenant-rent-payment-paid-list-step3.png`、`tenant-rent-payment-paid-detail-snapshot.md`。
- 页面链路：账单详情 → 点击支付按钮 → `POST /tenant-app/rent/bills/{id}/pay` 成功返回 `mode=MOCK` → 显示“模拟支付”确认框。取消后留在详情页，不调用 `/tenant-app/rent/payments/{id}/mock-confirm`；确认后调用该接口，显示“支付成功”并跳转账单列表；重新打开详情后状态为“已缴”、显示“已缴时间”，支付按钮消失。
- 本轮没有 `data-testid`，role + accessible name 足以稳定定位，暂不需要增加 testId。探索期间使用专属临时账单完成了一次 MOCK 支付，以观察成功状态；该账单为测试业务数据。
- 自动化代码映射：TRP-001 → `test('TRP-001: 取消模拟支付后账单仍未缴')`；TRP-002 → `test('TRP-002: 确认模拟支付后账单变为已缴')`，位于 `tests/test_tenant_rent_payment.spec.ts`。setup 分别创建独立租客和账单；支付成功后账单与支付记录会作为本地历史数据保留，管理接口没有账单/支付单删除能力。取消确认也会留下待处理支付单，业务接口没有单独取消支付单入口。
- 定向回归 **2 passed（3.0s）**。每条用例均生成 `test-finished-1.png`、`video.webm` 和 `trace.zip`。Playwright HTML 报告已在 Codex 中打开：`http://127.0.0.1:9340`。
