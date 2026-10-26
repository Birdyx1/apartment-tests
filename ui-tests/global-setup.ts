import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import { getAuthStatePath } from './auth-state';

export default async function globalSetup() {
  if (process.env.PW_SKIP_AUTH_SETUP === '1') {
    return;
  }

  const authFile = getAuthStatePath();
  try {
    await fs.access(authFile);
    return;
  } catch {
    // Missing local state is generated through the real UI login below.
  }

  const username = process.env.PW_ADMIN_USERNAME;
  const password = process.env.PW_ADMIN_PASSWORD;
  const captcha = process.env.PW_DEMO_CAPTCHA;
  if (!username || !password || !captcha) {
    throw new Error(
      '缺少管理员登录态。请提供 PW_ADMIN_USERNAME、PW_ADMIN_PASSWORD、PW_DEMO_CAPTCHA，' +
        '或设置已有的 PW_STORAGE_STATE 文件路径。',
    );
  }

  const baseURL = process.env.BASE_URL ?? 'http://localhost:3000';
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.PLAYWRIGHT_CHANNEL
      ? { channel: process.env.PLAYWRIGHT_CHANNEL as 'chrome' }
      : {}),
  });
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(new URL('/login', baseURL).toString());
    await page.getByRole('textbox', { name: '用户名' }).fill(username);
    await page.getByRole('textbox', { name: '密码' }).fill(password);
    await page.getByRole('textbox', { name: '验证码' }).fill(captcha);
    await page.getByRole('button', { name: /登录/ }).click();
    // 管理端实际登录后的首页是 dashboard；公寓列表是登录后的业务页。
    await page.waitForURL((url) => url.pathname === '/dashboard', { timeout: 15_000 });

    await fs.mkdir(path.dirname(authFile), { recursive: true });
    await context.storageState({ path: authFile });
    await context.close();
  } finally {
    await browser.close();
  }
}
