/**
 * VS Code Extension — COE Pricing Intelligence
 * Registers all 11 commands, collects VIN input, shows results in webview panel.
 */

const vscode = require('vscode');
const path   = require('path');
const { dispatch, healthCheck } = require('../plugins/coe-pricing/index');

// ── State ─────────────────────────────────────────────────────────────────────
let outputChannel;
let statusBarItem;
let scanHistory = [];

// ── Activation ────────────────────────────────────────────────────────────────
function activate(context) {
  outputChannel = vscode.window.createOutputChannel('COE Pricing Intelligence');
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.text = '$(car) COE Pricing';
  statusBarItem.tooltip = 'COE Pricing Intelligence — Click for Master Scan';
  statusBarItem.command = 'coe.masterScan';
  statusBarItem.show();

  log('COE Pricing Intelligence activated.');

  // Register all commands
  const cmds = [
    vscode.commands.registerCommand('coe.masterScan',        () => runCommand('master-scan',        collectMasterParams)),
    vscode.commands.registerCommand('coe.vinScan',           () => runCommand('vin-scan',           collectVinOnly)),
    vscode.commands.registerCommand('coe.moiAccident',       () => runCommand('moi-accident',       collectVinOnly)),
    vscode.commands.registerCommand('coe.priceEngine',       () => runCommand('price-engine',       collectFullParams)),
    vscode.commands.registerCommand('coe.auctionIntel',      () => runCommand('auction-intel',      collectFullParams)),
    vscode.commands.registerCommand('coe.gccVerify',         () => runCommand('gcc-verify',         collectFullParams)),
    vscode.commands.registerCommand('coe.execSummary',       () => runCommand('exec-summary',       collectVinOnly)),
    vscode.commands.registerCommand('coe.reliabilityScore',  () => runCommand('reliability-score',  collectFullParams)),
    vscode.commands.registerCommand('coe.copilotHandoff',    () => runCommand('copilot-handoff',    collectVinOnly)),
    vscode.commands.registerCommand('coe.healthCheck',       () => runHealthCheck()),
    vscode.commands.registerCommand('coe.openWidget',        () => openPricingWidget()),
  ];

  cmds.forEach(cmd => context.subscriptions.push(cmd));
  context.subscriptions.push(outputChannel, statusBarItem);
}

// ── Command Runner ────────────────────────────────────────────────────────────
async function runCommand(commandName, paramCollector) {
  const params = await paramCollector(commandName);
  if (!params) return; // User cancelled

  statusBarItem.text = `$(sync~spin) COE: Running /${commandName}...`;

  try {
    const result = await dispatch(commandName, params);
    statusBarItem.text = '$(car) COE Pricing';

    // Store in history
    scanHistory.unshift({
      command: commandName,
      vin: params.vin,
      vehicle: result.vehicle,
      timestamp: result.timestamp,
      result,
    });

    // Show results in webview panel
    showResultPanel(commandName, result, params);

    // Copy prompt to clipboard if it exists
    const prompt = result.result?.prompt || result.result?.masterPrompt;
    if (prompt) {
      await vscode.env.clipboard.writeText(prompt);
      vscode.window.showInformationMessage(
        `✓ /${commandName} complete. Prompt copied to clipboard — paste into Claude.`,
        'Open Output'
      ).then(action => { if (action === 'Open Output') outputChannel.show(); });
    }

    log(`[${commandName}] Completed in ${result.elapsed_ms}ms`);

  } catch (err) {
    statusBarItem.text = '$(error) COE Pricing';
    vscode.window.showErrorMessage(`COE Error: ${err.message}`);
    log(`[ERROR] ${commandName}: ${err.message}`);
    setTimeout(() => { statusBarItem.text = '$(car) COE Pricing'; }, 3000);
  }
}

// ── Input Collectors ──────────────────────────────────────────────────────────
async function collectVinOnly() {
  const vin = await vscode.window.showInputBox({
    prompt: 'Enter VIN (17 characters)',
    placeHolder: 'e.g. JTMAU7BJ5R4049000',
    validateInput: v => (!v || v.trim().length !== 17) ? 'VIN must be exactly 17 characters' : null,
  });
  if (!vin) return null;
  return { vin: vin.trim().toUpperCase() };
}

