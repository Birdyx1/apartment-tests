# Jenkins 上运行接口与 UI 回归

Jenkinsfile 顺序运行 Pytest 和 Playwright，并让两个 reporter 写入仓库根目录的 `allure-results/`。该目录只在 Pytest 开始时清理一次；Playwright 结果会追加进去，最后由现有 Allure Jenkins 插件统一发布。

## 一次性准备

1. 在 Jenkins Credentials 中创建：
   - `apartment-admin-login`：Username with password，使用本地测试环境管理员账号。
   - `apartment-demo-captcha`：Secret text，值为本地演示验证码绕过值。
2. 现有 `apartment-jenkins` 容器使用 Debian 13。首次运行前，在仓库检出并安装 Node/Playwright 包后，从宿主机以 root 执行一次浏览器系统依赖安装：

   ```bash
   docker exec -u root apartment-jenkins /var/jenkins_home/workspace/apartment-api-tests/ci/jenkins/install-playwright-linux-deps.sh
   ```

   重建 Jenkins 容器时需要重新执行。Node.js 和 Chromium 浏览器本身由 Jenkinsfile 安装到持久化的 Jenkins Home 缓存。
3. Jenkins Job 使用仓库根目录的 `Jenkinsfile`。管理端与后端地址分别通过 `host.docker.internal:3000` 和 `host.docker.internal:8080` 从容器访问。

## 每次构建

- 接口测试先用 `--clean-alluredir` 建立干净的统一结果目录。
- UI 测试通过 Jenkins Credentials 注入用户名、密码和验证码；`global-setup.ts` 通过真实登录页生成被忽略的 `ui-tests/tests/.auth/jenkins-admin.json`。
- 管理端静态包把 API 地址写为 `http://localhost:8080`。Jenkinsfile 会把浏览器中的 `localhost` 解析到 Docker Desktop 宿主机地址，让页面 API 请求可达本机后端。
- UI 测试通过 `API_BASE_URL` 将 Node 侧准备/清理数据的请求指向同一后端，避免访问 Jenkins 容器自身的 `localhost:8080`。
- API 与 UI 共用测试数据库，Jenkinsfile 禁止同一任务并发构建，避免多个回归任务相互污染数据和登录状态。
- UI 每条用例会附带截图、视频和 Playwright Trace；Jenkins 同时归档 Allure 结果、UI HTML 报告和原始 `test-results`。
- 接口或 UI 测试失败时，流水线继续执行剩余阶段并发布报告，最终构建状态仍为 FAILURE。

当前 Jenkins 容器还没有 NodeJS 插件，因此 Jenkinsfile 将 Node.js 24.16.0 下载到 `$JENKINS_HOME/.cache`，无需配置 Jenkins 全局 Node 工具。
