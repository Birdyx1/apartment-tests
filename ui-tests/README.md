# 公寓管理 UI 自动化

本目录使用 Playwright Test + TypeScript 编写管理端 UI 回归。用例通过 Playwright CLI 探索后，按用例矩阵映射为自动化测试。

## 本机运行前准备

1. 启动本地公寓系统，默认管理端地址为 `http://localhost:3000`。
2. 用 Playwright CLI 打开登录页，使用本机演示账号完成一次登录，然后保存 storage state：

   ```bash
   npx playwright-cli open http://localhost:3000/login --headed --browser=chrome
   npx playwright-cli state-save tests/explore/apartment-list-auth.json
   ```

   本项目的本地演示验证码值为用户提供的 `2998`；登录凭据和验证码不写入测试代码。
3. 确认登录态文件被 Git 忽略。该文件含本机认证信息，只供本机测试使用。

## 运行

```bash
PW_STORAGE_STATE=tests/explore/apartment-list-auth.json PLAYWRIGHT_CHANNEL=chrome npm test
```

单独运行未登录访问拦截测试时，不需要登录态：

```bash
PW_SKIP_AUTH_SETUP=1 npm run test:auth-gate
```

打开最近一次 HTML 报告：

```bash
npm run show-report
```

测试配置会为每条用例记录截图、视频和 Trace；Allure Playwright reporter 将它们附加到共享的 `../allure-results`，同时保留独立 HTML 报告。测试操作本地共享后端，当前配置为单 worker；写操作使用唯一临时公寓，并在用例结束时清理。

## Jenkins

流水线先清理一次 `allure-results` 并运行 Pytest，再运行 Playwright；两个框架按顺序向同一目录追加结果，由现有 Allure Jenkins 插件统一发布。

Jenkins 需要 Node.js 24、Playwright Chromium 及其 Linux 系统依赖。将以下凭据加入 Jenkins Credentials：

- `apartment-admin-login`：Username with password，填本地测试系统管理员账号。
- `apartment-demo-captcha`：Secret text，填本地演示验证码绕过值。

Jenkinsfile 通过 Credentials Binding 注入这些值，不在仓库保存明文。管理端地址通过 `BASE_URL` 设为 Jenkins 可访问的本地前端地址。

## 当前覆盖

- AUTH-001：未登录访问公寓列表时跳转登录页。
- AL-001 至 AL-007：列表加载、名称搜索、重置、新增、刷新、编辑地址和删除。

用例矩阵、探索观察、数据清理约定和最新执行结果见 `tests/explore/apartment-list-report.md`。
