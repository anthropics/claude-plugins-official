#!/usr/bin/env node
// mine-transcripts.mjs — local, offline aggregation of Claude Code session
// transcripts into a small JSON summary (and optionally a self-contained
// HTML "receipt") for a personal impact report.
//
// Reads only ~/.claude/projects/**/*.jsonl (this machine's own session logs)
// and optionally cross-references local `git log`. No network calls, no API
// calls — pure local file + git parsing. Safe to run often.
//
// Usage:
//   node mine-transcripts.mjs [--days 30] [--since YYYY-MM-DD] [--repo <substr>] [--html <path>]
//
// Always prints the JSON summary to stdout. If --html is given, also writes
// a self-contained, styled HTML "receipt" to that path (no JS frameworks,
// no external resources — safe to open directly or hand to the Artifact tool).

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { execFileSync } from 'node:child_process';

function parseArgs(argv) {
  const out = { days: 30, repo: null, since: null, html: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--days') out.days = parseInt(argv[++i], 10);
    else if (a === '--repo') out.repo = argv[++i];
    else if (a === '--since') out.since = argv[++i];
    else if (a === '--html') out.html = argv[++i];
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const now = new Date();
// Local midnight, not UTC — `--since 2026-07-01` means that date on the dev's
// calendar, and active days and git commits are both keyed locally too.
const cutoff = args.since
  ? new Date(args.since + 'T00:00:00')
  : new Date(now.getTime() - args.days * 86400000);

// Fail loudly on a bad window. An unparseable date makes `cutoff` NaN, and
// every `ts < cutoff` test then reads false — so the run would silently scan
// all history and label the result "NaN-NaN-NaN" instead of erroring.
if (isNaN(cutoff)) {
  const bad = args.since ? `--since ${args.since}` : `--days ${process.argv[process.argv.indexOf('--days') + 1]}`;
  console.error(
    `mine-transcripts: could not read a date from \`${bad}\`.\n` +
      `  --days expects a number (e.g. --days 30)\n` +
      `  --since expects YYYY-MM-DD (e.g. --since 2026-07-01)`
  );
  process.exit(2);
}

const projectsDir = path.join(os.homedir(), '.claude', 'projects');

function findJsonlFiles(dir) {
  const out = [];
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...findJsonlFiles(full));
    else if (e.isFile() && e.name.endsWith('.jsonl')) out.push(full);
  }
  return out;
}

function countLines(s) {
  if (typeof s !== 'string' || s.length === 0) return 0;
  return s.split('\n').length;
}

// Bucket a tool/MCP name into a handful of human categories, weighted by
// relative token cost (see RELATIVE_TOKEN_WEIGHTS), for the "where the spend
// went" breakdown. Grouping happens here so raw tool names — which enumerate
// the dev's connected services — never reach the report.
function categoryForTool(tool) {
  const CODE = new Set(['Edit', 'MultiEdit', 'Write', 'NotebookEdit']);
  const SHELL = new Set(['Bash', 'BashOutput', 'KillShell']);
  const RESEARCH = new Set([
    'Read', 'Grep', 'Glob', 'WebSearch', 'WebFetch', 'Skill', 'AskUserQuestion',
    'TodoWrite', 'ExitPlanMode', 'SlashCommand',
  ]);
  const DELEGATED = new Set(['Agent', 'Task']);
  if (CODE.has(tool)) return 'Writing & editing code';
  if (SHELL.has(tool)) return 'Running & verifying (shell)';
  if (DELEGATED.has(tool) || /^Task/.test(tool)) return 'Delegated / automated work';
  if (RESEARCH.has(tool)) return 'Reading & research';
  if (tool.startsWith('mcp__')) {
    const low = tool.toLowerCase();
    if (/(send|create_draft|draft|post|upload|update|copy|delete|reply|schedule_message|authenticate)/.test(low)) {
      return 'Collaboration (Slack, email, docs, etc.)';
    }
    return 'Reading & research';
  }
  // Anything else — a tool this script doesn't know, from a newer build or a
  // plugin — reads as research rather than being miscredited to delegation.
  return 'Reading & research';
}

