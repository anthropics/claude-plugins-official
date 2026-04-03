#!/usr/bin/env node

/**
 * SessionStart Hook — CLI detection + lightweight status
 *
 * Detects Codex/Gemini CLI availability, ensures artifact directory exists.
 * No routing table — that lives in CLAUDE.md (single source of truth).
 */

import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';

function detectCli(command) {
  try {
    execSync(`${command} --version`, { stdio: 'pipe', timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

let input = '';
process.stdin.setEncoding('utf-8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  const hasCodex = detectCli('codex');
  const hasGemini = detectCli('gemini');

  // Ensure artifact directory
  try {
    mkdirSync(join(process.cwd(), '.ksk', 'artifact'), { recursive: true });
  } catch {}

  const providers = [];
  if (hasCodex) providers.push('Codex');
  if (hasGemini) providers.push('Gemini');

  const providerNote = providers.length > 0
    ? providers.join(' + ')
    : 'NONE (install codex or gemini CLI for external verification)';

  const reminder = [
    `<system-reminder>`,
    `[KhakiSketcher v0.2] Providers: ${providerNote}`,
    `Model Policy: Sonnet=code | Codex=reasoning | Gemini=vision`,
    `Skills: /ksk:plan | /ksk:run | /ksk:complex-debug | /ksk:architecture | /ksk:ui-redesign | /ksk:visual-qa | /ksk:code-review | /ksk:test`,
    `</system-reminder>`,
  ].join('\n');

  process.stdout.write(reminder);
});

export default function() {}
