/**
 * Per-session state management for the Neutrally plugin.
 * Each Claude Code session gets its own state file at:
 *   ~/.neutrally/sessions/{sessionId}.json
 *
 * State schema:
 * {
 *   sessionId: string,
 *   projectName: string,
 *   projectPath: string,
 *   lastCapture: number,       // epoch ms of last flush to API
 *   pendingExchanges: Exchange[],  // flushed on next opportunity
 *   currentExchange: Exchange | null  // in-progress exchange
 * }
 *
 * Exchange schema:
 * {
 *   userMessage: string,
 *   tools: string[],   // ["Edited app/foo.ts", "Ran: npm test"]
 *   startedAt: number,
 *   projectName: string,
 *   projectPath: string
 * }
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, unlinkSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

const SESSIONS_DIR = join(homedir(), '.neutrally', 'sessions');

function sanitizeId(id) {
  return String(id).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64);
}

function sessionPath(sessionId) {
  return join(SESSIONS_DIR, `${sanitizeId(sessionId)}.json`);
}

function defaultState(sessionId) {
  return {
    sessionId,
    projectName: '',
    projectPath: '',
    lastCapture: Date.now(),
    pendingExchanges: [],
    currentExchange: null,
  };
}

export function ensureSessionsDir() {
  mkdirSync(SESSIONS_DIR, { recursive: true });
}

export function readSessionState(sessionId) {
  try {
    const p = sessionPath(sessionId);
    if (!existsSync(p)) return defaultState(sessionId);
    const parsed = JSON.parse(readFileSync(p, 'utf8'));
    return { ...defaultState(sessionId), ...parsed };
  } catch {
    return defaultState(sessionId);
  }
}

export function writeSessionState(sessionId, state) {
  ensureSessionsDir();
  writeFileSync(sessionPath(sessionId), JSON.stringify(state, null, 2));
}

/**
 * Returns sessions other than the current one that have unflushed data.
 * Used by session-start to recover data from crashed/abandoned sessions.
 */
export function listPendingSessions(currentSessionId) {
  try {
    if (!existsSync(SESSIONS_DIR)) return [];
    const currentFile = `${sanitizeId(currentSessionId)}.json`;

    return readdirSync(SESSIONS_DIR)
      .filter(f => f.endsWith('.json') && f !== currentFile)
      .map(f => {
        try {
          const fullPath = join(SESSIONS_DIR, f);
          const data = JSON.parse(readFileSync(fullPath, 'utf8'));
          const hasPending =
            (data.pendingExchanges?.length > 0) ||
            (data.currentExchange?.tools?.length > 0);
          return hasPending ? { filePath: fullPath, state: data } : null;
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

export function markSessionFlushed(filePath) {
  try {
    const data = JSON.parse(readFileSync(filePath, 'utf8'));
    data.pendingExchanges = [];
    data.currentExchange = null;
    writeFileSync(filePath, JSON.stringify(data, null, 2));
  } catch {}
}
