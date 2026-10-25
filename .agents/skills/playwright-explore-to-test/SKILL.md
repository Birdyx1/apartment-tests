---
name: playwright-explore-to-test
description: >-
  根据 URL 或任意格式用例文件探索 Web 界面并生成 Playwright Test 代码。
  用例文件无需固定格式，读取内容后由大模型理解。Use when the user provides
  a URL or test case file and asks to explore a page, write playwright tests,
  探索页面, 生成自动化测试, or mentions playwright-explore-to-test.
---

# Playwright 探索生成测试

`<skill-root>` 指本 skill 目录（`playwright-explore-to-test/`）。

## 触发条件

- 用户提供 URL，要求探索页面并编写 Playwright 测试
- 用户提供用例文件（任意格式：txt / md / xlsx / xmind / csv / 图片等）
- 用户说「探索界面」「写 playwright test」「根据用例生成自动化」

## 输入确认

开始前确认（上下文已有则跳过询问）：

1. **目标**：URL 或用例文件路径
2. **测试场景**：如登录、下单、搜索
3. **登录态**：是否需要账号密码或已有 cookie
4. **输出位置**：默认 `tests/{case-name}.spec.ts`，相关产出统一放在 `tests/` 下（见输出路径表）

## 四阶段工作流

```
- [ ] Step 1: 读取并理解输入（URL 或用例文件内容 → LLM 提取步骤）
- [ ] Step 2: playwright-cli 探索界面
- [ ] Step 3: 生成 Playwright Test 代码
- [ ] Step 4: 运行验证并修正
```

---

## 前置：安装 playwright-cli

探索前确认 CLI 可用：

```bash
npx @playwright/cli --version
```

未安装时：

```bash
npm install -D @playwright/cli@latest
npx playwright-cli install
```

**禁止使用** `cursor-ide-browser` 或 `user-playwright` MCP 做探索，统一用 Shell 执行 `playwright-cli` 命令。

**运行模式**：**探索有头、测试无头**。Step 2 探索用 `playwright-cli open {url} --headed` 弹出浏览器便于观察与人工介入；Step 4 测试用 `npx playwright test`（不加 `--headed`）。`trace` / `video` 由 `playwright.config.ts` 控制，与 headless 无关，无头测试下照常录制。

---

## Step 1: 读取并理解

### URL 模式

直接提取 URL，按功能场景拆解为测试用例矩阵（默认多条，不合并）。

### 用例文件模式（LLM 直接理解，无固定格式）

**不调用解析脚本，不要求固定 schema。**

1. 用 Read 工具读取文件内容（二进制格式先提取为文本，见 [references/case-reading.md](references/case-reading.md)）
2. 将全文作为上下文，自行理解并输出**测试用例矩阵**（见 [references/test-case-design.md](references/test-case-design.md)）：
   - 用例 ID、名称
   - 起始 URL（缺失则询问用户）
   - 前置条件
   - 操作步骤（打开 / 输入 / 点击 / 选择 / 验证）
   - 测试数据与预期结果
3. 不确定的内容标记并向用户确认，不猜测
4. 多场景页面**默认拆为多条独立用例**，不合并
5. **门禁**：用例矩阵必须先写入 `tests/explore/{case-name}-report.md`，未输出不得进入 Step 2
6. 理解完成后简要复述用例矩阵，再进入探索

---

## Step 2: 界面探索

**必须使用 `playwright-cli`**（Shell 命令，不用 MCP）。

### 探索模式（二选一）

#### 模式 A：直接打开（简单场景）

```bash
playwright-cli open {url} --headed
playwright-cli snapshot --filename=tests/explore/{case-name}-snapshot.md
```

#### 模式 B：通过 seed 测试 attach（推荐）

复用 Playwright Test 的 fixture / 登录态，探索与最终测试共用同一上下文：

```bash
# 1. 若无 seed，先创建 tests/seed.spec.ts（至少 page.goto 到起始 URL）
# 2. 后台启动 debug 会话
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/seed.spec.ts --debug=cli
# 3. 等待输出 tw-XXXX 后 attach
playwright-cli attach tw-XXXX
playwright-cli resume
playwright-cli snapshot --filename=tests/explore/{case-name}-snapshot.md
```

**重要**：有自定义 setup（登录、fixture）时优先用模式 B，不要跳过 seed 直接 `open` URL。

### 探索 Checklist

1. `playwright-cli snapshot` → 保存到 `tests/explore/{case-name}-snapshot.md`
2. 按理解的步骤逐步操作（每步 CLI 会自动输出对应 Playwright TS 代码，收集备用）：
   - `playwright-cli fill eN "value"` / `playwright-cli click eN`
   - `playwright-cli select eN "option"` / `playwright-cli check eN`
   - 每步操作后重新 `playwright-cli snapshot`
