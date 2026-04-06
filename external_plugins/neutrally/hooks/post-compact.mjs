#!/usr/bin/env node
/**
 * Neutrally post-compact hook
 * Fires on: SessionStart (compact)
 *
 * After /compact, Claude loses conversation history. This hook re-injects
 * the most critical context: what we were working on, recent decisions,
 * and current project state. Tighter than session-start (no general preferences).
 */
import { readFileSync } from 'fs';
import { execSync } from 'child_process';
import { readCredentials, getApiBase, getAuthHeaders } from './lib/credentials.mjs';
import { readSessionState } from './lib/session-state.mjs';
import { fetchContext, searchMemory, fetchRecentMessages, fetchMemoryItems } from './lib/api.mjs';

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

async function main() {
  const input = parseStdin();
  const sessionId = input.session_id || input.conversation_id || 'default';
  const projectName = getProjectName();

  const creds = readCredentials();
  if (!creds?.token) {
    process.stdout.write('{}');
    process.exit(0);
  }

  const apiBase = getApiBase(creds);
  const headers = getAuthHeaders(creds);

  // Fetch in parallel: project search + recent activity + project memory items
  const [searchResults, recentMessages, memoryItems] = await Promise.all([
    searchMemory(apiBase, headers, projectName),
    fetchRecentMessages(apiBase, headers, 8),
    fetchMemoryItems(apiBase, headers, 'note'),
  ]);

  const parts = [];

  // Recent session captures: find the most recent Claude Code entries for this project
  const recentCaptures = memoryItems
    .filter(item => {
      const src = item.metadata?.source;
      const haystack = `${item.title || ''} ${item.content || ''}`.toLowerCase();
      return src === 'claude-code-plugin' && haystack.includes(projectName.toLowerCase());
    })
    .slice(0, 5);

  if (recentCaptures.length) {
    const lines = recentCaptures.map(m => {
      const preview = (m.content || '').slice(0, 300).replace(/\n/g, ' ');
      return `• ${preview}`;
    });
    parts.push(`**Recent work on "${projectName}" (before compact):**\n${lines.join('\n')}`);
  }

  // Conversation search for project
  const hits = searchResults.slice(0, 3);
  if (hits.length) {
    const lines = hits.map(r => `• **${r.title}**: ${(r.summary || '').slice(0, 150)}`);
    parts.push(`**Related memory:**\n${lines.join('\n')}`);
  }

  // Very recent messages (what was happening just before compact)
  const recent = recentMessages.slice(0, 5);
  if (recent.length) {
    const lines = recent.map(m => {
      const preview = String(m.content || '').slice(0, 150).replace(/\n/g, ' ');
      return `• [${m.role}] ${preview}`;
    });
    parts.push(`**Messages before compact:**\n${lines.join('\n')}`);
  }

  if (parts.length === 0) {
    process.stdout.write('{}');
    process.exit(0);
  }

  const brief = `<neutrally-memory>\n**Context restored after /compact:**\n\n${parts.join('\n\n')}\n</neutrally-memory>`;

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'SessionStart',
        additionalContext: brief,
      },
    })
  );
  process.exit(0);
}

main().catch(() => {
  process.stdout.write('{}');
  process.exit(0);
});
