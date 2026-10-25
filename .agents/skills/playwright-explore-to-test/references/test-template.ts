import { test, expect } from '@playwright/test';
// import { {PageName} } from './pages/{PageName}';

/**
 * 模板：describe + beforeEach + 多条独立 test()
 * 每个 test() 对应用例矩阵中的一行，用例内用 test.step 做 AAA。
 * 黄金参考：tests/apartment-list.spec.ts
 * 详见 references/test-case-design.md、references/design-checklist.md
 */

const AUTH_STATE = 'tests/explore/{case-name}-auth.json';

test.describe('{模块名}', () => {
  test.use({
    storageState: AUTH_STATE,
    baseURL: 'http://localhost:3000',
  });

  let pageObject: {PageName};

  test.beforeEach(async ({ page }) => {
    pageObject = new {PageName}(page);
    await pageObject.goto();
  });

  test('{ID-001}: {用例名称}', async ({ page }) => {
    await test.step('验证', async () => {
      await expect(page.getByTestId('main-table')).toBeVisible();
    });
  });

  test('{ID-002}: {用例名称}', async () => {
    const uniqueName = `PW搜索测试-${Date.now()}`;

    await test.step('准备', async () => {
      await pageObject.createItem({ name: uniqueName, ... });
    });

    await test.step('操作', async () => {
      await pageObject.searchByName(uniqueName);
    });

    await test.step('验证', async () => {
      await expect(pageObject.getRowByName(uniqueName).first()).toBeVisible();
    });
  });

  test('{ID-003}: {用例名称}', async () => {
    const uniqueName = `PW编辑测试-${Date.now()}`;

    await test.step('准备', async () => {
      await pageObject.createItem({ name: uniqueName, ... });
    });

    await test.step('操作', async () => {
      await pageObject.editItem(uniqueName, { field: '新值' });
    });

    await test.step('验证', async () => {
      await expect(pageObject.getRowByName(uniqueName)).toContainText('新值');
    });
  });
});

/**
 * Page Object 模板（步骤 ≥ 5 或跨页面时使用）
 */
/*
// tests/pages/{PageName}.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class {PageName} {
  readonly page: Page;
  readonly table: Locator;

  constructor(page: Page) {
    this.page = page;
    this.table = page.getByTestId('main-table');
  }

  async goto() {
    await this.page.goto('/path');
    await expect(this.table).toBeVisible();
  }
}
*/