3. 关键步骤截图 → `playwright-cli screenshot --filename=tests/explore/{case-name}-step{N}.png`
4. 动态元素用 `playwright-cli run-code` 或 `playwright-cli eval` 探测（iframe、shadow DOM）
5. 需要稳定登录态时：`playwright-cli state-save tests/explore/{case-name}-auth.json`
6. 探索结束：`playwright-cli close`（模式 B 还需停止后台 debug 进程）

### 元素定位优先级（强制）

探索时每步必须按此顺序选取 locator，高优先级不可用时才降级：

| 优先级 | 策略 | Playwright API |
|--------|------|----------------|
| 1 | `data-testid` | `page.getByTestId('...')` |
| 2 | role + 可访问名称 | `page.getByRole('button', { name: '...' })` |
| 3 | `id` | `page.locator('#...')` |
| 4 | CSS 类 + 标签 | `page.locator('button.submit-btn')` |
| 5 | XPath | `page.locator('xpath=...')` — 最后手段 |

辅助命令：

```bash
playwright-cli eval "el => el.getAttribute('data-testid')" eN
playwright-cli generate-locator eN --raw
```

详细规则见 [references/locator-strategy.md](references/locator-strategy.md)。

### 探索报告

写入 `tests/explore/{case-name}-report.md`，包含：

- **测试用例矩阵**（ID / 名称 / 前置 / 步骤 / 预期）
- **用例 → 代码映射表**（`AL-001` → `test('AL-001: ...')`）
- 从用例文件理解出的步骤摘要
- 每步 CLI 输出的 Playwright 代码及 locator 优先级层级
- 备选 locator 方案
- URL 变化记录
- 断言点与预期状态
- 缺少 testId 的元素及建议值
- 用例描述与实际页面的差异
- 阻塞/异常说明
- 若有 auth 文件，记录路径及用法

---

## Step 3: 生成测试代码

基于探索报告、CLI 输出的代码片段、[references/test-template.ts](references/test-template.ts)、[references/test-case-design.md](references/test-case-design.md) 和 [references/design-checklist.md](references/design-checklist.md) 生成代码。

**生成前必须执行** [design-checklist.md](references/design-checklist.md) 自检，全部通过后再写码。

**黄金参考**：[`tests/apartment-list.spec.ts`](../../../tests/apartment-list.spec.ts)（7 条独立 test、AAA step、自包含数据、Page Object）。

### 生成规范

- **每个验证点一个 `test()`**，用例矩阵 1:1 映射，禁止多个场景合并为一条用例
- 用 `test.describe` 按模块分组，`test.beforeEach` 处理公共导航/初始化
- 用例内用 `test.step('准备'/'操作'/'验证')` 实现 AAA 结构
- `test.step` 是子步骤，`test()` 才是 Playwright 统计单位
- 优先采用 CLI 探索时输出的 Playwright 代码，再按定位优先级校验/升级
- 严格遵循定位优先级，不得跳级使用 XPath
- 注释标注 locator 优先级层级
- 敏感数据用 `process.env.TEST_USERNAME` 等环境变量
- 有 `state-save` 文件时，在 `playwright.config.ts` 或测试里用 `storageState` 复用登录态
- **`playwright.config.ts` 必须启用录制**：`use.video: 'on'` + `use.trace: 'on'`，确保每条用例在 HTML 报告中可回放视频与逐步 trace
- **数据依赖分级**（强制）：
  - 写/改/删/刷新验证 → 必须 `Date.now()` 自建数据
  - 搜索验证 → 优先「先创建目标数据再搜索」
  - 纯 UI 验证（列头、按钮）→ 无需预置数据
  - 禁止依赖分页敏感或可能被删的外部种子数据
- 步骤 ≥ 5 或跨页面时提取 Page Object 到 `tests/pages/`

### 输出路径

| 产出 | 路径 |
|------|------|
| 测试文件 | `tests/{case-name}.spec.ts` |
| Page Object | `tests/pages/{PageName}.ts` |
| 探索报告 | `tests/explore/{case-name}-report.md` |
| 截图 | `tests/explore/{case-name}-step{N}.png` |
| 登录态 | `tests/explore/{case-name}-auth.json` |

---

## Step 4: 验证

### 项目无 Playwright 时

```bash
bash <skill-root>/scripts/init-playwright.sh
```

### 1. 运行测试

```bash
npx playwright test tests/{case-name}.spec.ts
```

默认无头运行。`playwright.config.ts` 中 `use.video` 和 `use.trace` 必须为 `'on'`（无头下照常录制）。报告里每条用例附带录制视频；点击 **Trace** 可逐步查看每次 click/fill/network 操作。若项目已有配置但缺少此项，生成代码时一并补上。

### 2. 打开报告（强制执行）

测试跑完后**必须**打开 HTML 报告：

```bash
npm run show-report
```

