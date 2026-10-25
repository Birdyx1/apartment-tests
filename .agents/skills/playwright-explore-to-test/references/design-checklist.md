# 生成前设计自检清单

生成 Playwright 测试代码前，AI **必须逐项确认**。全部通过后方可进入 Step 3 写码。

## 用例矩阵

- [ ] 已输出用例矩阵（ID / 名称 / 前置 / 步骤 / 预期）
- [ ] 矩阵已写入 `tests/explore/{case-name}-report.md` 顶部
- [ ] 矩阵每行对应 **1 个 `test()`**，无多场景合并
- [ ] 探索报告含 **用例 → 代码映射表**

## 独立性与数据

- [ ] 每条用例可单独运行，不依赖上一条用例结果
- [ ] 写/改/删/刷新验证类用例使用 `Date.now()` 自建数据
- [ ] 搜索类用例优先「先创建目标数据再搜索」，不依赖外部种子数据
- [ ] 纯 UI 验证（列头、按钮可见）无需预置数据
- [ ] 禁止依赖分页敏感或可能被删的共享数据

## 代码结构

- [ ] 使用 `test.describe` + `test.beforeEach` 分组与公共导航
- [ ] 用例内 AAA：`test.step('准备'/'操作'/'验证')`
- [ ] `test()` 是统计单位，`test.step()` 仅作子步骤
- [ ] 命名格式：`{ID}: {动作} + {预期}`
- [ ] 步骤 ≥ 5 或跨页面时已提取 Page Object

## 配置与录制

- [ ] 探索使用 `playwright-cli open {url} --headed`（有头）
- [ ] `playwright.config.ts` 含 `headless: true`（或省略，Playwright 默认无头）
- [ ] `playwright.config.ts` 含 `video: 'on'`
- [ ] `playwright.config.ts` 含 `trace: 'on'`
- [ ] 运行测试不加 `--headed`（无头下 trace/video 照常生成）

## Step 4 收尾

- [ ] 测试跑完后后台执行 `npm run show-report` 打开 HTML 报告
- [ ] 通过数 = 用例矩阵行数
- [ ] 全部通过 → 告知通过数与报告地址，直接完成
- [ ] 有问题 → 用 `AskQuestion` 询问用户是否自动修复；用户确认后进入 heal（最多 2 轮）

## 目录结构

所有测试相关产出统一放在 `tests/` 下：

```
tests/
├── {case-name}.spec.ts
├── pages/{PageName}.ts
└── explore/{case-name}-report.md
```

## 参考

- 黄金参考实现：项目内 `tests/apartment-list.spec.ts`
- 设计规范：[test-case-design.md](test-case-design.md)
