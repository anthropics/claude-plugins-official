#!/usr/bin/env node
/**
 * parse-session.mjs
 * Reads a Claude Code JSONL session file and outputs a structured context summary.
 * Usage: node parse-session.mjs [session-id-or-path] [--last N]
 */
import fs   from 'node:fs';
import path from 'node:path';
import os   from 'node:os';

const args      = process.argv.slice(2);
const lastN     = (() => { const i = args.indexOf('--last'); return i !== -1 ? parseInt(args[i+1]) || 30 : 30; })();
const sessionArg = args.filter(a => !a.startsWith('--') && a !== String(lastN)).join('').trim();

// ── Find project sessions dir ─────────────────────────────────────────────────
function projectDirName(cwd) {
  return cwd.replace(/\\/g, '/').replace(/[:/]/g, '-').replace(/^-+/, '');
}

function findSessions() {
  const cwd      = process.cwd();
  const projKey  = projectDirName(cwd);
  const base     = path.join(os.homedir(), '.claude', 'projects', projKey);
  if (!fs.existsSync(base)) return [];
  return fs.readdirSync(base)
    .filter(f => f.endsWith('.jsonl'))
    .map(f => ({ name: f, full: path.join(base, f), mtime: fs.statSync(path.join(base, f)).mtime }))
    .sort((a, b) => b.mtime - a.mtime);
}

// ── Pick session file ─────────────────────────────────────────────────────────
let filePath;
if (sessionArg) {
  if (fs.existsSync(sessionArg)) {
    filePath = sessionArg;
  } else {
    const sessions = findSessions();
    const match = sessions.find(s => s.name.includes(sessionArg));
    if (!match) { console.error('Session not found:', sessionArg); process.exit(1); }
    filePath = match.full;
  }
} else {
  const sessions = findSessions();
  if (!sessions.length) { console.error('No sessions found for this project.'); process.exit(1); }
  filePath = sessions[0].full;
}

// ── Parse JSONL ───────────────────────────────────────────────────────────────
const stat        = fs.statSync(filePath);
const MB          = 1024 * 1024;
const MAX_HEAD    = 3 * MB;
const MAX_TAIL    = 1 * MB;

function readParts() {
  if (stat.size <= MAX_HEAD + MAX_TAIL) return fs.readFileSync(filePath, 'utf8');
  const fd      = fs.openSync(filePath, 'r');
  const headBuf = Buffer.alloc(MAX_HEAD);
  const tailBuf = Buffer.alloc(MAX_TAIL);
  fs.readSync(fd, headBuf, 0, MAX_HEAD, 0);
  fs.readSync(fd, tailBuf, 0, MAX_TAIL, stat.size - MAX_TAIL);
  fs.closeSync(fd);
  return headBuf.toString('utf8') + '\n' + tailBuf.toString('utf8');
}

const raw  = readParts();
const lines = raw.split('\n').filter(l => l.trim());

const userMessages   = [];
const assistantTexts = [];
const filesWritten   = new Set();
const filesEdited    = new Set();
const jiraSet        = new Set();
const toolCounts     = {};
const seenUser       = new Set();
let firstTs = null, lastTs = null, turns = 0;

for (const line of lines) {
  let obj;
  try { obj = JSON.parse(line); } catch { continue; }

  const ts = obj.timestamp;
  if (ts) {
    if (!firstTs || ts < firstTs) firstTs = ts;
    if (!lastTs  || ts > lastTs)  lastTs  = ts;
  }

  // ── User messages ───────────────────────────────────────────────────────────
  if (obj.type === 'user') {
    const content = obj.message?.content;
    const texts = Array.isArray(content)
      ? content.filter(c => c.type === 'text').map(c => c.text || '')
      : (typeof content === 'string' ? [content] : []);

    for (const text of texts) {
      const clean = text.trim();
      if (clean.length < 15) continue;
      if (clean.includes('This session is being continued')) continue;
      if (clean.includes('<system-reminder>')) continue;
      if (clean.includes('IMPORTANT: this context')) continue;

      const key = clean.substring(0, 80);
      if (!seenUser.has(key)) {
        seenUser.add(key);
        userMessages.push({ ts: ts || '', text: clean.substring(0, 800) });
      }

      const jira = clean.match(/\b[A-Z]{2,}-\d+\b/g);
      if (jira) jira.forEach(t => jiraSet.add(t));
    }
  }

  // ── Assistant turns ─────────────────────────────────────────────────────────
  if (obj.type === 'assistant') {
    turns++;
    const content = obj.message?.content;
    if (!Array.isArray(content)) continue;

    for (const item of content) {
      // Collect plain text from last N turns
      if (item.type === 'text' && item.text) {
        assistantTexts.push({ ts: ts || '', text: item.text.trim().substring(0, 600) });
      }

      if (item.type !== 'tool_use') continue;
      const name = item.name || '';
      toolCounts[name] = (toolCounts[name] || 0) + 1;

      if (name === 'Write' && item.input?.file_path) filesWritten.add(item.input.file_path);
      if (name === 'Edit'  && item.input?.file_path) filesEdited.add(item.input.file_path);

      const cmd = (item.input?.command) || '';
      const jira = cmd.match(/\b[A-Z]{2,}-\d+\b/g);
      if (jira) jira.forEach(t => jiraSet.add(t));
    }
  }
}

// ── Output ────────────────────────────────────────────────────────────────────
const result = {
  file:         path.basename(filePath),
  sessionId:    path.basename(filePath, '.jsonl'),
  filePath,
  sizeKB:       Math.round(stat.size / 1024),
  truncated:    stat.size > MAX_HEAD + MAX_TAIL,
  firstTs,
  lastTs,
  turns,
  userMessages,
  lastAssistantTexts: assistantTexts.slice(-lastN),
  jiraTickets:  [...jiraSet].sort(),
  filesWritten: [...filesWritten],
  filesEdited:  [...filesEdited],
  toolCounts,
};

console.log(JSON.stringify(result, null, 2));
