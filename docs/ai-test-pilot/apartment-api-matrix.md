# 公寓模块接口事实与覆盖差距矩阵（AI 试点草稿）

- 状态：待人工审查；这是 AI 盘点结果，不是已批准的接口契约。
- 范围：管理端 `/apartment` 模块；本轮只盘点，不生成或修改测试代码。
- 盘点日期：2026-10-25。

## 证据与判断规则

| 来源 | 用途 | 限制 |
|---|---|---|
| `smartApartment-main/docs/swagger-apartment.json` | 路径、方法、参数、请求模型、文档契约 | 可能与实际实现或产品预期不一致 |
| `smartApartment-main/backend/src/main/java/com/wk/webframe/controller/ApartmentController.java` | 当前实现观察：过滤、归属校验、删除和字段处理 | 代码行为不自动等于正确业务预期 |
| `smartApartment-main/backend/src/main/java/com/wk/webframe/config/SecurityConfig.java` | 认证边界 | 全局要求已认证；控制器另按创建人限制资源，不表示只有某个角色可调用 |
| `apartment-tests/apis/apartment_api.py`、`tests/test_apartment.py`、根 `conftest.py` | 当前测试封装、明确断言、fixture 生命周期 | fixture 执行过某操作，不等于存在完整的独立行为断言 |

## 接口事实表

| 方法与路径 | 文档事实 | 当前实现观察 | 当前框架覆盖 | 可信度/待确认 |
|---|---|---|---|---|
| `GET /apartment/list` | 可选 `name`、`address`、`contactName`、`contactPhone` 模糊筛选；查询本人列表；电话脱敏 | 以当前用户 `create_by` 与 `deleted=0` 限定；四个筛选字段均使用模糊匹配；按更新时间倒序；列表电话脱敏 | 有 list；显式测试全列表含本次创建记录、名称筛选及每条结果名称匹配。名称筛选没有准备不匹配对照数据；其他筛选、电话脱敏、跨账号隔离未显式覆盖 | 路径/参数高；业务预期以产品确认优先 |
| `GET /apartment/page` | `current` 默认 1、`size` 默认 10；支持与 list 相同筛选；查询本人；电话脱敏 | 使用 MyBatis Plus 分页；同样限制本人和未删除数据，按更新时间倒序；分页记录的电话脱敏 | 当前 `ApartmentApi` 没有 page 方法，测试文件无分页用例 | 文档与代码一致；响应结构/边界值需从实际契约或样例确认 |
| `GET /apartment/{id}` | 按 ID 查详情，仅本人可访问 | 不存在/已删除返回业务失败“公寓不存在”；其他创建人返回 forbidden；成功返回实体 | 有 detail；成功断言 ID、名称。fixture teardown 另验证删除后业务码 400、提示“公寓不存在”、data 为 null | 成功路径已覆盖；跨账号和未存在 ID 独立场景未覆盖 |
| `POST /apartment` | JSON `ApartmentRequest`；名称必填；`createBy` 服务端填充；成功数据为 ID | 控制器用 `Assert.isTrue` 检查非空名称；调用保存前无条件将 description 设为空；createBy 由 MyBatis Plus 自动填充 | API wrapper 有 create；`created_apartment` fixture 创建名称并断言 ID 为正整数，供测试使用 | **文档/实现疑点：**Swagger 示例允许 `description`，但控制器清空它。是否为预期需人工确认。空白名称的 HTTP/业务码也需确认，不能从代码擅自推定 |
| `PUT /apartment/{id}` | JSON `ApartmentRequest`；仅本人可更新；不得修改归属 | 校验资源存在及创建人；把路径 ID 写入对象，并覆盖请求体中的 createBy 为数据库原值 | API wrapper 当前无 update 方法；无显式更新用例 | 文档与控制器归属逻辑一致；部分更新还是全量更新、空值语义需确认 |
| `DELETE /apartment/{id}` | 本人公寓逻辑删除；返回 Boolean 结果 | 校验资源存在及创建人后 `removeById`；后续 detail 视为不存在 | API wrapper 有 delete。fixture teardown 断言 HTTP/业务码 200，并确认 detail 返回不存在；无独立删除用例，也未断言 data=true/重复删除行为 | 常规清理链路已验证；重复删除预期未定义/未覆盖 |

