# 用例文件读取与理解

## 核心原则

**不预设固定格式，不调用解析脚本。** 读取文件原始内容作为上下文，由大模型自行理解测试意图。

用户可以用任意方式编写用例：口语描述、Markdown 表格、Excel 自定义列、XMind 思维导图、截图配文字等。

## 读取方式

| 文件类型 | 读取方式 |
|----------|----------|
| `.txt` / `.md` / `.csv` | Read 工具直接读取全文 |
| `.xlsx` / `.xls` | shell 提取可读文本后放入上下文 |
| `.xmind` | `unzip -p file.xmind content.json` 读取 JSON 文本 |
| 图片 | Read 工具（若支持）或请用户补充文字描述 |
| 其他 | 尝试 Read；失败则请用户提供文本版 |

### Excel 内容提取示例

```bash
python3 -c "
import zipfile, xml.etree.ElementTree as ET, sys
# 简易 xlsx 文本提取；复杂文件可请用户导出 csv
print(open(sys.argv[1],'rb').read()[:0])  # fallback: 请用户描述
" file.xlsx
```

若系统有 `xlsx2csv` 或 `in2csv` 等工具，优先使用将表格转为 CSV 文本。

### XMind 内容提取

```bash
unzip -p case.xmind content.json
```

将 JSON 全文作为上下文，从中识别节点 title 即为用例步骤。

## LLM 理解任务

读取内容后，在内部整理以下信息（无需输出固定 JSON）：

1. **用例标题** — 测试场景名称
2. **起始 URL** — 从文件中识别；找不到则向用户确认
3. **操作步骤** — 按顺序理解：打开、输入、点击、选择、等待、验证
4. **测试数据** — 账号、密码、搜索词等输入值
5. **预期结果** — 需要断言的内容和状态
6. **不确定项** — 标记并向用户确认，不猜测

## 理解示例

### 输入（自由文本）

```
测试一下 playwright 官网
1. 打开 https://playwright.dev
2. 点 Docs
3. 应该能看到 Getting started
```

### 内部理解（Agent 自行整理）

- 标题：Playwright 官网文档浏览
- URL：https://playwright.dev
- 步骤：navigate → click "Docs" → assert "Getting started" visible

### 输入（Excel 截图式描述）

用户 Excel 可能是：

| 测试点 | 操作说明 | 数据 |
|--------|----------|------|
| 登录 | 输入账号密码后点登录 | admin/123456 |

Agent 从表格语义理解，不依赖固定列名。

## 不确定时

- URL 缺失 → 询问用户
- 步骤模糊（「点那个按钮」）→ 探索阶段结合 snapshot 推断，推断结果写入报告
- 多个可能解读 → 列出选项请用户选择
- 文件无法读取 → 请用户粘贴文本或换格式

## 与探索阶段的衔接

理解完成后，按整理出的步骤顺序用 `playwright-cli` 探索。探索中发现与用例描述不符时，以实际页面为准，并在报告中注明差异。
