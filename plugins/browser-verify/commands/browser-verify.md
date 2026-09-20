---
description: Validate product flows in a browser end-to-end using Playwright
allowed-tools: Bash, Playwright
---

# Browser Verification Command

Validate the target flow in a browser. Run full end-to-end checks against live or staging URLs, capture screenshots, assert on DOM state, detect console errors, and return a structured leadership summary.

## Check:

1. **Page load** — URL resolves, HTTP 200, no redirect loops
2. **Core UI elements** — Hero, CTA buttons, nav, footer all render
3. **Product flow** — Target action (add-to-cart / checkout / signup / download) completes without error
4. **Console errors** — Zero `console.error` or `unhandledrejection` events during flow
5. **Network requests** — Key API calls return 2xx; no 4xx/5xx on critical paths
6. **Mobile viewport** — Flow works at 390×844 (iPhone 14)
7. **Performance** — LCP under 2.5s, no layout shift score above 0.1
8. **Screenshot proof** — Final state captured and saved to `/tmp/verify-screenshot.png`

## Return:

1. **top blockers** — Any failures that prevent conversion (P0)
2. **required next actions** — Ordered fix list with file/line references where possible
3. **owners** — Which system/module owns each blocker (Frontend / API / DNS / CDN / Auth)
4. **deadlines** — Suggested fix-by window based on severity (P0 = same day / P1 = 48h / P2 = 1 week)
5. **fallback plan** — What to serve/redirect to if the blocker cannot be fixed before deadline
6. **leadership summary** — 3-sentence plain-English exec brief: current state, risk, and recommended action

## Usage

```
/browser-verify <url> [--flow <flow-name>] [--env <staging|prod>] [--mobile]
```

### Examples

```bash
# Verify checkout flow on production
/browser-verify https://yourstore.com --flow checkout --env prod

# Verify signup on staging, mobile viewport
/browser-verify https://staging.yourstore.com --flow signup --mobile

# Quick smoke test — just load and screenshot
/browser-verify https://yourstore.com
```

## Playwright Script (auto-executed)

```js
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: process.env.MOBILE ? { width: 390, height: 844 } : { width: 1280, height: 800 },
    userAgent: process.env.MOBILE
      ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  });

  const page = await context.newPage();
  const errors = [];
  const failedRequests = [];

  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('requestfailed', req => failedRequests.push({ url: req.url(), failure: req.failure()?.errorText }));

  const url = process.env.TARGET_URL || 'https://example.com';
  const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

  const status = response?.status();
  const lcp = await page.evaluate(() =>
    new Promise(res => new PerformanceObserver(list => {
      const entries = list.getEntries();
      res(entries[entries.length - 1]?.startTime ?? null);
    }).observe({ type: 'largest-contentful-paint', buffered: true }))
  );

  await page.screenshot({ path: '/tmp/verify-screenshot.png', fullPage: false });

  const result = {
    url,
    status,
    consoleErrors: errors,
    failedRequests,
    lcpMs: lcp,
    screenshot: '/tmp/verify-screenshot.png',
    passed: status === 200 && errors.length === 0 && failedRequests.length === 0 && (!lcp || lcp < 2500)
  };

  console.log(JSON.stringify(result, null, 2));
  await browser.close();
})();
```

## Output Format

```json
{
  "topBlockers": ["string"],
  "requiredNextActions": ["string"],
  "owners": { "blocker": "module" },
  "deadlines": { "blocker": "P0|P1|P2 + date" },
  "fallbackPlan": "string",
  "leadershipSummary": "string"
}
```