## 覆盖差距与建议优先级

| 优先级 | 场景候选 | 当前证据与差距 | 需要确认/设计的测试数据 |
|---|---|---|---|
| P1 | 分页查询基础行为 | page 路径与参数存在，但 wrapper 和测试都缺失 | 新建多条专用公寓；验证分页结构、当前页记录、总数及默认参数。先确认响应字段名和项目期望的边界行为 |
| P1 | 更新成功与持久化 | update 路径有文档和实现，但无 API 封装及测试 | 更新本次创建的数据，再用 detail 验证字段；确定更新请求是否要传完整模型 |
| P1 | 更新不能转移归属 | 控制器会忽略请求体 createBy 并保留数据库归属；尚无回归测试 | 在现有管理员身份下提交伪造 createBy，再验证所有者仍可查且归属未变。若要验证跨账号隔离，还需第二个有效账号及其建立方式 |
| P1 | 其他用户公寓的访问隔离 | list/page 以用户 ID 过滤；detail/update/delete 检查创建人；当前测试只走管理员自己的资源 | 需要第二个账号创建资源，再由当前账号尝试查询/修改/删除。具体 HTTP 状态码与业务码须先以接口契约或已确认行为为准 |
| P1 | 描述字段是否应被保存 | Swagger 允许 description，但当前 create 实现强制置空 | 先由产品/维护者确认契约；确认之前不生成断言，也不把实现行为当作正确预期 |
| P2 | 四种列表筛选及组合筛选 | 目前只测 name；且没有负向对照记录 | 创建字段可控的目标记录和非匹配记录；逐项覆盖地址、联系人、电话，并检查组合条件是否 AND 关系 |
| P2 | 电话脱敏 | Swagger 与控制器都声明/实施列表脱敏；当前用例未断言 | 通过创建数据写入可识别手机号，再检查 list/page 中展示值；确认 detail 是否也应脱敏（当前控制器未显式脱敏） |
| P2 | 创建参数校验 | 只通过 fixture 创建合法公寓；空/空白名称没有独立测试 | 确认空字符串、纯空格、缺少 name 的契约及错误码；断言稳定业务含义，不猜 HTTP 映射 |
| P2 | 删除独立行为 | fixture 已检查删除后的不可见性，但删除断言与清理绑定，且没有验证响应 data | 可考虑单独的删除行为测试；先确认成功 data 与重复删除的预期，并确保清理不会二次依赖该对象 |

## 当前明确覆盖的范围

- 显式测试：`test_apartment_list`、`test_apartment_detail`、`test_apartment_list_filter_by_name`。
- fixture 生命周期：创建合法公寓、检查返回 ID；测试结束删除该 ID，并通过 detail 确认业务上不可见。
- 不应把以上内容描述成分页、更新、跨账号权限、全部筛选字段或创建参数校验已经覆盖。

## 人工审查清单

1. `description`：创建接口应保存传入描述，还是当前实现清空描述才是预期？请以产品/接口维护者确认结果为准。
2. 管理端身份：公寓接口是否允许任意已认证管理端用户调用，再由数据归属做隔离？现有 SecurityConfig 是任意非公开接口要求认证；Controller 按创建人隔离，没有看到该类上的角色注解。
3. 更新语义：PUT 是全量替换还是允许部分字段更新？空值、缺字段如何处理？
4. 失败契约：无权访问、缺少名称、重复删除分别应检查哪些 HTTP 状态码、业务码和提示？
5. 下一步优先项：建议确认后先补分页，或先补 update wrapper + 更新成功测试；不建议一次生成全部候选用例。

## AI 生成边界

本表只归纳可查证事实并提出待确认问题。后续生成测试草稿时，必须遵循项目现有 `admin_apartment_api`、`ApiClient`、`assert_response` 与 fixture 模式；不得自动编辑后端，不得把当前已知实现疑点写成预期正确结果，也不得在未经审查时把草稿纳入 Jenkins 回归。
