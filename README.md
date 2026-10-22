# 公寓接口自动化测试

Python + Pytest + Requests + Allure。当前覆盖管理员认证、公寓及房间，共 14 个测试场景。

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

当前 P0 为 4 条，P1 为 10 条。标记用于选择测试，不保证执行顺序。

## 配置与限制

config.py 提供基础地址、默认超时和管理员演示账号；可通过 APARTMENT_BASE_URL、APARTMENT_ADMIN_USERNAME、APARTMENT_ADMIN_PASSWORD 覆盖。默认环境是本地服务，不使用真实环境账号。

当前仅按串行执行设计。错误密码用例的 login_state fixture 在前后正确登录，恢复失败计数；已锁定账号无法通过正确登录直接解锁，需要先等锁定到期或单独恢复本地账号状态。同账号重新登录会使旧令牌失效，不并行运行，也避免与该账号的手动操作同时进行。

公寓和房间数据按测试创建并清理，房间先于所属公寓清理；清理断言失败会报告 ERROR。验证码 2998 是项目内置演示绕过值，不代表真实图片验证码流程已覆盖。

## 目录职责

- config.py：环境配置。
- core/api_client.py：相对路径检查、地址拼接、超时、基础日志和请求发送。
- apis/：认证、公寓和房间接口方法，返回原始 Response。
- conftest.py：客户端、登录准备、测试数据与清理。
- data/ 与 data_loader.py：登录 YAML 数据及校验。
- test_*.py：场景与业务断言。
- read_yaml_demo.py：学习演示脚本，不是自动化用例。

## 报告

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

## 已知覆盖范围

不等同于完整公寓业务验收。租客/维修工角色、入住、报修抢单、账单、并发、UI 与性能尚未实现。名称筛选未主动准备不匹配对照数据，本轮按学习安排暂缓。具体进度见上级目录 WIKI.md 与代码审查与补齐清单.md。
