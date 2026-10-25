# 公寓接口自动化测试

Python + Pytest + Requests + Allure。当前收集 110 条测试，覆盖三角色认证、核心租住/维修/账单链路、系统管理、权限和跨账号场景。2026-10-25 最新全量为 **105 passed、5 failed（53.94s）**；失败是保留的 D03、D04 以及用户接口响应包含 `password` 字段的缺陷回归，没有修改后端或跳过测试。测试状态和覆盖评估见上级目录 `WIKI.md` 与 `docs/ai-test-pilot/project-wide-api-test-assessment.md`。

公共代码分工见 [重复代码简化说明](docs/重复代码简化说明.md)。

## 环境准备

先启动同级 smartApartment-main 的 Docker 服务，再在本目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

已存在虚拟环境时只需激活，不必重复创建。

## 运行

```bash
python -m pytest -v
python -m pytest -v -m p0
python -m pytest -v -m p1
python -m pytest --collect-only -q
```

当前 P0 为 37 条，P1 为 40 条，另有租客详情 1 条尚未标记。标记用于选择测试，不保证执行顺序；完整执行请使用不带 -m 的命令。

## 配置与限制

`config.py` 集中管理 API 地址、管理员演示账号和 MinIO 连接参数。API 地址与管理员账号可通过 `APARTMENT_BASE_URL`、`APARTMENT_ADMIN_USERNAME`、`APARTMENT_ADMIN_PASSWORD` 覆盖；MinIO 使用以下环境变量，未设置时采用本地练习默认值：

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| `APARTMENT_MINIO_ENDPOINT` | `localhost:9000` | MinIO 服务地址 |
| `APARTMENT_MINIO_PUBLIC_ORIGIN` | 空 | 覆盖后端返回图片 URL 的协议和主机；保留对象路径，供容器内测试访问 |
| `APARTMENT_MINIO_ACCESS_KEY` | `minioadmin` | MinIO 访问账号 |
| `APARTMENT_MINIO_SECRET_KEY` | `minioadmin` | MinIO 访问密钥 |
| `APARTMENT_MINIO_BUCKET` | `apartment` | 测试图片所在桶 |
| `APARTMENT_MINIO_SECURE` | `false` | 是否通过 HTTPS 连接 |

`APARTMENT_MINIO_SECURE` 会去除首尾空格并忽略大小写；只有字符串 `true` 会转换为布尔值 `True`，其他值转换为 `False`。

连接其他测试环境时，可在启动命令前设置变量。请将示例地址和占位凭据替换为该环境提供的值：

```bash
APARTMENT_BASE_URL="http://test-api.example:8080" \
APARTMENT_MINIO_ENDPOINT="test-minio.example:9000" \
APARTMENT_MINIO_PUBLIC_ORIGIN="http://test-minio.example:9000" \
APARTMENT_MINIO_ACCESS_KEY="your-access-key" \
APARTMENT_MINIO_SECRET_KEY="your-secret-key" \
APARTMENT_MINIO_BUCKET="apartment-test" \
APARTMENT_MINIO_SECURE="true" \
python -m pytest -v
```

此写法只对当前测试进程生效。不要把真实环境凭据写进 README 或提交到代码仓库。默认环境是本地服务，不使用真实环境账号。

当前仅按串行执行设计。错误密码用例的 login_state fixture 在前后正确登录，恢复失败计数；已锁定账号无法通过正确登录直接解锁，需要先等锁定到期或单独恢复本地账号状态。同账号重新登录会使旧令牌失效，不并行运行，也避免与该账号的手动操作同时进行。并发抢单用例仅在单条测试内使用两个独立维修工会话发送请求，10 个参数轮次按顺序执行；不表示整个测试套件支持并行。

公寓、房间和租客数据按测试创建并清理，房间先于所属公寓清理；入住 fixture 先退房并检查状态，再结束相关资源 fixture。报修 fixture 先检查工单状态：待处理/处理中则取消至状态 3，已完成 2 或已取消 3 则保留终态；复查终态后退房和清理基础资料。取消和完工保留工单与操作日志，退房保留入住和账单历史。图片成功用例由 uploaded_repair_image 在结束后删除本次上传对象；已完成测试工单的图片关联历史保留，对应测试图片已删除。MinIO 客户端使用 `config.py` 中的环境配置，依赖 minio SDK。清理断言失败会报告 ERROR。验证码 2998 是项目内置演示绕过值，不代表真实图片验证码流程已覆盖。

维修工使用独立 Session；管理员按启用角色编码 MAINTENANCE_WORKER 查询 ID，创建具有唯一用户名、邮箱和模拟手机号的临时系统用户，测试结束后通过用户删除接口清理。邮箱/手机号缺失触发唯一约束的后端缺陷仍待修复，当前正常场景使用完整测试数据。删除权限编码已统一为 system:user:remove，已验证管理员可删除、维修工无权删除。