async function collectFullParams() {
  const vin = await vscode.window.showInputBox({
    prompt: 'VIN (17 characters)',
    placeHolder: 'e.g. JTMAU7BJ5R4049000',
    validateInput: v => (!v || v.trim().length !== 17) ? 'Must be 17 characters' : null,
  });
  if (!vin) return null;

  const make = await vscode.window.showInputBox({ prompt: 'Make', placeHolder: 'e.g. Toyota' });
  if (!make) return null;

  const model = await vscode.window.showInputBox({ prompt: 'Model', placeHolder: 'e.g. Land Cruiser' });
  if (!model) return null;

  const yearStr = await vscode.window.showInputBox({
    prompt: 'Year',
    placeHolder: '2024',
    validateInput: v => isNaN(parseInt(v)) ? 'Enter a valid year' : null,
  });
  if (!yearStr) return null;

  const mileageStr = await vscode.window.showInputBox({
    prompt: 'Mileage (km) — press Enter to skip',
    placeHolder: '25000',
  });

  return {
    vin: vin.trim().toUpperCase(),
    make: make.trim(),
    model: model.trim(),
    year: parseInt(yearStr),
    mileage: mileageStr ? parseInt(mileageStr) : undefined,
  };
}

async function collectMasterParams() {
  const base = await collectFullParams();
  if (!base) return null;

  const colour = await vscode.window.showInputBox({
    prompt: 'Colour — press Enter to skip',
    placeHolder: 'e.g. White, Black, Silver',
  });

  const plateNumber = await vscode.window.showInputBox({
    prompt: 'UAE Plate Number — press Enter to skip (used for MOI query)',
    placeHolder: 'e.g. Dubai A 12345',
  });

  return { ...base, colour: colour || undefined, plateNumber: plateNumber || undefined };
}

// ── Results Webview Panel ─────────────────────────────────────────────────────
function showResultPanel(commandName, result, params) {
  const panel = vscode.window.createWebviewPanel(
    'coePricingResult',
    `COE: ${commandName} — ${result.vehicle || params.vin}`,
    vscode.ViewColumn.Beside,
    { enableScripts: true }
  );

  const prompt = result.result?.prompt || result.result?.masterPrompt || '';
  const handoffBlock = result.result?.handoffBlock || '';
  const subPromptsCount = result.result?.subPrompts
    ? Object.keys(result.result.subPrompts).length : 0;

  panel.webview.html = buildResultHTML({
    commandName,
    vehicle: result.vehicle || params.vin,
    vin: result.vin,
    timestamp: result.timestamp,
    elapsed: result.elapsed_ms,
    prompt,
    handoffBlock,
    subPromptsCount,
    instructions: result.result?.instructions || [],
  });
}