- 在 Shell 中**后台运行**（`block_until_ms: 0`），避免阻塞 agent
- 告知用户报告地址（默认 `http://localhost:9323`）
- 若 `package.json` 无 `show-report` script，先补：

```json
"scripts": {
  "show-report": "playwright show-report"
}
```

### 3. 合规验证

- 确认测试通过数 = 用例矩阵行数（如 7 passed）
- 每条用例报告中有 video 与 trace 附件
- 缺少录制配置则回补 `playwright.config.ts`

### 4. 结果判定与修复询问

**全部通过**：简要输出通过数 + 报告已打开，直接提示完成（不询问修复）。

**有问题**（满足任一条件）：

- 存在 failed / flaky
- 通过数 ≠ 用例矩阵行数
- 报告缺少 video 或 trace
- heal 2 轮后仍失败

使用 `AskQuestion` 询问用户：

> 测试报告已打开，发现 N 条失败 / 合规问题。是否需要我自动修复？

选项：

- **是，自动修复** → 进入 heal 流程（见下），最多 2 轮；修完重新跑测 + 重新 `npm run show-report`
- **否，稍后手动处理** → 输出失败摘要（用例名、错误信息、报告链接），结束 skill

### 5. heal 流程（用户确认修复后，最多 2 轮）

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/{case-name}.spec.ts:<line> --debug=cli
playwright-cli attach tw-XXXX
playwright-cli snapshot
playwright-cli console
playwright-cli requests
# 修正 locator 后更新 .spec.ts，再跑测试 + npm run show-report
```

通过后提示完成。

---

## playwright-cli 命令清单

| 命令 | 用途 |
|------|------|
| `playwright-cli open {url} --headed` | 有头打开浏览器并导航（探索专用） |
| `playwright-cli goto {url}` | 当前会话内导航 |
| `playwright-cli snapshot` | 获取 accessibility tree + element refs |
| `playwright-cli click eN` | 点击元素 |
| `playwright-cli fill eN "value"` | 填写表单（自动输出 TS 代码） |
| `playwright-cli select eN "opt"` | 下拉选择 |
| `playwright-cli press Enter` | 键盘操作 |
| `playwright-cli screenshot --filename=...` | 截图存档 |
| `playwright-cli run-code "async page => ..."` | 执行 Playwright 代码片段 |
| `playwright-cli eval "expr" eN` | 读取元素属性/状态 |
| `playwright-cli generate-locator eN --raw` | 生成 locator 表达式 |
| `playwright-cli state-save auth.json` | 保存 cookie/localStorage |
| `playwright-cli state-load auth.json` | 加载登录态 |
| `playwright-cli attach tw-XXXX` | 附着到 `--debug=cli` 测试会话 |
| `playwright-cli resume` | 继续执行暂停中的测试 |
| `playwright-cli close` | 关闭浏览器 |

---

## 图形验证码处理（禁止 OCR）

遇到图形验证码时，**禁止**安装或使用 tesseract、ddddocr、tesseract.js 等 OCR 库。改用大模型视觉识别：

```
1. playwright-cli screenshot eN --filename=tests/explore/{case-name}-captcha.png
   （eN 为验证码图片元素 ref，截不清时可截整个验证码区域）
2. 用 Read 工具读取 PNG，识别 4 位字母/数字
3. playwright-cli fill 用户名/密码/验证码 → click 登录
4. 验证 URL 跳转；失败则 click 刷新验证码，重新截图识别，最多重试 2 次
5. 仍失败 → 提示用户在有头浏览器中手动登录（`playwright-cli open {url} --headed`），确认后 state-save
6. 登录成功 → playwright-cli state-save tests/explore/{case-name}-auth.json
```

探索报告须记录：识别值、是否成功、重试次数。测试代码用 `storageState` 复用登录态，**不把验证码识别写进 spec**。

## 阻塞处理

遇到以下情况停止自动化，报告用户：

- **短信验证码** → 建议用户手动登录后 `state-save`，测试用 `storageState` 跳过
- **图形验证码** → 按上文「图形验证码处理」流程；2 次识别失败后提示用户手动登录
- 需要人工确认的弹窗
- 缺少测试账号或 cookie
- 页面需要 VPN / 内网访问

报告格式：说明阻塞原因、当前页面截图、建议的下一步（提供账号 / 手动完成 + state-save / 跳过该步骤）。

---

## 参考资源

- 用例读取与理解：[references/case-reading.md](references/case-reading.md)
- **测试用例设计**：[references/test-case-design.md](references/test-case-design.md)
- **生成前自检**：[references/design-checklist.md](references/design-checklist.md)
- 定位器策略：[references/locator-strategy.md](references/locator-strategy.md)
- 代码模板：[references/test-template.ts](references/test-template.ts)
- 示例用例：[examples/](examples/)（含 [case-apartment-list.md](examples/case-apartment-list.md)）
