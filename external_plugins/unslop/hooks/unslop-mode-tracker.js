#!/usr/bin/env node
// unslop — UserPromptSubmit hook to track which unslop mode is active
// Inspects user input for /unslop commands and natural language activation,
// writes mode to flag file, and emits per-turn style reinforcement.

const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  getDefaultMode, safeWriteFlag, readFlag, getFlagPath,
  getTurnCounterPath, readTurnCount, writeTurnCount, resetTurnCount,
} = require('./unslop-config');

const flagPath = getFlagPath();
const counterPath = getTurnCounterPath();

// Persona-drift reinforcement checkpoints. RMTBench / HorizonBench (Apr
// 2026) measure persona degradation beginning around turn 8 and becoming
// severe by turn 12–16. We re-emit at these points rather than every turn
// so the reinforcement stays salient. After turn 32 we fall back to every
// 16 turns to avoid spam in marathon sessions.
const DRIFT_CHECKPOINTS = new Set([8, 16, 24, 32]);
function isDriftCheckpoint(turn) {
  if (DRIFT_CHECKPOINTS.has(turn)) return true;
  if (turn > 32 && turn % 16 === 0) return true;
  return false;
}

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const prompt = (data.prompt || '').trim();
    const promptLower = prompt.toLowerCase();

    // Natural language activation (e.g. "activate unslop", "turn on unslop mode",
    // "make this sound human", "humanize this").
    if (/\b(activate|enable|turn on|start)\b.*\bunslop\b/i.test(prompt) ||
        /\bunslop\b.*\b(mode|activate|enable|turn on|start)\b/i.test(prompt) ||
        /\b(humanize|de-?slop|make.*sound human|less robotic)\b/i.test(prompt)) {
      if (!/\b(stop|disable|turn off|deactivate)\b/i.test(prompt)) {
        const mode = getDefaultMode();
        if (mode !== 'off') {
          safeWriteFlag(flagPath, mode);
        }
      }
    }

    // Match /unslop slash commands
    if (promptLower.startsWith('/unslop')) {
      const parts = promptLower.split(/\s+/);
      const cmd = parts[0];
      const arg = parts[1] || '';

      let mode = null;

      if (cmd === '/unslop-commit') {
        mode = 'commit';
      } else if (cmd === '/unslop-review') {
        mode = 'review';
      } else if (cmd === '/unslop' || cmd === '/unslop:unslop') {
        if (arg === 'subtle') mode = 'subtle';
        else if (arg === 'balanced') mode = 'balanced';
        else if (arg === 'full') mode = 'full';
        else if (arg === 'voice-match') mode = 'voice-match';
        else if (arg === 'anti-detector') mode = 'anti-detector';
        else mode = getDefaultMode();
      }

      if (mode && mode !== 'off') {
        safeWriteFlag(flagPath, mode);
      } else if (mode === 'off') {
        try { fs.unlinkSync(flagPath); } catch (e) {}
      }
    }

    // Also match /unslop-file (the file-rewriter command) — set mode to current default
    if (promptLower.startsWith('/humanize') && !promptLower.startsWith('/unslop')) {
      const mode = getDefaultMode();
      if (mode !== 'off') {
        safeWriteFlag(flagPath, mode);
      }
    }

    // Detect deactivation — natural language and explicit stop phrases
    if (/\b(stop|disable|deactivate|turn off)\b.*\bunslop\b/i.test(prompt) ||
        /\bunslop\b.*\b(stop|disable|deactivate|turn off)\b/i.test(prompt) ||
        /\bnormal mode\b/i.test(prompt) ||
        /\brobotic mode\b/i.test(prompt)) {
      try { fs.unlinkSync(flagPath); } catch (e) {}
      resetTurnCount(counterPath);
    }

    // Per-turn reinforcement: emit a structured reminder when unslop is active.
    // The SessionStart hook injects the full ruleset once, but models lose it
    // when other plugins inject competing style instructions every turn.
    // Skip independent modes (commit, review) — they have their own skill behavior.
    const INDEPENDENT_MODES = new Set(['commit', 'review']);
    const activeMode = readFlag(flagPath);
    if (activeMode && !INDEPENDENT_MODES.has(activeMode)) {
      // Advance the persona-drift counter and decide whether this turn
      // warrants an expanded reinforcement. Best-effort: counter failures
      // degrade to the standard per-turn banner.
      const turn = readTurnCount(counterPath) + 1;
      writeTurnCount(counterPath, turn);

      let additional = "UNSLOP MODE ACTIVE (" + activeMode + "). " +
        "Drop sycophancy/stock-vocab/hedging-stacks/tricolons/em-dash-pileups. " +
        "Engineer burstiness. Code/commits/security: write normal.";

      if (isDriftCheckpoint(turn)) {
        // RMTBench / HorizonBench: at these turn counts models silently
        // drift back to template English. Re-state the ruleset header
        // explicitly so the model has fresh context to anchor against.
        additional +=
          " [drift-check turn " + turn + "] Persona drift risk is elevated after " +
          "long contexts (RMTBench / HorizonBench arXiv 2604.17283). Re-anchor: " +
          "no 'great question'/'certainly'/'I'd be happy to'; no delve/tapestry/" +
          "testament/seamless/holistic; no 'it's important to note'; avoid symmetric " +
          "tricolons and em-dash pileups; mix sentence lengths; admit uncertainty " +
          "when real. Keep all code, URLs, numbers, and technical terms exact.";
      }

      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "UserPromptSubmit",
          additionalContext: additional
        }
      }));
    } else {
      // Mode not active — counter should be zero so the next activation
      // starts fresh rather than inheriting stale turns.
      resetTurnCount(counterPath);
    }
  } catch (e) {
    // Silent fail
  }
});
