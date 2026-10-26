# 租客 H5“公告详情”页：测试矩阵与探索报告

## 页面范围与数据原则

- 页面 URL：`http://localhost:3001/tenant-h5/notices/{noticeId}`，正常入口来自首页公告卡片。
- 预期依据：`tenant-h5/src/pages/Notice/index.tsx`、`tenant-h5/src/pages/Home/index.tsx`、`tenant-h5/src/api/notice.ts` 和后端 `TenantAppNoticeController`。
- 使用管理员 API 创建本用例专属的全局已发布公告；测试结束删除公告。有效访问使用专属在住租客；无入住场景使用独立租客账号，不修改其他业务数据。

## 测试用例矩阵

| 用例 ID | 场景 | 前置条件 | 操作步骤 | 预期结果 |
|---|---|---|---|---|
| TND-001 | 从首页打开已发布公告详情 | 专属租客有入住记录；管理员创建并发布唯一公告 | 登录首页，点击唯一公告卡片 | 路由进入公告详情；标题、更新时间、正文与 `GET /tenant-app/notices/{id}` 一致；返回导航可用 |
| TND-002 | 无入住租客不能查看公告详情 | 独立租客无入住记录；已有专属已发布公告 | 登录后直接访问公告详情 URL | 详情接口返回“当前没有在住记录”；页面提示错误并回到租客首页 |
| TND-003 | 从公告详情返回首页 | 专属租客有入住记录；已从首页进入公告详情 | 点击详情页左上角返回控件 | 路由返回租客首页，首页内容可见 |

## 用例与代码映射

| ID | 测试名称 |
|---|---|
| TND-001 | `test('TND-001: 首页公告卡片可打开完整公告详情')` |
| TND-002 | `test('TND-002: 无入住记录时公告详情返回首页')` |
| TND-003 | `test('TND-003: 公告详情返回按钮回到首页')` |

## Playwright CLI 探索记录

- 用 headed Playwright CLI 登录本轮临时在住租客，从首页点击管理员刚创建并发布的全局公告，进入 `/tenant-h5/notices/40`。页面快照/截图保存在 `tenant-notice-detail-snapshot.md`、`tenant-notice-detail-step1.png`；点击左上角返回控件后的快照在 `tenant-notice-detail-return-snapshot.md`。
- 首页公告列表 `GET /tenant-app/notices?limit=3` 和详情 `GET /tenant-app/notices/40` 均 HTTP 200。详情页展示公告标题、更新时间和正文，接口与页面一致；页面底部仍显示“首页/工单/我的”导航。
- 无入住租客访问详情时，后端返回 HTTP 200、业务码 400 和“当前没有在住记录”；前端 Toast 提示后回到首页。该路径在自动化 TND-002 中验证通过。
- 公告标题通过精确文本定位，详情标题用 `getByRole('heading', { name })`，正文和时间使用 `.notice-content` / `.notice-time`。返回控件没有可访问名称；快照确认是导航栏返回按钮后，自动化通过 `.adm-nav-bar-back` 定位。从首页进入详情后点击可回到 `/tenant-h5/home`。页面没有 `data-testid`。
- 自动化映射：TND-001 → `test('TND-001: 首页公告卡片可打开完整公告详情')`；TND-002 → `test('TND-002: 无入住记录时公告详情返回首页')`；TND-003 → `test('TND-003: 公告详情返回按钮回到首页')`，均见 `tests/test_tenant_notice_detail.spec.ts`；临时全局公告由 `tests/tenant-notice-data.fixture.ts` 创建、发布并删除。
- 租客、公寓、房间和入住由既有 fixture 创建并在 teardown 中退房、核验空置后清理；专属公告也在 teardown 删除。三条用例均生成截图、视频和 Trace；四模块联合定向回归中公告详情 **3 条全部通过**，HTML 报告已更新并重新打开。
