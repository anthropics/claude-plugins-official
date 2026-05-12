---
name: playwright
description:
  "Use this skill when the user wants to automate a browser, scrape or extract data from a web
  page, take a screenshot of a URL, fill out a web form, click elements on a page, log in to a
  website, handle cookies or auth flows, or run any multi-step web workflow. Trigger on: 'open
  this URL', 'take a screenshot of', 'fill the form at', 'click on', 'extract text from',
  'scrape', 'automate the browser', 'navigate to and', 'log in to', 'check what the page says',
  or any sequence of steps on a web page. Prefer this skill over curl/fetch for anything
  requiring a real browser with JavaScript rendering."
version: 0.1.0
---

# Playwright Browser Automation

## Environment Facts

These constants are fixed — never re-discover them via shell commands.

- **playwright-core path** (use forward slashes in `require()` — Node accepts them on Windows): `C:/Users/daars/AppData/Roaming/npm/node_modules/@playwright/test/node_modules/playwright-core`
- **Chromium executable**: `C:\Users\daars\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe`
- **Only Chromium is installed** — never attempt `firefox` or `webkit` launches; they will fail with ENOENT
- **Temp dir**: `C:\Users\daars\AppData\Local\Temp\` (PowerShell: `$env:TEMP`)
- **Script template**: read from `scripts/automation-template.cjs` in this skill directory before generating any task script

---

## Execution Pattern

For every automation request, follow these steps in order:

1. **Read the template** — use the Read tool to load `scripts/automation-template.cjs` from this skill's directory. Use it as the base for your task script.

2. **Write a task script** — customize the template by replacing `// === TASK-SPECIFIC CODE HERE ===` with the automation logic. Write it to:
   ```
   C:\Users\daars\AppData\Local\Temp\pw-task-<Date.now()>.cjs
   ```
   Use the Write tool. Never overwrite an earlier script — always include a fresh `Date.now()` timestamp.

3. **Execute** — run via Bash:
   ```
   node "C:\Users\daars\AppData\Local\Temp\pw-task-<timestamp>.cjs"
   ```
   Set timeout to **60000 ms** (navigation-heavy tasks can take 15–30 s).

4. **Capture output** — stdout from the script is your result. Screenshots are saved inside the script to `SCREENSHOT_PATH`.

5. **Display screenshots** — if a screenshot was saved, use the Read tool on the path the script printed to show it inline.

---

## Task Playbooks

### Navigate & Extract Text
```javascript
await page.goto('https://example.com', { waitUntil: 'domcontentloaded' });
const text = await page.evaluate(() => document.body.innerText);
console.log(text);
```
If `innerText` is empty (JS-rendered content), wait first:
```javascript
await page.waitForFunction(() => document.body.innerText.length > 100);
```

### Take a Screenshot
```javascript
await page.goto('https://example.com', { waitUntil: 'networkidle' });
await page.screenshot({ path: SCREENSHOT_PATH, fullPage: true });
console.log('screenshot:', SCREENSHOT_PATH);
```
After the script runs, use the Read tool on the printed path to display the image.

### Fill a Form & Submit
```javascript
await page.goto('https://example.com/form');
await page.fill('#username', 'myuser');
await page.fill('#password', 'mypass');
await page.click('button[type="submit"]');
await page.waitForURL('**');
console.log('landed at:', page.url());
console.log(await page.title());
```

### Auth / Cookie Handling
Pre-seed cookies:
```javascript
await context.addCookies([
  { name: 'session', value: 'abc123', domain: 'example.com', path: '/' }
]);
```
Capture session state after login for reuse:
```javascript
const state = await context.storageState();
fs.writeFileSync(
  path.join(os.tmpdir(), 'pw-state.json'),
  JSON.stringify(state, null, 2)
);
console.log('state saved to:', path.join(os.tmpdir(), 'pw-state.json'));
```
Restore in a later script:
```javascript
const context = await browser.newContext({
  storageState: path.join(os.tmpdir(), 'pw-state.json'),
});
```

---

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `spawn chrome.exe ENOENT` | Wrong `executablePath` | Confirm it matches the hardcoded CHROMIUM_EXE constant |
| `MODULE_NOT_FOUND playwright-core` | Wrong require path | Use forward-slash form: `C:/Users/daars/.../playwright-core` |
| `TimeoutError: waiting for selector` | Element absent or late | Switch to `waitUntil: 'networkidle'`; add `page.waitForSelector(sel, {timeout: 15000})` |
| `Target page/context/browser closed` | Uncaught exception before `finally` | Check task code for thrown errors; the `finally` block handles `browser.close()` |
| Empty `innerText` | JS not yet rendered | Add `page.waitForFunction(() => document.body.innerText.length > 100)` |

---

## Permissions Checklist

These entries must be in `settings.local.json` for the workflow to run without prompts:

```json
"Write(C:\\Users\\daars\\AppData\\Local\\Temp\\pw-task-*.cjs)",
"Bash(node *pw-task*.cjs)",
"Write(C:\\Users\\daars\\AppData\\Local\\Temp\\pw-screenshot-*.png)"
```

If running outside the `lumos-browser` project, add these to the relevant project's `settings.local.json` or to global `settings.json`.
