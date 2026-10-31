#!/usr/bin/env node
// PkgDiet PreToolUse Guard for Claude Code
// Intercepts Bash tool execution to verify npm/pnpm/yarn/bun package installs against PkgDiet policy.

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const deny = reason => {
  process.stdout.write(JSON.stringify({
    decision: 'block',
    reason,
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason,
    }
  }));
  process.exit(0);
};

let input;
try {
  input = JSON.parse(fs.readFileSync(0, 'utf8'));
} catch {
  deny('🔒 PkgDiet blocked execution: malformed tool input JSON.');
  process.exit(1);
}

if (!input || typeof input !== 'object') {
  deny('🔒 PkgDiet blocked execution: tool input must be a JSON object.');
  process.exit(1);
}

const command = String(input?.tool_input?.command || input?.input?.command || '');
const cwd = input?.cwd || process.cwd();

// Only inspect package manager install commands
const isInstall = /(?:^|[;&|\s])(npm|pnpm|yarn|bun)\s+.*?(?:install|i|add)\b/.test(command);
if (!isInstall) {
  process.exit(0);
}

const SAFE_NAME_REGEX = /^(@[a-zA-Z0-9_.-]+\/)?[a-zA-Z0-9_.-]+$/;

const runCheck = names => {
  const localCli = path.join(cwd, 'node_modules', 'pkgdiet', 'build', 'cli.js');
  if (fs.existsSync(localCli)) {
    return spawnSync(process.execPath, [localCli, 'check', '--json', ...names], { cwd, encoding: 'utf8', shell: false });
  }
  const localBin = path.join(cwd, 'node_modules', '.bin', process.platform === 'win32' ? 'pkgdiet.cmd' : 'pkgdiet');
  if (fs.existsSync(localBin)) {
    return spawnSync(localBin, ['check', '--json', ...names], { cwd, encoding: 'utf8', shell: process.platform === 'win32' });
  }
  return spawnSync('npx', ['-y', 'pkgdiet@2.0.1', 'check', '--json', ...names], { cwd, encoding: 'utf8', shell: process.platform === 'win32' });
};

// Try importing core commandParser
let parseInstallCommands;
try {
  const localCorePath = path.join(cwd, 'node_modules', '@pkgdiet', 'core', 'dist', 'commandParser.js');
  if (fs.existsSync(localCorePath)) {
    const mod = await import('file://' + (process.platform === 'win32' ? '/' : '') + localCorePath.replace(/\\/g, '/'));
    parseInstallCommands = mod.parseInstallCommands;
  }
} catch {}

if (!parseInstallCommands) {
  try {
    const mod = await import('@pkgdiet/core/dist/commandParser.js');
    parseInstallCommands = mod.parseInstallCommands;
  } catch {}
}

if (!parseInstallCommands) {
  // Degraded fallback mode
  if (/[$*?|;&<>\x60]/.test(command)) {
    deny('🔒 PkgDiet blocked install [DEGRADED MODE]: core parser unavailable and command contains dynamic shell syntax.');
  }

  const tokens = command.trim().split(/\s+/);
  const verbIdx = tokens.findIndex(t => /^(?:install|i|add)$/.test(t));
  if (verbIdx === -1) {
    deny('🔒 PkgDiet blocked install [DEGRADED MODE]: unable to parse install verb.');
  }

  const rawArgs = tokens.slice(verbIdx + 1).filter(t => !t.startsWith('-'));
  if (rawArgs.length === 0) {
    deny('🔒 PkgDiet blocked bare install [DEGRADED MODE]. Pin to an exact version (package@x.y.z) after PkgDiet approves it.');
  }

  const pkgNames = [];
  for (const arg of rawArgs) {
    if (arg.includes('@npm:')) {
      const aliasMatch = arg.match(/^(@?[a-zA-Z0-9_.-]+(?:\/[a-zA-Z0-9_.-]+)?)@npm:(@?[a-zA-Z0-9_.-]+(?:\/[a-zA-Z0-9_.-]+)?)(?:@(v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?.*))?$/i);
      if (!aliasMatch || !aliasMatch[3]) {
        deny('🔒 PkgDiet blocked unpinned install of alias ' + arg + ' [DEGRADED MODE]. Pin to an exact version.');
      }
      const targetName = aliasMatch[2];
      if (!SAFE_NAME_REGEX.test(targetName)) {
        deny('🔒 PkgDiet blocked unsafe package name: ' + targetName);
      }
      pkgNames.push(targetName);
      continue;
    }

    const atIdx = arg.lastIndexOf('@');
    if (atIdx <= 0 || !/^v?\d+\.\d+\.\d+/.test(arg.slice(atIdx + 1))) {
      deny('🔒 PkgDiet blocked unpinned install of ' + arg + ' [DEGRADED MODE]. Pin to an exact version (package@x.y.z) after PkgDiet approves it.');
    }
    const name = arg.slice(0, atIdx);
    if (!SAFE_NAME_REGEX.test(name)) {
      deny('🔒 PkgDiet blocked unsafe package name: ' + name);
    }
    pkgNames.push(name);
  }

  const check = runCheck(pkgNames);
  if (check.status !== 0) {
    deny('🔒 PkgDiet blocked install: failed policy check.');
  }
  process.exit(0);
}

const cmds = parseInstallCommands(command);
for (const cmd of cmds) {
  if (!cmd.isInstall) continue;

  if (cmd.isAmbiguous) {
    deny('🔒 PkgDiet blocked ambiguous install command (' + (cmd.ambiguityReason || 'dynamic syntax') + ').');
  }

  if (cmd.isBareInstall) {
    deny('🔒 PkgDiet blocked bare install (package.json-driven). Use an exact version (e.g. npm i pkg@1.2.3) after PkgDiet approves it.');
  }

  const unpinned = cmd.packages.filter(p => !p.isPinned);
  if (unpinned.length > 0) {
    deny('🔒 PkgDiet blocked unpinned install of ' + unpinned.map(p => p.raw).join(', ') + '. Pin to an exact version after PkgDiet approves it.');
  }

  const names = cmd.packages.map(p => p.aliasOf || p.name);
  for (const name of names) {
    if (!SAFE_NAME_REGEX.test(name)) {
      deny('🔒 PkgDiet blocked unsafe package name: ' + name);
    }
  }

  if (names.length > 0) {
    const check = runCheck(names);
    if (check.status !== 0) {
      deny('🔒 PkgDiet blocked this install — one or more packages failed policy. Run: npx -y pkgdiet@2.0.1 check ' + names.join(' ') + ' --json');
    }
  }
}
process.exit(0);