## 目录职责

- config.py：环境配置。
- core/api_client.py：相对路径检查、地址拼接、超时、基础日志和请求发送。
- core/assertions.py：HTTP/业务码及 data=true 响应校验。
- helpers/：账号生命周期、账单业务步骤、工单业务断言；不合并身份会话或吞掉失败。
- apis/：管理员认证、公寓、房间、租客资料、租客认证/房间/报修、入住、维修工认证/工单/文件上传和系统角色/用户接口，返回原始 Response。
- conftest.py：客户端、登录准备、测试数据与清理。
- data/ 与 data_loader.py：登录 YAML 数据、校验及 PNG 测试图片。
- tests/test_*.py：场景与业务断言。
- read_yaml_demo.py：学习演示脚本，不是自动化用例。

## 报告

2026-10-25 接入 UI 自动化时，曾用目录中已有的 78 条接口结果与新增的 8 条 Playwright UI 结果验证 Allure 合并流程，报告共 86 条（83 passed、3 failed）；这只是历史结果快照，不代表当前接口用例总数或最新全量回归。当前 Pytest 可收集 110 条接口用例；生成最新统一报告前，应由 Jenkins/本地先清理结果目录并运行全量接口测试，再追加 UI 结果。8 条 UI 用例当时全部通过，且每条都附有截图、视频和 Trace。

先生成本轮原始数据：

```bash
python -m pytest -v --alluredir=allure-results --clean-alluredir
```

项目内 Allure 命令行工具需要 Node.js 和 Java，单独安装，不属于 requirements.txt：

```bash
npm install --prefix .tools allure-commandline@2
./.tools/node_modules/.bin/allure serve allure-results
```

查看期间保持进程运行，结束时按 Control+C。也可生成固定目录后查看：

```bash
./.tools/node_modules/.bin/allure generate allure-results --clean -o allure-report
./.tools/node_modules/.bin/allure open allure-report
```

清理选项仅针对指定报告目录。报告是生成产物，默认不提交 Git。

Playwright UI 测试的运行方式与 Jenkins Credentials 配置见 [ui-tests/README.md](ui-tests/README.md) 和 [Jenkins 持续集成说明](ci/jenkins/README.md)。Jenkinsfile 先由 Pytest 清理统一 `allure-results/`，再由 Playwright 追加 UI 结果，最终在 Jenkins 的同一份 Allure 报告中发布接口和 UI 测试。

## AI / MCP 辅助接口测试

项目 Skill 会在当前会话发现可用 MCP。Playwright MCP 可用于本地页面和 API 网络请求发现；目前已观测到登录页加载验证码接口返回 HTTP 200，但该运行观测不代表已确认业务预期。MCP 使用范围、敏感信息边界和测试闭环见 [MCP 辅助接口测试工作流](docs/ai-test-pilot/mcp-test-workflow.md)。

## 已知覆盖范围

不等同于完整公寓业务验收。租客登录到本人资料、入住及退房状态恢复、重复入住拒绝、本人房间查询已有测试；报修覆盖创建后的详情/列表、取消后的详情/列表、未入住拒绝、空字符串/纯空格标题、缺少紧急程度及重复取消；维修工账号创建、登录及清理已有一条 P0 用例。管理员公寓列表已有 8 条 UI 测试；其它业务页面 UI、维修工派单/抢单/接单/完工、账单支付、跨租客越权、并发与性能仍未完成。名称筛选未主动准备不匹配对照数据，本轮按学习安排暂缓。具体进度见上级目录 WIKI.md 与代码审查与补齐清单.md。

## 阅读代码

暂停新增功能时，可以先按 [代码结构与调用说明](docs/代码结构与调用说明.md) 阅读目录、调用链、fixture 依赖、身份区别和数据清理顺序。各 Python 文件已添加中文职责说明和关键步骤注释。

## 场景任务书

[任务书 01：租客报修接口自动化](docs/任务书01-租客报修自动化.md) 包含接口文档、独立设计目标、清理要求与验收标准；任务书中的场景不代表已完成。

[报修测试设计](docs/报修测试设计.md) 记录已实现的六类场景、fixture 职责与清理顺序、连续复跑和全量回归证据，以及尚未覆盖的范围。

[维修工账号准备缺陷记录](docs/缺陷记录-维修工账号准备.md) 记录创建账号的字段约束问题、删除权限修复，以及重新部署后的回归证据。

账单范围与限制见 [账单测试设计](docs/账单测试设计.md)。新发现的跨角色会话缺陷见 [D04 记录](docs/缺陷记录-跨角色登录状态冲突.md)；本轮对异常后置遗留测试工单的定向收尾已记录，后端尚未修复。

D04 专项节点：`tests/test_auth_identity_isolation.py`，两种登录顺序均已稳定复现并按正确预期失败，账号清理正常；已纳入本轮 78 条全量。
