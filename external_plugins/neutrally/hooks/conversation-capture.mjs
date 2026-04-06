#!/usr/bin/env node
/**
 * Neutrally conversation capture hook
 * Fires on: PostToolUse (Edit, Write, Read, Bash, Glob, Grep, MultiEdit)
 *
 * Two responsibilities:
 * 1. Always: record tool activity into the current exchange buffer (fast, <5ms)
 * 2. Every N minutes: flush pending exchanges to Neutrally API
 *
 * This hook is async (non-blocking). The flush is awaited before exit, but
 * since Claude Code doesn't wait for async hooks, it runs in the background.
 *
 * Crash recovery: buffered exchanges are always written to disk first.
 * The session-start hook recovers and flushes data from crashed sessions.
 */
import { readFileSync } from 'fs';
import { readCredentials, readPluginConfig, getApiBase, getAuthHeaders } from './lib/credentials.mjs';
import { readSessionState, writeSessionState } from './lib/session-state.mjs';
import { flushExchanges } from './lib/api.mjs';

function parseStdin() {
  try {
    const raw = readFileSync(0, 'utf8').trim();
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

/**
 * Convert a tool call into a human-readable one-liner for storage.
 * Summaries are intentionally terse — this is activity metadata, not a transcript.
 */
function summariseTool(toolName, toolInput) {
  switch (toolName) {
    case 'Edit': {
      const file = toolInput.file_path || 'file';
      return `Edited ${file}`;
    }
    case 'MultiEdit': {
      const file = toolInput.file_path || 'file';
      return `Edited ${file} (multiple changes)`;
    }
    case 'Write': {
      const file = toolInput.file_path || 'file';
      return `Created ${file}`;
    }
    case 'Read': {
      const file = toolInput.file_path || 'file';
      return `Read ${file}`;
    }
    case 'Bash': {
      const cmd = String(toolInput.command || '').replace(/\n/g, ' ').slice(0, 100);
      return `Ran: ${cmd}`;
    }
    case 'Glob': {
      return `Glob: ${toolInput.pattern || ''}`;
    }
    case 'Grep': {
      const pat = String(toolInput.pattern || '').slice(0, 60);
      return `Grep: "${pat}"`;
    }
    default:
      return `Used ${toolName}`;
  }
}

async function main() {
  const input = parseStdin();
  const sessionId = input.session_id || input.conversation_id || 'default';
  const toolName = input.tool_name || '';
  const toolInput = input.tool_input || {};

  // Read current state
  const state = readSessionState(sessionId);

  // Append tool summary to current exchange
  const summary = summariseTool(toolName, toolInput);

  if (state.currentExchange) {
    state.currentExchange.tools.push(summary);
  } else {
    // No exchange open — tool fired without a preceding user message (e.g., sub-agent)
    // Open a synthetic exchange to capture it
    state.currentExchange = {
      userMessage: '',
      tools: [summary],
      startedAt: Date.now(),
      projectName: state.projectName || '',
      projectPath: state.projectPath || process.cwd(),
    };
  }

  // Check flush timer
  const config = readPluginConfig();
  const captureIntervalMs = (config.captureIntervalMinutes || 5) * 60 * 1000;
  const now = Date.now();
  const elapsed = now - (state.lastCapture || 0);

  if (elapsed >= captureIntervalMs) {
    // ── Flush time ──
    // Close the current exchange and move everything to the flush queue
    if (state.currentExchange) {
      state.currentExchange.projectName = state.projectName || '';
      state.currentExchange.projectPath = state.projectPath || process.cwd();
      state.pendingExchanges.push({ ...state.currentExchange });
      state.currentExchange = null;
    }

    const toFlush = [...state.pendingExchanges];
    state.pendingExchanges = [];
    state.lastCapture = now;

    // Write state to disk BEFORE the API call (crash safety)
    writeSessionState(sessionId, state);

    // Flush to Neutrally API
    const creds = readCredentials();
    if (creds?.token && toFlush.length > 0) {
      const apiBase = getApiBase(creds);
      const headers = getAuthHeaders(creds);
      await flushExchanges(apiBase, headers, toFlush).catch(() => {});
    }
  } else {
    // ── Fast path — just update the buffer ──
    writeSessionState(sessionId, state);
  }

  process.stdout.write('{}');
  process.exit(0);
}

main().catch(() => {
  process.stdout.write('{}');
  process.exit(0);
});
