#!/usr/bin/env node
/**
 * Neutrally user-message capture hook
 * Fires on: UserPromptSubmit (every user message)
 *
 * Records the user's message verbatim as the start of a new exchange.
 * This is the "intent" side of the capture — stored in full.
 * Claude's activity is captured separately in conversation-capture.mjs.
 *
 * This hook is async (non-blocking): Claude Code doesn't wait for it.
 */
import { readFileSync } from 'fs';
import { readSessionState, writeSessionState } from './lib/session-state.mjs';

function parseStdin() {
  try {
    const raw = readFileSync(0, 'utf8').trim();
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

async function main() {
  const input = parseStdin();
  const sessionId = input.session_id || input.conversation_id || 'default';
  const prompt = String(input.prompt || input.message || '').trim();

  if (!prompt) {
    process.stdout.write('{}');
    process.exit(0);
  }

  const state = readSessionState(sessionId);

  // Close any open exchange that wasn't properly closed
  if (state.currentExchange?.tools?.length > 0) {
    state.pendingExchanges.push({ ...state.currentExchange });
  }

  // Open a new exchange for this user message
  state.currentExchange = {
    userMessage: prompt,
    tools: [],
    startedAt: Date.now(),
    projectName: state.projectName || '',
    projectPath: state.projectPath || process.cwd(),
  };

  writeSessionState(sessionId, state);

  process.stdout.write('{}');
  process.exit(0);
}

main().catch(() => {
  process.stdout.write('{}');
  process.exit(0);
});