function buildResultHTML({ commandName, vehicle, vin, timestamp, elapsed, prompt, handoffBlock, subPromptsCount, instructions }) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COE Result</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0d1117;
    color: #e6edf3;
    padding: 20px;
    font-size: 13px;
    line-height: 1.6;
  }
  .header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 16px;
    border-bottom: 1px solid #21262d;
    margin-bottom: 20px;
  }
  .badge {
    background: #1f6feb;
    color: white;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .meta {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }
  .meta-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px;
  }
  .meta-card label {
    font-size: 10px;
    text-transform: uppercase;
    color: #7d8590;
    letter-spacing: 0.8px;
    display: block;
    margin-bottom: 4px;
  }
  .meta-card span {
    font-size: 13px;
    font-weight: 600;
    color: #e6edf3;
  }
  .section {
    margin-bottom: 20px;
  }
  .section-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #7d8590;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #21262d;
  }
  .prompt-box {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 16px;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 12px;
    white-space: pre-wrap;
    word-break: break-word;
    color: #adbac7;
    max-height: 400px;
    overflow-y: auto;
    line-height: 1.7;
  }
  .handoff-box {
    background: #0d2035;
    border: 1px solid #1f6feb;
    border-radius: 8px;
    padding: 16px;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 11px;
    white-space: pre;
    color: #79c0ff;
    max-height: 300px;
    overflow: auto;
  }
  .instructions {
    list-style: none;
    counter-reset: step;
  }
  .instructions li {
    counter-increment: step;
    display: flex;
    gap: 12px;
    padding: 8px 12px;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    margin-bottom: 6px;
  }
  .instructions li::before {
    content: counter(step);
    background: #1f6feb;
    color: white;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 700;
    flex-shrink: 0;
  }
  .copy-btn {
    background: #238636;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    margin-top: 8px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .copy-btn:hover { background: #2ea043; }
  .elapsed { color: #3fb950; font-size: 11px; }
</style>
</head>
<body>
<div class="header">
  <div class="badge">${commandName}</div>
  <div style="font-size:15px;font-weight:600">${vehicle}</div>
  <div class="elapsed" style="margin-left:auto">${elapsed}ms</div>
</div>

<div class="meta">
  <div class="meta-card"><label>VIN</label><span>${vin || '—'}</span></div>
  <div class="meta-card"><label>Command</label><span>/${commandName}</span></div>
  <div class="meta-card"><label>Modules</label><span>${subPromptsCount || 1}</span></div>
  <div class="meta-card"><label>Time</label><span>${new Date(timestamp).toLocaleTimeString()}</span></div>
</div>

${instructions.length ? `
<div class="section">
  <div class="section-title">Next Steps</div>
  <ul class="instructions">
    ${instructions.map(i => `<li>${i.replace(/^\d+\.\s*/, '')}</li>`).join('')}
  </ul>
</div>` : ''}

${handoffBlock ? `
<div class="section">
  <div class="section-title">Copilot Handoff Block</div>
  <div class="handoff-box">${escapeHtml(handoffBlock)}</div>
  <button class="copy-btn" onclick="copyHandoff()">📋 Copy Handoff Block → Paste into Copilot</button>
</div>` : ''}

${prompt ? `
<div class="section">
  <div class="section-title">Generated Prompt (auto-copied to clipboard)</div>
  <div class="prompt-box">${escapeHtml(prompt.substring(0, 3000))}${prompt.length > 3000 ? '\n\n... [truncated — full prompt in clipboard]' : ''}</div>
</div>` : ''}

<script>
  const vscode = acquireVsCodeApi();
  const handoff = ${JSON.stringify(handoffBlock)};
  const prompt  = ${JSON.stringify(prompt)};

  function copyHandoff() {
    navigator.clipboard.writeText(handoff).then(() => {
      const btn = document.querySelector('.copy-btn');
      btn.textContent = '✓ Copied! Now paste into Microsoft Copilot';
      btn.style.background = '#388bfd';
      setTimeout(() => {
        btn.textContent = '📋 Copy Handoff Block → Paste into Copilot';
        btn.style.background = '#238636';
      }, 3000);
    });
  }

  function escapeHtml(text) {
    return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
</script>
</body>
</html>`;
}

function escapeHtml(str) {
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Health Check ──────────────────────────────────────────────────────────────
async function runHealthCheck() {
  const checks = await healthCheck();
  const lines = Object.entries(checks).map(([k, v]) => {
    const icon = v === 'OK' ? '$(check)' : v === 'OFFLINE' ? '$(error)' : '$(warning)';
    return `${icon} ${k}: ${v}`;
  });

  const msg = lines.join('  |  ');
  vscode.window.showInformationMessage(`COE Health: ${msg}`);
  log(`Health check: ${JSON.stringify(checks)}`);
}

// ── Open Widget ───────────────────────────────────────────────────────────────
async function openPricingWidget() {
  const config = vscode.workspace.getConfiguration('coe');
  const url = config.get('vehiclePricingWidgetUrl') || 'http://localhost:5173';
  vscode.env.openExternal(vscode.Uri.parse(url));
}

// ── Logging ───────────────────────────────────────────────────────────────────
function log(msg) {
  const ts = new Date().toLocaleTimeString();
  outputChannel.appendLine(`[${ts}] ${msg}`);
}

function deactivate() {
  log('COE Pricing Intelligence deactivated.');
}

module.exports = { activate, deactivate };
