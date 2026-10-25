#!/bin/bash
# 初始化 Playwright Test 项目（TypeScript + Chromium）
set -euo pipefail

TARGET_DIR="${1:-.}"
cd "$TARGET_DIR"

if [ -f "playwright.config.ts" ] || [ -f "playwright.config.js" ]; then
  echo "Playwright 已初始化，跳过。"
  exit 0
fi

echo "正在初始化 Playwright 项目..."
npm init -y > /dev/null 2>&1
npm init playwright@latest -- --quiet --lang=ts --browser=chromium --install-deps
npm install -D @playwright/cli@latest
npx playwright-cli install 2>/dev/null || true

mkdir -p tests/pages tests/explore

# 默认无头 + 启用视频与 trace 录制（无头下照常生成）
if ! grep -q "headless:" playwright.config.ts 2>/dev/null; then
  sed -i '' '/use: {/a\
    headless: true,
' playwright.config.ts
fi
if ! grep -q "video:" playwright.config.ts 2>/dev/null; then
  sed -i '' '/use: {/a\
    video: '\''on'\'',
' playwright.config.ts
fi
if ! grep -q "trace:" playwright.config.ts 2>/dev/null; then
  sed -i '' '/use: {/a\
    trace: '\''on'\'',
' playwright.config.ts
fi

# 添加 show-report npm script
if ! grep -q '"show-report"' package.json 2>/dev/null; then
  npm pkg set scripts.show-report="playwright show-report"
fi

echo "Playwright 项目初始化完成。"
echo "  配置文件: playwright.config.ts"
echo "  测试目录: tests/"
echo "  Page Object: tests/pages/"
echo "  探索输出: tests/explore/"
