'use strict';
const { chromium } = require(
  'C:/Users/daars/AppData/Roaming/npm/node_modules/@playwright/test/node_modules/playwright-core'
);
const path = require('path');
const os = require('os');
const fs = require('fs');

const CHROMIUM_EXE = 'C:\\Users\\daars\\AppData\\Local\\ms-playwright\\chromium-1223\\chrome-win64\\chrome.exe';
const TIMESTAMP = Date.now();
const SCREENSHOT_PATH = path.join(os.tmpdir(), `pw-screenshot-${TIMESTAMP}.png`);

(async () => {
  const browser = await chromium.launch({
    executablePath: CHROMIUM_EXE,
    headless: true,
  });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
  });
  const page = await context.newPage();

  try {
    // === TASK-SPECIFIC CODE HERE ===

  } finally {
    await browser.close();
  }
})();
