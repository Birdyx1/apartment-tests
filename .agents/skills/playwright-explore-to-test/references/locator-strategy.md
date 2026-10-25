# 元素定位策略

## 优先级顺序（强制）

探索与生成代码时，**必须**按以下顺序选择 locator：

| 优先级 | 策略 | Playwright API | 适用场景 |
|--------|------|----------------|----------|
| 1 | `data-testid` | `page.getByTestId('login-btn')` | 元素有 test id 属性 |
| 2 | role + 可访问名称 | `page.getByRole('button', { name: '登录' })` | 按钮、链接、输入框等有语义 role |
| 3 | `id` | `page.locator('#username')` | id 唯一且稳定 |
| 4 | CSS 类 + 标签 | `page.locator('button.submit-btn')` | 无 testId/role/id 时的结构化选择 |
| 5 | XPath | `page.locator('xpath=//button[text()="登录"]')` | 前 4 级均不可用 |

## 降级规则

1. 在 `playwright-cli snapshot` 输出中依次检查：`data-testid` → role/name → id → tag+class → XPath
2. 属性不可见时用 `playwright-cli eval "el => el.getAttribute('data-testid')" eN` 或 `playwright-cli generate-locator eN --raw`
3. 生成代码时必须映射到对应 Playwright API，不得跳过高优先级；优先采用 CLI 自动输出的代码再校验
4. 使用 XPath 时必须在代码注释中说明原因
5. 元素缺少 testId 时，在探索报告中标注 `建议添加 data-testid="..."`

## 各优先级示例

### 1. data-testid

```typescript
await page.getByTestId('username-input').fill('admin');
await page.getByTestId('submit-btn').click();
await expect(page.getByTestId('welcome-message')).toBeVisible();
```

### 2. role + 可访问名称

```typescript
await page.getByRole('textbox', { name: '用户名' }).fill('admin');
await page.getByRole('button', { name: '登录' }).click();
await expect(page.getByRole('heading', { name: '欢迎' })).toBeVisible();
```

常用 role：`button`, `link`, `textbox`, `checkbox`, `radio`, `combobox`, `heading`, `tab`, `menuitem`

### 3. id

```typescript
await page.locator('#username').fill('admin');
await page.locator('#login-form').locator('#submit').click();
```

仅当 id 在页面中唯一时使用，避免 `#content`、`#main` 等通用 id。

### 4. CSS 类 + 标签

```typescript
await page.locator('input.form-control[name="username"]').fill('admin');
await page.locator('button.btn-primary[type="submit"]').click();
```

避免：
- 纯 hash 类名：`.css-1a2b3c`
- 深层嵌套：`div > div > div > span.text`
- 动态生成的 class

### 5. XPath（最后手段）

```typescript
// XPath: 表格第 2 行操作按钮，无 testId/role/id 可用
await page.locator('xpath=//table[@data-testid="user-list"]//tr[2]//button[text()="编辑"]').click();
```

## 断言模板

```typescript
// 可见性
await expect(locator).toBeVisible();
await expect(locator).toBeHidden();

// 文本
await expect(locator).toHaveText('欢迎');
await expect(locator).toContainText('成功');

// 属性
await expect(locator).toHaveAttribute('href', '/dashboard');
await expect(locator).toBeEnabled();
await expect(locator).toBeDisabled();

// 输入值
await expect(locator).toHaveValue('admin');

// URL
await expect(page).toHaveURL(/dashboard/);
await expect(page).toHaveTitle('首页');
```

## 探索报告 locator 记录格式

```markdown
### Step 3: 点击登录按钮

- **选用**: 优先级 1 — `getByTestId('login-btn')`
- **备选**: 优先级 2 — `getByRole('button', { name: '登录' })`
- **建议**: 密码框缺少 testId，建议添加 `data-testid="password-input"`
```
