#!/usr/bin/env node
// unslop — Claude Code SessionStart activation hook
//
// Runs on every session start:
//   1. Writes flag file at $CLAUDE_CONFIG_DIR/.unslop-active (statusline reads this)
//   2. Emits unslop ruleset as hidden SessionStart context
//   3. Detects missing statusline config and emits setup nudge

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  getDefaultMode, safeWriteFlag, getFlagPath,
  getTurnCounterPath, resetTurnCount,
} = require('./unslop-config');

const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
const flagPath = getFlagPath();
const counterPath = getTurnCounterPath();
const settingsPath = path.join(claudeDir, 'settings.json');

const mode = getDefaultMode();

// Persona-drift reset: a new session always starts at turn 0. RMTBench /
// HorizonBench report that long contexts accumulate drift; the counter is
// only meaningful within a single session, so we zero it here.
resetTurnCount(counterPath);

if (mode === 'off') {
  try { fs.unlinkSync(flagPath); } catch (e) {}
  process.stdout.write('OK');
  process.exit(0);
}

safeWriteFlag(flagPath, mode);

// Independent modes have their own skill files — don't emit the full ruleset.
const INDEPENDENT_MODES = new Set(['commit', 'review']);

if (INDEPENDENT_MODES.has(mode)) {
  process.stdout.write('UNSLOP MODE ACTIVE — level: ' + mode + '. Behavior defined by /unslop-' + mode + ' skill.');
  process.exit(0);
}

// Read SKILL.md — the single source of truth for unslop behavior.
// Plugin installs: __dirname = <plugin_root>/hooks/, SKILL.md at <plugin_root>/skills/unslop/SKILL.md
// Standalone installs: __dirname = $CLAUDE_CONFIG_DIR/hooks/, SKILL.md won't exist — falls back to activation rule then hardcoded rules.
let skillContent = '';
try {
  skillContent = fs.readFileSync(
    path.join(__dirname, '..', 'skills', 'unslop', 'SKILL.md'), 'utf8'
  );
} catch (e) { /* try activation rule next */ }

// Fallback: try the activation rule file (lighter weight than full SKILL.md)
let activationRule = '';
if (!skillContent) {
  try {
    activationRule = fs.readFileSync(
      path.join(__dirname, '..', 'rules', 'unslop-activate.md'), 'utf8'
    ).trim();
  } catch (e) { /* will use hardcoded fallback */ }
}

let output;

if (skillContent) {
  const body = skillContent.replace(/^---[\s\S]*?---\s*/, '');

  // Filter intensity table and examples to the active level
  const filtered = body.split('\n').reduce((acc, line) => {
    const tableRowMatch = line.match(/^\|\s*\*\*(\S+?)\*\*\s*\|/);
    if (tableRowMatch) {
      if (tableRowMatch[1] === mode) {
        acc.push(line);
      }
      return acc;
    }

    const exampleMatch = line.match(/^- (\S+?):\s/);
    if (exampleMatch) {
      if (exampleMatch[1] === mode) {
        acc.push(line);
      }
      return acc;
    }

    acc.push(line);
    return acc;
  }, []);

  output = 'UNSLOP MODE ACTIVE — level: ' + mode + '\n\n' + filtered.join('\n');
} else if (activationRule) {
  output = 'UNSLOP MODE ACTIVE — level: ' + mode + '\n\n' + activationRule;
} else {
  output =
    'UNSLOP MODE ACTIVE — level: ' + mode + '\n\n' +
    'Write like a careful human. All technical substance stays exact. Only AI-slop dies.\n\n' +
    '## Persistence\n\n' +
    'ACTIVE EVERY RESPONSE. No revert after many turns. No drift back into AI-template English.\n' +
    'Off only: "stop unslop" / "normal mode".\n\n' +
    'Current level: **' + mode + '**. Switch: `/unslop subtle|balanced|full|voice-match|anti-detector`.\n\n' +
    '## Rules\n\n' +
    'Drop: sycophancy ("great question", "I\'d be happy to"), stock vocab (delve/tapestry/testament/seamless/holistic/leverage-as-filler), ' +
    'hedging stacks ("it\'s important to note that"), tricolon padding, em-dash pileups, performative balance, tidy five-paragraph shapes.\n\n' +
    'Keep: technical terms exact, code unchanged, real uncertainty when honest.\n' +
    'Engineer burstiness: mix short and long sentences deliberately.\n\n' +
    'Pattern: [concrete observation]. [why]. [what to do next].\n\n' +
    '## Auto-Clarity\n\n' +
    'Drop unslop style for: security warnings, irreversible actions, legal/medical/financial precision, user confused. Resume after.\n\n' +
    '## Boundaries\n\n' +
    'Code/commits/PRs: write normal. "stop unslop" or "normal mode": revert. Level persists until changed or session ends.';
}

// Detect missing statusline config — nudge Claude to help set it up
try {
  let hasStatusline = false;
  if (fs.existsSync(settingsPath)) {
    const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
    if (settings.statusLine) {
      hasStatusline = true;
    }
  }

  if (!hasStatusline) {
    const isWindows = process.platform === 'win32';
    const scriptName = isWindows ? 'unslop-statusline.ps1' : 'unslop-statusline.sh';
    const scriptPath = path.join(__dirname, scriptName);
    const command = isWindows
      ? `powershell -ExecutionPolicy Bypass -File "${scriptPath}"`
      : `bash "${scriptPath}"`;
    const statusLineSnippet =
      '"statusLine": { "type": "command", "command": ' + JSON.stringify(command) + ' }';
    output += "\n\n" +
      "STATUSLINE SETUP NEEDED: The unslop plugin includes a statusline badge showing active mode " +
      "(e.g. [unslop], [unslop:full]). It is not configured yet. " +
      "To enable, add this to " + path.join(claudeDir, 'settings.json') + ": " +
      statusLineSnippet + " " +
      "Proactively offer to set this up for the user on first interaction.";
  }
} catch (e) {
  // Silent fail — don't block session start over statusline detection
}

process.stdout.write(output);