// A command starts at the beginning of a line or after a shell separator —
// `;`, `&&`, `||`, `|`, or a `then`/`do`/`else` keyword. Requiring one of
// those keeps prose that merely mentions "git commit" from counting, while
// still catching the multi-line and guarded forms agents actually write.
// (The `m` flag is what makes multi-line blocks work.)
const CMD_START = String.raw`(?:^\s*|[;&|]\s*|\s&&\s*|\b(?:then|do|else)\s+)`;

// Tokens allowed between `git` and its subcommand: options, plus the value of
// the options that take a separate one (whose values hold `/` and `=`, so
// they can't be matched as a plain word class). Bare words are deliberately
// NOT allowed — they'd be a different subcommand, and `git cat-file commit
// HEAD` is not a commit.
const GIT_OPTS = String.raw`(?:(?:-C|-c|--git-dir|--work-tree|--exec-path|--namespace)\s+\S+\s+|--?\S+\s+)*`;

// (?=\s|$) rather than \b — \b would also match "commit-tree"/"commit-graph".
const CMD_GIT_COMMIT = new RegExp(CMD_START + String.raw`git\s+` + GIT_OPTS + String.raw`commit(?=\s|$)`, 'm');
const CMD_GH_PR_CREATE = new RegExp(CMD_START + String.raw`gh\s+pr\s+create(?=\s|$)`, 'm');

// Relative weights between token types, derived from the ratios between
// published per-token rates (output tokens cost ~5x input; cache writes
// ~1.25x; cache reads ~0.1x). These are RATIOS used only to weight "where the
// spend went" across activity categories — never converted to a dollar
// figure, since that would imply a precision (and a real bill) we can't back.
const RELATIVE_TOKEN_WEIGHTS = { input: 1, output: 5, cacheCreation: 1.25, cacheRead: 0.1 };

function freshAgg() {
  return {
    sessions: new Set(),
    prompts: new Set(),
    activeDays: new Set(),
    filesTouched: new Set(),
    linesTouched: 0,
    gitCommitCmds: 0,
    prCreateCmds: 0,
    costWeight: 0, // relative compute weight (unitless, see RELATIVE_TOKEN_WEIGHTS) — used for byRepo pctSpend
  };
}

const overall = freshAgg();
overall.categoryCost = {}; // category label -> relative weight (unitless)
overall.firstSeen = null;
overall.lastSeen = null;

// Tracks, per session, the category of the most recent tool call — so a
// text-only turn (Claude thinking/writing a response, no further tool use)
// gets folded into whatever activity it's wrapping up, rather than its own
// "thinking" bucket.
const lastCategoryBySession = new Map();
const DEFAULT_CATEGORY = 'Reading & research'; // fallback for a session's first turn(s), before any tool call

const byRepo = {}; // repoName -> { ...freshAgg(), cwd: Set }

function getRepo(cwd) {
  const name = cwd ? path.basename(cwd) : 'unknown';
  if (!byRepo[name]) {
    byRepo[name] = { ...freshAgg(), cwd: new Set() };
  }
  if (cwd) byRepo[name].cwd.add(cwd);
  return byRepo[name];
}

const files = findJsonlFiles(projectsDir);
let filesScanned = 0;
let linesScanned = 0;

