#!/usr/bin/env node
/**
 * Neutrally session-start hook
 * Fires on: SessionStart (startup, resume)
 *
 * Actions:
 * 1. Flush any pending exchanges from previous sessions (crash recovery)
 * 2. Fetch user context, project memory, and recent activity from Neutrally
 * 3. Inject a concise memory brief into the session context
 * 4. Reset session state for the new session
 */
import { readFileSync } from 'fs';
import { execSync } from 'child_process';
import { readCredentials, readPluginConfig, getApiBase, getAuthHeaders } from './lib/credentials.mjs';
import {
  readSessionState,
  writeSessionState,
  listPendingSessions,
  markSessionFlushed,
} from './lib/session-state.mjs';
import {
  fetchContext,
  searchMemory,
  fetchRecentMessages,
  fetchMemoryItems,
  flushExchanges,
} from './lib/api.mjs';

function parseStdin() {
  try {
    const raw = readFileSync(0, 'utf8').trim();
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function getProjectName() {
  try {
    const remote = execSync('git remote get-url origin 2>/dev/null', {
      encoding: 'utf8',
      timeout: 2000,
    }).trim();
    if (remote) {
      const match = remote.match(/\/([^\/]+?)(\.git)?$/);
      if (match) return match[1];
    }
  } catch {}
  return process.cwd().split('/').pop() || 'project';
}

function buildContextBrief(context, searchResults, recentMessages, memoryItems, projectName) {
  const parts = [];

  // User context: tech stack, projects, interests
  if (context?.user_context) {
    const { stack, projects, interests } = context.user_context;
    const lines = [];
    if (stack?.length) lines.push(`Tech stack: ${stack.join(', ')}`);
    if (projects?.length) lines.push(`Known projects: ${projects.join(', ')}`);
    if (interests?.length) lines.push(`Focus areas: ${interests.join(', ')}`);
    if (lines.length) parts.push(`**User context:**\n${lines.join('\n')}`);
  }

  // Project-specific memory items (notes saved via Claude Code)
  const projectItems = memoryItems
    .filter(item => {
      const haystack = `${item.title || ''} ${item.content || ''}`.toLowerCase();
      return haystack.includes(projectName.toLowerCase());
    })
    .slice(0, 6);

  if (projectItems.length) {
    const lines = projectItems.map(m => {
      const preview = (m.content || '').slice(0, 200).replace(/\n/g, ' ');
      return `• **${m.title}**: ${preview}`;
    });
    parts.push(`**Saved memory for "${projectName}":**\n${lines.join('\n')}`);
  }

  // Semantic search results for the current project
  const hits = searchResults.slice(0, 3);
  if (hits.length) {
    const lines = hits.map(r => `• **${r.title}**: ${(r.summary || '').slice(0, 150)}`);
    parts.push(`**Related conversations:**\n${lines.join('\n')}`);
  }

  // Recent conversation context
  const recent = recentMessages.slice(0, 4);
  if (recent.length) {
    const lines = recent.map(m => {
      const preview = String(m.content || '').slice(0, 120).replace(/\n/g, ' ');
      return `• [${m.role}] ${preview}`;
    });
    parts.push(`**Recent activity:**\n${lines.join('\n')}`);
  }

  return parts;
}

function outputContext(eventName, text) {
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: eventName,
        additionalContext: text,
      },
    })
  );
}

async function main() {
  const input = parseStdin();
  const sessionId = input.session_id || input.conversation_id || 'default';
  const projectName = getProjectName();
  const projectPath = process.cwd();

  const creds = readCredentials();

  // Not authenticated: prompt to set up
  if (!creds?.token) {
    outputContext(
      'SessionStart',
      '<neutrally-memory>\nNeutrally memory is not connected.\nRun /neutrally:setup to connect persistent cross-session memory.\n</neutrally-memory>'
    );
    process.exit(0);
  }

  const apiBase = getApiBase(creds);
  const headers = getAuthHeaders(creds);

  // ── Step 1: Crash recovery — flush pending exchanges from previous sessions ──
  const pendingSessions = listPendingSessions(sessionId);
  if (pendingSessions.length > 0) {
    for (const { filePath, state } of pendingSessions) {
      const toFlush = [
        ...(state.pendingExchanges || []),
        ...(state.currentExchange ? [state.currentExchange] : []),
      ];
      if (toFlush.length > 0) {
        await flushExchanges(apiBase, headers, toFlush).catch(() => {});
      }
      markSessionFlushed(filePath);
    }
  }

  // ── Step 2: Reset state for this new session ──
  writeSessionState(sessionId, {
    sessionId,
    projectName,
    projectPath,
    lastCapture: Date.now(),
    pendingExchanges: [],
    currentExchange: null,
  });

  // ── Step 3: Fetch context data in parallel ──
  const [context, searchResults, recentMessages, memoryItems] = await Promise.all([
    fetchContext(apiBase, headers),
    searchMemory(apiBase, headers, projectName),
    fetchRecentMessages(apiBase, headers, 5),
    fetchMemoryItems(apiBase, headers, 'note'),
  ]);

  // ── Step 4: Build and inject context brief ──
  const parts = buildContextBrief(context, searchResults, recentMessages, memoryItems, projectName);

  if (parts.length === 0) {
    process.stdout.write('{}');
    process.exit(0);
  }

  const brief = `<neutrally-memory>\n${parts.join('\n\n')}\n</neutrally-memory>`;
  outputContext('SessionStart', brief);
  process.exit(0);
}

main().catch(() => {
  process.stdout.write('{}');
  process.exit(0);
});