// A local YYYY-MM-DD calendar date. Matches what `git log --date=short`
// prints, which is what active days are cross-referenced against.
function localDay(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// A resumed session re-serializes its earlier entries into the new transcript,
// so the same entry can appear in more than one file. Dedupe globally by uuid
// or everything it carries (tool calls, files, lines, cost) counts twice.
const seenUuids = new Set();

// Merge two usage records from the same API response, field by field. In
// practice every entry of a response repeats the identical usage, so any one
// of them would do; taking the max is the safe reading either way, and holds
// if a future format only puts the final counts on the last entry.
function maxUsage(a, b) {
  if (!a) return b;
  const out = { ...a };
  for (const k of Object.keys(b)) {
    if (typeof b[k] === 'number') out[k] = Math.max(a[k] || 0, b[k]);
  }
  return out;
}

for (const file of files) {
  let stat;
  try {
    stat = fs.statSync(file);
  } catch {
    continue;
  }
  if (stat.mtime < cutoff) continue; // fast skip — nothing recent in this file

  let content;
  try {
    content = fs.readFileSync(file, 'utf8');
  } catch {
    continue;
  }
  filesScanned++;

  // One API response is split across several `assistant` entries — one per
  // content block — that share a requestId and each repeat the response's
  // usage. Group them here so the response's cost is charged exactly once;
  // counting per entry overstates it ~3x, and unevenly (responses with more
  // tool calls have more entries), which would skew the category split.
  const responses = new Map(); // requestId -> { usage, blocks, repo, sid }

  for (const line of content.split('\n')) {
    if (!line.trim()) continue;
    linesScanned++;
    let obj;
    try {
      obj = JSON.parse(line);
    } catch {
      continue;
    }

    if (!obj.timestamp) continue;
    const ts = new Date(obj.timestamp);
    if (isNaN(ts) || ts < cutoff) continue;

    if (obj.uuid) {
      if (seenUuids.has(obj.uuid)) continue; // replayed by a resumed session
      seenUuids.add(obj.uuid);
    }

    const cwd = obj.cwd;
    if (args.repo && !(cwd || '').includes(args.repo)) continue;

    // Key active days by LOCAL calendar date. `git log --date=short` reports
    // author-local dates, so slicing the UTC timestamp would put an evening
    // session on the next day and stop it matching its own commits.
    const date = localDay(ts);
    const repo = getRepo(cwd);

    if (!overall.firstSeen || ts < overall.firstSeen) overall.firstSeen = ts;
    if (!overall.lastSeen || ts > overall.lastSeen) overall.lastSeen = ts;

    overall.activeDays.add(date);
    repo.activeDays.add(date);

    if (obj.sessionId) {
      overall.sessions.add(obj.sessionId);
      repo.sessions.add(obj.sessionId);
    }

    // Count real user turns (not tool-result-only echoes back to the model,
    // and not sidechain turns — those are an orchestrator delegating to a
    // subagent, not the human prompting Claude).
    if (obj.type === 'user' && obj.message && obj.promptId && !obj.isSidechain) {
      const c = obj.message.content;
      const isToolResultOnly =
        Array.isArray(c) && c.length > 0 && c.every((b) => b && b.type === 'tool_result');
      if (!isToolResultOnly) {
        overall.prompts.add(obj.promptId);
        repo.prompts.add(obj.promptId);
      }
    }

    if (obj.type === 'assistant' && obj.message) {
      const blocks = Array.isArray(obj.message.content) ? obj.message.content : [];

      // Accumulate this entry into its API response. The cost is charged once
      // per response, after the file is read — see the `responses` loop below.
      const rid = obj.requestId || (obj.message && obj.message.id) || obj.uuid;
      if (rid) {
        const r = responses.get(rid) || { usage: null, blocks: [], repo, sid: obj.sessionId };
        if (obj.message.usage) r.usage = maxUsage(r.usage, obj.message.usage);
        for (const b of blocks) if (b && b.type === 'tool_use') r.blocks.push(b);
        responses.set(rid, r);
      }

      for (const b of blocks) {
        if (!b || b.type !== 'tool_use') continue;
        const name = b.name || 'Unknown';
        const input = b.input || {};
        if (name === 'Edit' || name === 'NotebookEdit') {
          if (input.file_path) {
            overall.filesTouched.add(input.file_path);
            repo.filesTouched.add(input.file_path);
          }
          const n = Math.max(
            countLines(input.old_string ?? input.old_source),
            countLines(input.new_string ?? input.new_source)
          );
          overall.linesTouched += n;
          repo.linesTouched += n;
        } else if (name === 'MultiEdit') {
          if (input.file_path) {
            overall.filesTouched.add(input.file_path);
            repo.filesTouched.add(input.file_path);
          }
          for (const e of input.edits || []) {
            const n = Math.max(countLines(e.old_string), countLines(e.new_string));
            overall.linesTouched += n;
            repo.linesTouched += n;
          }
        } else if (name === 'Write') {
          if (input.file_path) {
            overall.filesTouched.add(input.file_path);
            repo.filesTouched.add(input.file_path);
          }
          const n = countLines(input.content);
          overall.linesTouched += n;
          repo.linesTouched += n;
        } else if (name === 'Bash') {
          const cmd = input.command || '';
          // Anchored to the start of a command so prose containing the words
          // "git commit" doesn't count. `m` and the newline/`then` separators
          // matter: multi-line blocks and guarded one-liners are the common
          // shapes. Any intervening tokens are allowed, to cover
          // pre-subcommand options whose values hold `/` or `=` (`git -C
          // <path> commit`, `git -c key=value commit`). (?=\s|$) rather than
          // \b, since \b also matches "commit-tree"/"commit-graph".
          if (CMD_GIT_COMMIT.test(cmd)) {
            overall.gitCommitCmds++;
            repo.gitCommitCmds++;
          }
          if (CMD_GH_PR_CREATE.test(cmd)) {
            overall.prCreateCmds++;
            repo.prCreateCmds++;
          }
        }
      }
    }
  }

  // Charge each API response's relative cost once, spread across the
  // categories of the tool calls it made. A response with no tool calls
  // (Claude thinking or writing a reply — e.g. the wrap-up after a batch of
  // edits) folds into the session's most recent category rather than becoming
  // a bucket of its own. Map iteration is insertion order, so sessions still
  // advance chronologically.
  for (const r of responses.values()) {
    if (!r.usage) continue;
    const w = RELATIVE_TOKEN_WEIGHTS;
    const weight =
      (r.usage.input_tokens || 0) * w.input +
      (r.usage.output_tokens || 0) * w.output +
      (r.usage.cache_creation_input_tokens || 0) * w.cacheCreation +
      (r.usage.cache_read_input_tokens || 0) * w.cacheRead;
    r.repo.costWeight += weight;
    if (r.blocks.length === 0) {
      const cat = lastCategoryBySession.get(r.sid) || DEFAULT_CATEGORY;
      overall.categoryCost[cat] = (overall.categoryCost[cat] || 0) + weight;
    } else {
      const share = weight / r.blocks.length;
      for (const b of r.blocks) {
        const cat = categoryForTool(b.name || 'Unknown');
        overall.categoryCost[cat] = (overall.categoryCost[cat] || 0) + share;
        lastCategoryBySession.set(r.sid, cat);
      }
    }
  }
}

// --- Local git cross-reference (no network) ---
// The dev's display name, for personalizing the receipt — read from global
// git config (the same identity used for commit attribution). Best-effort;
// null if unset.
function gitUserName() {
  try {
    const name = execFileSync('git', ['config', '--global', 'user.name'], {
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
    return name || null;
  } catch {
    return null;
  }
}

// For each repo dir we saw activity in, list commits authored by this user
// since the cutoff (sha + date), so we can both count them and de-duplicate
// across repos. Best-effort; failures are silent (not a git repo, no email
// configured, etc).
function gitCommits(cwd, sinceDate) {
  try {
    const email = execFileSync('git', ['-C', cwd, 'config', 'user.email'], {
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
    if (!email) return null;
    const out = execFileSync(
      'git',
      ['-C', cwd, 'log', `--since=${sinceDate}`, `--author=${email}`, '--date=short', '--pretty=format:%H %ad'],
      { encoding: 'utf8', timeout: 5000, stdio: ['ignore', 'pipe', 'ignore'] }
    );
    return out
      .split('\n')
      .filter(Boolean)
      .map((line) => {
        const sp = line.indexOf(' ');
        return { sha: line.slice(0, sp), date: line.slice(sp + 1) };
      });
  } catch {
    return null;
  }
}

// Resolve the shared `.git` dir for a worktree. Multiple "repos" (by basename)
// can be worktrees of the same checkout — `git log` on each only sees commits
// reachable from that worktree's branch, but branches can share ancestor
// commits, so naively summing per-repo commit counts can double-count. We
// flag repos that share a common-dir so the report can caveat this, and we
// de-duplicate the global total by commit SHA regardless.
function gitCommonDir(cwd) {
  try {
    const out = execFileSync('git', ['-C', cwd, 'rev-parse', '--git-common-dir'], {
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
    return out ? path.resolve(cwd, out) : null;
  } catch {
    return null;
  }
}

// Local, not UTC: this is handed to `git log --since=`, which reads it in
// local time, and it's the date printed on the receipt.
const sinceDate = localDay(cutoff);
const repoSummaries = {};
const globalCommits = new Map(); // sha -> date, deduped across all repos
const commonDirCounts = new Map(); // git-common-dir -> number of repos sharing it
let anyGitData = false;

for (const [name, agg] of Object.entries(byRepo)) {
  const cwd = [...agg.cwd][0];
  const commits = cwd ? gitCommits(cwd, sinceDate) : null;
  const commonDir = cwd ? gitCommonDir(cwd) : null;
  if (commonDir) commonDirCounts.set(commonDir, (commonDirCounts.get(commonDir) || 0) + 1);

  let gitActiveDayOverlap = null;
  if (commits) {
    anyGitData = true;
    const days = new Set(commits.map((c) => c.date));
    let overlap = 0;
    for (const d of agg.activeDays) if (days.has(d)) overlap++;
    gitActiveDayOverlap = overlap;
    for (const c of commits) globalCommits.set(c.sha, c.date);
  }
  repoSummaries[name] = {
    sessions: agg.sessions.size,
    prompts: agg.prompts.size,
    activeDays: agg.activeDays.size,
    filesTouched: agg.filesTouched.size,
    linesTouched: agg.linesTouched,
    gitCommitCmds: agg.gitCommitCmds,
    prCreateCmds: agg.prCreateCmds,
    gitCommitsByYou: commits ? commits.length : null,
    gitActiveDayOverlap,
    _commonDir: commonDir, // stripped before output, below
    _costWeight: agg.costWeight, // stripped after pctSpend is computed, below
    _activeDays: agg.activeDays, // stripped after the rollup unions them, below
    _shas: commits ? commits.map((c) => c.sha) : null, // ditto — see the rollup
  };
}

// Mark repos that share git history with another repo in this report — their
// per-repo commit counts may overlap (the global total below is de-duplicated
// by commit SHA, so it's accurate even when this is true).
for (const r of Object.values(repoSummaries)) {
  if (r._commonDir && commonDirCounts.get(r._commonDir) > 1) r.sharedGitHistory = true;
  delete r._commonDir;
}

// Each repo's share of total relative compute (see RELATIVE_TOKEN_WEIGHTS) —
// percentages across ALL repos (incl. ones rolled into "(other repos)") sum to ~100.
const totalCostWeight = Object.values(repoSummaries).reduce((a, r) => a + r._costWeight, 0) || 1;
for (const r of Object.values(repoSummaries)) {
  r.pctSpend = (100 * r._costWeight) / totalCostWeight;
  delete r._costWeight;
}

// Sort repos by their share of relative compute (pctSpend) desc, keep top 12,
// roll the rest into "(other repos)" — along with anything that produced no
// output AND consumed a negligible share of spend, which is what background
// and no-cwd sessions look like. The spend clause matters: a repo the dev only
// read in — an architecture review, an incident dig — touches no files but can
// be one of the biggest line items in the report, and naming it is the point.
const WORTH_NAMING_PCT = 1;
const hasOutput = ([, r]) =>
  r.filesTouched > 0 ||
  r.linesTouched > 0 ||
  r.gitCommitCmds > 0 ||
  r.prCreateCmds > 0 ||
  r.gitCommitsByYou ||
  r.pctSpend >= WORTH_NAMING_PCT;
const sortedRepos = Object.entries(repoSummaries)
  .filter(hasOutput)
  .sort((a, b) => b[1].pctSpend - a[1].pctSpend);
const topRepos = Object.fromEntries(sortedRepos.slice(0, 12));
const otherRepos = [
  ...Object.entries(repoSummaries).filter((e) => !hasOutput(e)),
  ...sortedRepos.slice(12),
];
if (otherRepos.length) {
  const rollup = {
    sessions: 0, prompts: 0, activeDays: 0, filesTouched: 0, linesTouched: 0,
    gitCommitCmds: 0, prCreateCmds: 0, gitCommitsByYou: null, pctSpend: 0, repoCount: otherRepos.length,
  };
  // Active days and commits are UNIONS, not sums. One day worked across three
  // of these repos is one active day. And worktrees of the same checkout each
  // report the same shared ancestor commits, so adding their counts inflates
  // the row — dedupe by SHA, exactly as the report-wide total does.
  const rollupDays = new Set();
  const rollupShas = new Set();
  let anyRollupGit = false;
  for (const [, r] of otherRepos) {
    rollup.sessions += r.sessions;
    rollup.prompts += r.prompts;
    rollup.filesTouched += r.filesTouched;
    rollup.linesTouched += r.linesTouched;
    rollup.gitCommitCmds += r.gitCommitCmds;
    rollup.prCreateCmds += r.prCreateCmds;
    rollup.pctSpend += r.pctSpend;
    for (const d of r._activeDays) rollupDays.add(d);
    if (r._shas) {
      anyRollupGit = true;
      for (const s of r._shas) rollupShas.add(s);
    }
  }
  rollup.activeDays = rollupDays.size;
  rollup.gitCommitsByYou = anyRollupGit ? rollupShas.size : null;
  topRepos['(other repos)'] = rollup;
}

const totalCalendarDays = Math.max(1, Math.round((now - cutoff) / 86400000));

// Global commit total: de-duplicated by SHA across all repos (see gitCommonDir
// above — worktrees of the same repo would otherwise double-count shared
// ancestor commits).
const gitCommitDates = new Set(globalCommits.values());
let gitActiveDayOverlapTotal = 0;
for (const d of overall.activeDays) if (gitCommitDates.has(d)) gitActiveDayOverlapTotal++;

const summary = {
  generatedAt: now.toISOString(),
  userName: gitUserName(),
  // Derived from the real cutoff, not `args.days` — an explicit --since sets
  // the window without touching --days, so echoing the flag misreports it.
  periodDays: totalCalendarDays,
  since: sinceDate,
  until: localDay(now),
  filesScanned,
  linesScanned,
  totals: {
    sessions: overall.sessions.size,
    prompts: overall.prompts.size,
    activeDays: overall.activeDays.size,
    calendarDays: totalCalendarDays,
    filesTouched: overall.filesTouched.size,
    linesTouched: overall.linesTouched,
    gitCommitCmds: overall.gitCommitCmds,
    prCreateCmds: overall.prCreateCmds,
    // De-duplicated by commit SHA across repos (see gitCommonDir). Per-repo
    // gitCommitsByYou figures are NOT deduplicated and may sum to more than this.
    gitCommitsByYou: anyGitData ? globalCommits.size : null,
    gitActiveDayOverlap: anyGitData ? gitActiveDayOverlapTotal : null,
    // Relative cost weight per activity category (unitless — see
    // RELATIVE_TOKEN_WEIGHTS). Use categoryBreakdown()/the HTML bars to turn
    // this into percentages; don't sum these into a dollar figure.
    // firstSeen/lastSeen are deliberately not emitted: nothing in the report
    // uses them, and the exact instant of a dev's first and last turn is a
    // working-hours signal that has no business in a spend receipt.
    categoryCost: overall.categoryCost,
  },
  byRepo: topRepos,
};

// Strip the internal working fields. These are read by the "(other repos)"
// rollup above — which unions them rather than summing — so they have to
// survive until now, but they must not reach the output.
for (const r of Object.values(topRepos)) {
  delete r._activeDays;
  delete r._shas;
}

process.stdout.write(JSON.stringify(summary, null, 2));

// --- Optional HTML "receipt" ---
if (args.html) {
  try {
    fs.writeFileSync(args.html, renderHTML(summary));
  } catch (e) {
    process.stderr.write(`\n(failed to write HTML receipt: ${e.message})\n`);
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function fmt(n) {
  return Number(n).toLocaleString('en-US');
}

function fmtPct(pct) {
  if (pct <= 0) return '–';
  if (pct < 1) return '<1%';
  return `${Math.round(pct)}%`;
}

// Turn the relative cost-weight map into percentages for the bars. Weights
// are unitless (see RELATIVE_TOKEN_WEIGHTS) — only their proportions matter.
function categoryBreakdown(categoryCost) {
  const total = Object.values(categoryCost).reduce((a, b) => a + b, 0) || 1;
  return Object.entries(categoryCost)
    .map(([label, weight]) => ({ label, pct: (100 * weight) / total }))
    .filter((c) => c.pct > 0)
    .sort((a, b) => b.pct - a.pct);
}

function renderHTML(s) {
  const t = s.totals;
  const cats = categoryBreakdown(t.categoryCost);

  const repoEntries = Object.entries(s.byRepo);
  let anySharedGitHistory = false;
  let anyCmdFallback = false;
  const repoRows = repoEntries
    .map(([name, r]) => {
      let commits;
      if (r.gitCommitsByYou != null) {
        commits = fmt(r.gitCommitsByYou) + (r.sharedGitHistory ? '†' : '');
        if (r.sharedGitHistory) anySharedGitHistory = true;
      } else if (r.gitCommitCmds > 0) {
        commits = `~${fmt(r.gitCommitCmds)}*`;
        anyCmdFallback = true;
      } else {
        commits = '–';
      }
      return `
      <tr>
        <td>${escapeHtml(name)}</td>
        <td class="num">${fmt(r.sessions)}</td>
        <td class="num">${fmt(r.filesTouched)}</td>
        <td class="num">${fmt(r.linesTouched)}</td>
        <td class="num">${commits}</td>
        <td class="num">${fmtPct(r.pctSpend)}</td>
      </tr>`;
    })
    .join('');
  const repoFootnotes = [
    anySharedGitHistory && '† shares commit history with another project here (worktrees of the same repo) — the total above is de-duplicated by commit, but these per-repo counts may overlap.',
    anyCmdFallback && '* git history unavailable for this project; based on `git commit` commands run in Claude Code sessions instead.',
  ].filter(Boolean).map(t => `<div class="note">${escapeHtml(t)}</div>`).join('');

  const barRows = cats
    .map(
      (c) => `
      <div class="bar-row">
        <div class="bar-label"><span>${escapeHtml(c.label)}</span><span>${c.pct.toFixed(0)}%</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${c.pct.toFixed(1)}%"></div></div>
      </div>`
    )
    .join('');

  const shipped = (t.gitCommitsByYou || 0) + (t.prCreateCmds || 0);
  const overlapNote = t.gitActiveDayOverlap != null
    ? `${fmt(t.gitActiveDayOverlap)} of your ${fmt(t.activeDays)} active days also had a git commit in one of these projects.`
    : null;

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude Code Receipt — ${escapeHtml(s.since)} to ${escapeHtml(s.until)}</title>
<style>
  :root { --ink:#1f1d1a; --paper:#fdfcf7; --muted:#8a8478; --accent:#d97757; --line:#d8d3c8; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; }
  body {
    min-height:100vh;
    padding: 2.5rem 1rem;
    background: #e7e3da;
    font-family: ui-monospace, "SF Mono", "Menlo", "Consolas", monospace;
    color: var(--ink);
    display:flex; justify-content:center; align-items:flex-start;
  }
  .receipt {
    background: var(--paper);
    width: 100%; max-width: 440px;
    padding: 2rem 1.75rem 1.5rem;
    box-shadow: 0 12px 32px rgba(0,0,0,0.18);
    border-radius: 2px;
  }
  h1 { text-align:center; font-size:1rem; letter-spacing:0.25em; margin:0; font-weight:700; }
  h2 { font-size:0.7rem; letter-spacing:0.15em; text-transform:uppercase; color:var(--muted); margin: 1.25rem 0 0.6rem; font-weight:700; }
  .sub { text-align:center; color:var(--muted); font-size:0.7rem; margin-top:0.35rem; letter-spacing:0.05em; }
  .stars { text-align:center; color: var(--accent); font-size:0.8rem; margin: 0.5rem 0; letter-spacing:0.4em; }
  hr { border:none; border-top:1px dashed var(--line); margin: 1.1rem 0; }
  .row { display:flex; justify-content:space-between; gap:0.75rem; font-size:0.8rem; padding:0.2rem 0; }
  .row .label { color: var(--ink); }
  .row .value { font-weight:700; font-variant-numeric: tabular-nums; }
  .total {
    display:flex; justify-content:space-between; align-items:baseline;
    font-size:1.05rem; font-weight:800; letter-spacing:0.05em;
    border-top: 2px solid var(--ink); border-bottom: 2px solid var(--ink);
    padding: 0.6rem 0; margin: 1rem 0; text-transform:uppercase;
  }
  .total .value { color: var(--accent); font-size:1.3rem; }
  .bar-row { margin: 0.55rem 0; }
  .bar-label { display:flex; justify-content:space-between; font-size:0.72rem; margin-bottom:0.25rem; }
  .bar-track { background:#efece4; border-radius:3px; height:7px; overflow:hidden; }
  .bar-fill { background: var(--accent); height:100%; border-radius:3px; }
  table { width:100%; table-layout:fixed; border-collapse:collapse; font-size:0.65rem; }
  th, td { text-align:left; padding:0.3rem 0.2rem; border-bottom:1px dotted var(--line); overflow-wrap:break-word; }
  th:first-child, td:first-child { width:30%; }
  th { font-weight:700; color: var(--muted); text-transform:uppercase; font-size:0.6rem; letter-spacing:0.04em; }
  td.num, th.num { text-align:right; }
  td.num { white-space:nowrap; }
  .barcode {
    height: 36px; margin: 1.25rem 0 0.75rem;
    background: repeating-linear-gradient(90deg, var(--ink) 0 2px, transparent 2px 4px, var(--ink) 4px 5px, transparent 5px 9px, var(--ink) 9px 12px, transparent 12px 14px);
    opacity: 0.85;
  }
  .footer { text-align:center; font-size:0.65rem; color:var(--muted); line-height:1.6; }
  .footer a { color: inherit; }
  .note { font-size:0.68rem; color:var(--muted); line-height:1.5; margin-top:0.4rem; }
</style>
</head>
<body>
  <div class="receipt">
    <h1>Claude Code</h1>
    <div class="stars">★ ★ ★ ★ ★</div>
    <div class="sub">USAGE RECEIPT${s.userName ? ` — ${escapeHtml(s.userName)}` : ''}</div>
    <div class="sub">${escapeHtml(s.since)} — ${escapeHtml(s.until)} (${t.activeDays} of ${t.calendarDays} days active)</div>
    <hr>
    <div class="row"><span class="label">Sessions</span><span class="value">${fmt(t.sessions)}</span></div>
    <div class="row"><span class="label">Prompts</span><span class="value">${fmt(t.prompts)}</span></div>
    <div class="row"><span class="label">Files touched</span><span class="value">${fmt(t.filesTouched)}</span></div>
    <div class="row"><span class="label">Lines touched (approx.)</span><span class="value">${fmt(t.linesTouched)}</span></div>
    ${t.gitCommitsByYou != null ? `<div class="row"><span class="label">Git commits</span><span class="value">${fmt(t.gitCommitsByYou)}</span></div>` : ''}
    ${t.prCreateCmds ? `<div class="row"><span class="label">PRs opened</span><span class="value">${fmt(t.prCreateCmds)}</span></div>` : ''}
    <div class="total"><span>Commits + PRs shipped</span><span class="value">${fmt(shipped)}</span></div>
    <div class="note">Commits in projects you used Claude Code in, plus PRs opened via Claude Code, this window. Commits aren't all individually CC-attributed.${overlapNote ? ` ${escapeHtml(overlapNote)}` : ''}</div>

    <h2>Where the spend went</h2>
    ${barRows}
    <div class="note">Relative share of compute, weighted by token cost (output tokens count ~5x input; cached tokens count less) — not a dollar figure, and not the same as a count of tool calls.</div>

    <h2>Top projects</h2>
    <table>
      <thead><tr><th>Project</th><th class="num">Sessions</th><th class="num">Files</th><th class="num">Lines</th><th class="num">Commits</th><th class="num">% Spend</th></tr></thead>
      <tbody>${repoRows}</tbody>
    </table>
    ${repoFootnotes}

    <div class="barcode"></div>
    <div class="footer">
      Built on this machine from ${fmt(s.filesScanned)} local session files —<br>
      counts and project names only, no code or conversation content.<br>
      ${escapeHtml(s.generatedAt)}
    </div>
  </div>
</body>
</html>`;
}
