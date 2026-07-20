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

// A local YYYY-MM-DD calendar date. This is the unit the whole report counts
// in: active days, the window, and git's own --date=short all key off it.
function localDay(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// Local midnight N days back, by CALENDAR arithmetic. Subtracting N*86400000
// assumes every day is 24h, which is false across a DST boundary — it lands an
// hour early and can slip `since` onto the previous date.
function midnightDaysAgo(from, n) {
  const d = new Date(from);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - n);
  return d;
}

// Distinct local dates in [from, to] inclusive — the denominator of "active on
// N of M days". Counting elapsed milliseconds instead answers a different
// question: `--days 7` spans 8 calendar dates, so a daily user could be
// "active on 8 of 7 days".
function calendarDaysBetween(from, to) {
  const a = new Date(from); a.setHours(0, 0, 0, 0);
  const b = new Date(to); b.setHours(0, 0, 0, 0);
  let n = 0;
  for (const d = a; d <= b; d.setDate(d.getDate() + 1)) n++;
  return Math.max(1, n);
}

const args = parseArgs(process.argv.slice(2));
const now = new Date();
// Local midnight, not UTC — `--since 2026-07-01` means that date on the dev's
// calendar, and active days and git commits are both keyed locally too.
// `--days 30` means the last 30 calendar days INCLUDING today — so the floor
// is midnight 29 days back, and the window spans exactly 30 dates. Going back
// a full 30 spans 31, which is how a daily user ends up "active on 31 of 30
// days".
const cutoff = args.since
  ? new Date(args.since + 'T00:00:00')
  : midnightDaysAgo(now, Math.max(0, args.days - 1));

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

// There is deliberately no "delegated" category. Delegation is a mechanism,
// not a kind of work: a subagent that spends an hour editing a repo did an
// hour of editing, and that is what the dev paid for. Its cost lands in the
// activity it performed and the project it performed it on, same as any other
// work. Spawning one costs almost nothing and is not worth a row.
// There is deliberately no per-activity breakdown of spend.
//
// It's tempting — "38% of your compute went to reading code" reads like insight.
// But a turn's cost is ~90% context handling, and half of that is re-reading
// what earlier turns put there. Charging it to whichever tool happened to fire
// on that turn is a modeling choice, not a measurement, and the choice decides
// the answer: on one real month, web search came out at 11%, 28% or 51% of
// spend depending on which defensible weighting you picked. Three reasonable
// definitions, three different headlines, nothing in the data to arbitrate.
//
// Per-PROJECT spend survives that test — the ranking is invariant and the
// numbers move a few points at most — because it divides a real quantity (a
// session's whole cost) by a real fact (which project the session served),
// rather than by which tool fired when. So the report keeps `pctSpend` and
// says nothing about activity mix.

// A command starts at the beginning of a line or after a shell separator —
// `;`, `&&`, `||`, `|`, or a `then`/`do`/`else` keyword. Requiring one of
// those keeps prose that merely mentions "git commit" from counting, while
// still catching the multi-line and guarded forms agents actually write.
// (The `m` flag is what makes multi-line blocks work.)
const CMD_START = String.raw`(?:^\s*|[;&|]\s*|\s&&\s*|\b(?:then|do|else)\s+)`;

// There is no `git commit` counter.
//
// A Bash tool call carries no working directory, so a commit made in a
// throwaway fixture repo under the agent's own scratchpad is indistinguishable
// from one made in the dev's project — and gets credited to whatever project
// the session was mainly working on. Measured on one real month: 33 commit
// commands counted, 4 real commits, the other 29 made by test fixtures in
// /tmp. It can't be filtered (there's no path to test) and nothing in the
// report reads it, so it isn't collected. Commits are counted where they can
// be checked: against git, in `commitsWithOurWork`.
//
// `gh pr create` survives because a PR needs a real remote, so it can't be
// faked in a scratch repo — verified 3/3 real on the same corpus.
const CMD_GH_PR_CREATE = new RegExp(CMD_START + String.raw`gh\s+pr\s+create(?=\s|$)`, 'm');

// Heredoc bodies are DATA, not commands — and `^` under the `m` flag can't
// tell the difference. Writing a deploy script, a CI workflow or a test
// fixture that contains the words `git commit` is routine, and every such line
// counted as a commit the dev made: on one real repo this reported 33 commit
// commands against 2 actual commits, because the session had been writing
// fixtures about git. Blank the bodies before matching.
function stripHeredocs(cmd) {
  if (!cmd.includes('<<')) return cmd;
  return cmd.replace(
    /<<-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1[\s\S]*?^\s*\2\s*$/gm,
    '<<HEREDOC'
  );
}
function runsCommand(re, cmd) {
  return re.test(stripHeredocs(cmd));
}

// Relative weights between token types, derived from the ratios between
// published per-token rates (output ~5x input; cache writes ~1.25x, or 2x at
// the 1-hour TTL; cache reads ~0.1x). RATIOS only — never converted to a
// dollar figure, which would imply a precision, and a real bill, we can't back.
// The 1h/5m distinction matters: on a real corpus the two are near an even
// split, so reading only the flattened cache total underprices half the writes
// by 60%.
//
// These feed exactly one number: each project's share of spend
// (`byRepo[].pctSpend`). Nothing else reads them.
//
// One caveat the table can't fix: the ratios hold WITHIN a model, but the
// script doesn't read `message.model`, so a cheap model's token and an
// expensive one's weigh the same. Mixing models moves a project's share by a
// few points. Correcting it would mean shipping a per-model price table in a
// public plugin, which goes stale silently and is the same false precision the
// no-dollar-figures rule exists to avoid. A share is a shape, not a bill.
const RELATIVE_TOKEN_WEIGHTS = {
  input: 1,
  output: 5,
  cacheCreation: 1.25, // 5-minute TTL
  cacheCreation1h: 2,
  cacheRead: 0.1,
};

// Weight one response's usage. Prefers the itemized cache_creation breakdown
// when present and falls back to the flattened total.
function weighUsage(u) {
  const w = RELATIVE_TOKEN_WEIGHTS;
  const cc = u.cache_creation || null;
  const c1h = cc ? cc.ephemeral_1h_input_tokens || 0 : 0;
  const c5m = cc
    ? cc.ephemeral_5m_input_tokens || 0
    : u.cache_creation_input_tokens || 0;
  return (
    (u.input_tokens || 0) * w.input +
    (u.output_tokens || 0) * w.output +
    c5m * w.cacheCreation +
    c1h * w.cacheCreation1h +
    (u.cache_read_input_tokens || 0) * w.cacheRead
  );
}

function freshAgg() {
  return {
    sessions: new Set(),
    prompts: new Set(),
    activeDays: new Set(),
    filesTouched: new Set(),
    linesTouched: 0,
    prCreateCmds: 0,
    costWeight: 0, // relative compute weight (unitless, see RELATIVE_TOKEN_WEIGHTS) — used for byRepo pctSpend
  };
}

const overall = freshAgg();
overall.firstSeen = null;
overall.lastSeen = null;

const byRepo = {}; // projectName -> { ...freshAgg(), cwd: Set }

// --- Project resolution -----------------------------------------------------
//
// A "project" is where work landed, not where the shell happened to be sitting.
// Everything the report counts maps to one: a git repository, or the directory
// a file lives in when it's outside a repo. Work outside a repo is still work —
// it just gets named for its directory rather than dropped.
//
// Claude Code's own machinery is not work. The agent's scratchpad, its
// per-session tool-results, and ~/.claude internals are the tool's bookkeeping;
// counting them credits the dev with files Claude wrote to talk to itself.
const HOME = os.homedir();

// Work that isn't in a project and isn't pretending to be. Sessions that
// searched the web, read Slack, or queried a dashboard without touching a file
// land here. For a lot of people this is the biggest row in the report, and
// that is a true and useful thing to learn about your own usage.
const NO_PROJECT = 'Research & investigation (no project)';

// Every path comparison in this file goes through here first.
//
// Windows mixes separators — transcripts carry `C:\Users\...` while
// `git rev-parse --show-toplevel` answers `C:/Users/...` — and its filesystem
// is case-insensitive. Comparing raw strings means every check below silently
// returns false there, which does not fail loudly: it means Claude's own
// scratchpad stops being excluded and starts counting as the dev's work, and
// `tool-results` shows up as their biggest project. A receipt that credits the
// agent's temp files and drops the real commits is worse than no receipt.
const WIN = process.platform === 'win32';
// Separator normalization only — safe to hand back to git or print.
function fwd(p) {
  return String(p).replace(/\\/g, '/');
}
// Separator + case folding: for COMPARING paths, never for constructing them.
// Lowercasing a path and then passing it to git would break a case-sensitive
// checkout on a case-insensitive filesystem.
function norm(p) {
  const s = fwd(p);
  return WIN ? s.toLowerCase() : s;
}
const HOME_N = norm(HOME);

function isAgentMachinery(p) {
  if (!p) return false;
  const n = norm(p);
  return (
    // Agent scratchpad, under whichever temp root the platform uses:
    // /tmp/claude-501/..., /private/tmp/claude-501/..., and on Windows
    // C:/Users/me/AppData/Local/Temp/claude-501/...
    /\/(?:private\/)?tmp\/claude-[^/]*\//.test(n) ||
    /\/temp\/claude-[^/]*\//.test(n) ||
    /\/var\/folders\/.*\/t\//i.test(n) || // macOS per-user temp
    n.includes('/tool-results/') || // per-session tool output
    // Trailing separator matters: without it this also swallows `~/.claude-foo`
    // and `~/.claude.json`, which are somebody's actual projects and config.
    n.startsWith(HOME_N + '/.claude/') || // memory, projects, config
    // This report's own output. Left in, every run counts the last run's
    // receipt as work and the dev's home directory grows a project made
    // entirely of receipts about itself.
    /\/claude-code-receipts-\d{4}-\d{2}-\d{2}-to-\d{4}-\d{2}-\d{2}\.(md|html)$/.test(n)
  );
}

// git rev-parse is a subprocess; the corpus asks about the same handful of
// directories tens of thousands of times, so memoize per directory.
const _toplevelCache = new Map();
function gitToplevel(dir) {
  if (!dir) return null;
  if (_toplevelCache.has(dir)) return _toplevelCache.get(dir);
  let top = null;
  try {
    top = execFileSync('git', ['-C', dir, 'rev-parse', '--show-toplevel'], {
      encoding: 'utf8',
      timeout: 3000,
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim() || null;
  } catch {
    top = null;
  }
  // A home directory under version control — the `git init ~` dotfiles habit —
  // is not a project, and treating it as one is catastrophic: every directory
  // beneath it stops resolving to itself and collapses into a single row named
  // after the user's account. The whole point of resolving projects is undone.
  // Same for a repo rooted at the filesystem root. Fall back to naming the
  // directory.
  //
  // Compared through realpath, not as raw strings: `git rev-parse` resolves
  // symlinks and `os.homedir()` doesn't, so on an automounted or migrated
  // account (`/home/me` -> `/private/.../home/me`) a string compare misses and
  // the collapse happens anyway.
  if (top && (samePath(top, HOME) || top === path.parse(top).root)) top = null;
  _toplevelCache.set(dir, top);
  return top;
}

// True if two paths name the same directory, allowing for symlinks, separator
// style and Windows case-insensitivity.
function samePath(a, b) {
  if (norm(a) === norm(b)) return true;
  try {
    return norm(fs.realpathSync(a)) === norm(fs.realpathSync(b));
  } catch {
    return false;
  }
}

// A project name is the one piece of the dev's environment the report repeats
// verbatim, so it gets bounded before it goes anywhere.
//
// Length: a directory name can be arbitrarily long and this lands in a 440px
// receipt and in a prompt.
//
// Control characters: newlines and ANSI escapes in a name can restructure the
// JSON the model reads, or the terminal it's printed in.
//
// It is NOT sanitized for meaning, and it can't be — a project genuinely named
// "ignore previous instructions" is a valid directory name. Names are data,
// never instructions; SKILL.md says so where the model reads them.
function cleanProjectName(s) {
  // The control-character class is written as escapes, never as literal
  // bytes: a raw NUL or ESC pasted into source is invisible to the next
  // reader and gets mangled by anything that rewrites the file.
  const flat = String(s).replace(/[\u0000-\u001f\u007f-\u009f]+/g, ' ').trim();
  return flat.length > 64 ? flat.slice(0, 61) + '\u2026' : flat || '(unnamed)';
}

// Resolve a path to { key, dir } — the project it belongs to.
//
// A git repo is keyed by its root's name: `~/code/widget` -> `widget`.
//
// Work outside a repo is named for its directory, because it's still work and
// dropping it would be worse than naming it. Under the home directory that's a
// `~/`-relative path (`~/Downloads`, `~/notes/tax-2026`). Outside it, the last
// two segments only (`/Volumes/AcmeCorp-NDA/merger-diligence` ->
// `AcmeCorp-NDA/merger-diligence`), because a full absolute path is a map of
// the dev's filesystem and the report doesn't need one.
//
// Be clear-eyed about what this does and doesn't do: it bounds the shape, it
// does not anonymize. A directory name can itself be the sensitive thing, and
// the last two segments of a client path still carry the client. That's why
// Step 5 of SKILL.md reads the project names back to the user before the
// report travels, and why `--repo` exists.
const _projectCache = new Map();
function projectForDir(dir) {
  if (!dir || isAgentMachinery(dir + '/')) return null;
  if (_projectCache.has(dir)) return _projectCache.get(dir);
  const top = gitToplevel(dir);
  let key;
  if (top) {
    key = path.basename(top);
  } else {
    // Compare through norm(), like every other path test here. A raw compare
    // fails on Windows — `C:\Users\me\Downloads` never starts with
    // `C:\Users\me` + `/` — and the failure isn't benign: the `~/` branch is
    // what keeps the account name out of the row, so missing it prints
    // `me/Downloads` instead of `~/Downloads`. (norm folds separators and
    // case; symlinked homes are handled by samePath() in gitToplevel.)
    const dirN = norm(dir);
    if (dirN === HOME_N) key = '~';
    else if (dirN.startsWith(HOME_N + '/')) key = '~' + fwd(dir).slice(HOME.length);
    else key = path.posix.join(path.basename(path.dirname(dir)), path.basename(dir));
  }
  const out = { key: cleanProjectName(key), dir };
  if (top) out.dir = top;
  _projectCache.set(dir, out);
  return out;
}
function projectForPath(p) {
  if (!p || isAgentMachinery(p)) return null;
  return projectForDir(path.dirname(p));
}

function repoBucket(key, dir) {
  if (!byRepo[key]) byRepo[key] = { ...freshAgg(), cwd: new Set() };
  if (dir) byRepo[key].cwd.add(dir);
  return byRepo[key];
}

const files = findJsonlFiles(projectsDir);
let filesScanned = 0;
let linesScanned = 0;

// A resumed session re-serializes its earlier entries into the new transcript,
// so the same entry can appear in more than one file. Dedupe globally by uuid
// or everything it carries (tool calls, files, lines, cost) counts twice.
const seenUuids = new Set();

// Merge two usage records from the same API response, field by field. Entries
// of one response usually repeat the identical usage, but ~13% disagree on
// output_tokens as the response streams — max picks the final total, and never
// invents a combination that didn't occur.
function maxUsage(a, b) {
  if (!a) return b;
  const out = { ...a };
  for (const k of Object.keys(b)) {
    if (typeof b[k] === 'number') out[k] = Math.max(a[k] || 0, b[k]);
    // `cache_creation` is a nested object of per-TTL counts. Without this it
    // would silently keep whichever entry arrived first.
    else if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k])) {
      out[k] = maxUsage(a[k], b[k]);
    }
  }
  return out;
}

// Tools whose file_path is a read, not a write. These don't produce output,
// but they say which project the session was working in — and reading is most
// of what the work is.
const FILE_READ_TOOLS = new Set(['Read', 'NotebookRead']);

// --- Per-session collection -------------------------------------------------
//
// Everything is gathered per SESSION first, then attributed to projects once
// the session's full picture is known. Subagents share their parent's
// sessionId, so they land here automatically — a subagent's work ladders into
// whatever its parent was doing, with no special case.
const sessions = new Map();
function session(sid) {
  let S = sessions.get(sid);
  if (!S) {
    S = {
      days: new Set(),
      prompts: new Set(),
      cwds: new Set(),
      votes: new Map(), // projectKey -> touches, decides where this session's spend went
      dirs: new Map(), // projectKey -> resolved dir
      writes: [], // { path, lines, project }
      costWeight: 0,
      prCreateCmds: 0,
      vote(p) {
        const proj = projectForPath(p);
        if (!proj) return null; // agent machinery — not work
        this.votes.set(proj.key, (this.votes.get(proj.key) || 0) + 1);
        this.dirs.set(proj.key, proj.dir);
        return proj;
      },
      write(p, n) {
        if (!p || !n) return;
        const proj = this.vote(p);
        if (!proj) return;
        this.writes.push({ path: p, lines: n, project: proj.key });
      },
    };
    sessions.set(sid, S);
  }
  return S;
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
  // tool calls have more entries), which would skew every project's share.
  const responses = new Map(); // requestId -> { usage, blocks, sid }

  const lines = content.split('\n');

  // Pre-pass: which tool calls came back an error? A tool_result arrives after
  // the tool_use it answers, so this can't be decided inline. An edit that was
  // rejected or denied touched nothing and must not count as work.
  const failedToolIds = new Set();
  for (const line of lines) {
    if (!line.trim() || !line.includes('is_error')) continue;
    let o;
    try {
      o = JSON.parse(line);
    } catch {
      continue;
    }
    const c = o && o.message && o.message.content;
    if (!Array.isArray(c)) continue;
    for (const b of c) {
      if (b && b.type === 'tool_result' && b.is_error && b.tool_use_id) {
        failedToolIds.add(b.tool_use_id);
      }
    }
  }

  for (const line of lines) {
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

    // Key active days by LOCAL calendar date. `git log --date=short` reports
    // author-local dates, so slicing the UTC timestamp would put an evening
    // session on the next day and stop it matching its own commits.
    const date = localDay(ts);
    const sid = obj.sessionId || `file:${file}`;
    const S = session(sid);
    if (cwd) S.cwds.add(cwd);
    S.days.add(date);

    // Count real user turns. Tool-result echoes back to the model aren't
    // prompts, and neither are interrupt markers or compaction summaries —
    // those are transcript bookkeeping, not someone asking for something.
    // A scheduled or queued invocation IS a prompt: the dev set it up, and
    // its usage is theirs.
    if (
      obj.type === 'user' &&
      obj.message &&
      obj.promptId &&
      !obj.isSidechain &&
      !obj.isCompactSummary
    ) {
      const c = obj.message.content;
      const isToolResultOnly =
        Array.isArray(c) && c.length > 0 && c.every((b) => b && b.type === 'tool_result');
      const isInterrupt = typeof c === 'string' && /^\[Request interrupted/.test(c);
      if (!isToolResultOnly && !isInterrupt) S.prompts.add(obj.promptId);
    }

    if (obj.type === 'assistant' && obj.message) {
      const blocks = Array.isArray(obj.message.content) ? obj.message.content : [];

      // Accumulate this entry into its API response. The cost is charged once
      // per response, after the file is read — see the `responses` loop below.
      const rid = obj.requestId || (obj.message && obj.message.id) || obj.uuid;
      if (rid) {
        const r = responses.get(rid) || { usage: null, blocks: [], sid };
        if (obj.message.usage) r.usage = maxUsage(r.usage, obj.message.usage);
        for (const b of blocks) if (b && b.type === 'tool_use') r.blocks.push(b);
        responses.set(rid, r);
      }

      for (const b of blocks) {
        if (!b || b.type !== 'tool_use') continue;
        const name = b.name || 'Unknown';
        const input = b.input || {};
        // A tool_use block is an ATTEMPT. If its result came back an error —
        // a rejected edit, a denied write, a stale read — nothing was touched,
        // and counting it credits work that never happened.
        if (b.id && failedToolIds.has(b.id)) continue;

        // Every file path this session touched, read or write, votes on which
        // project the session's spend belongs to. Reading a repo to answer a
        // question is work in that repo.
        const readPath = FILE_READ_TOOLS.has(name) ? input.file_path || input.notebook_path : null;
        if (readPath) S.vote(readPath);

        // NotebookEdit carries `notebook_path`, not `file_path` — reading only
        // file_path counted a notebook's lines while never counting the
        // notebook itself.
        const p = input.file_path || input.notebook_path;
        if (name === 'Edit' || name === 'NotebookEdit') {
          const n = Math.max(
            countLines(input.old_string ?? input.old_source),
            countLines(input.new_string ?? input.new_source)
          );
          S.write(p, n);
        } else if (name === 'MultiEdit') {
          let n = 0;
          for (const e of input.edits || []) {
            n += Math.max(countLines(e.old_string), countLines(e.new_string));
          }
          S.write(p, n);
        } else if (name === 'Write') {
          S.write(p, countLines(input.content));
        } else if (name === 'Bash') {
          const cmd = input.command || '';
          if (runsCommand(CMD_GH_PR_CREATE, cmd)) S.prCreateCmds++;
        }
      }
    }
  }

  // Charge each API response's relative cost once, onto its session. Where it
  // goes from there is decided later, by which projects the session touched —
  // never by which tool happened to fire on this turn.
  for (const r of responses.values()) {
    if (!r.usage) continue;
    session(r.sid).costWeight += weighUsage(r.usage);
  }
}

// --- Attribute each session's work to the projects it touched ---------------
//
// A session's spend goes where its work went, split across projects in
// proportion to how much it touched each. The shell's cwd is a fallback, not
// evidence: a session run from the home directory that spent an hour editing
// one repo belongs to that repo, not to "home".
// `--repo <substr>` scopes the whole report to matching projects. It filters
// on the resolved project, not the session's cwd: the point is to leave other
// projects' names out of a report someone is about to send onward, and a cwd
// match would still let a session running from elsewhere drag them in.
const matchesFilter = (key) =>
  !args.repo || key.toLowerCase().includes(args.repo.toLowerCase());

for (const S of sessions.values()) {
  // Files land in their own project, wherever the session was sitting.
  for (const wr of S.writes) {
    if (!matchesFilter(wr.project)) continue;
    const r = repoBucket(wr.project, S.dirs.get(wr.project));
    r.filesTouched.add(wr.path);
    r.linesTouched += wr.lines;
    overall.filesTouched.add(wr.path);
    overall.linesTouched += wr.lines;
  }

  let allVotes = [...S.votes.entries()];

  // A session that touched no files still did work — it searched the web, read
  // Slack, queried a dashboard. Where does that belong?
  //
  // If it ran inside a repo, the cwd is real evidence: the dev was sitting in
  // that project, investigating it. Attribute it there.
  //
  // Otherwise there is no project, and saying so is more honest than inventing
  // one. Bucketing it under the home directory would dress "unknown" up as a
  // project name and make the dev's shell location the biggest row in a report
  // about their work. Research is a real category of work; it just doesn't
  // live anywhere on disk.
  //
  // Work out where the session belongs BEFORE applying --repo. Deciding the
  // home first and filtering second is what keeps the filter honest: filtering
  // first lets a session whose real project was excluded fall through to some
  // other bucket, which is how `--repo project` ended up *growing* the research
  // row — "Research & investigation (no project)" contains the substring, so
  // sessions belonging to filtered-out repos were relabelled as research. A
  // filter must only ever remove.
  if (!allVotes.length) {
    // Dedupe by project key: several cwds can resolve to one repo, and an
    // undeduped list would hand that repo the session's whole-number counts
    // once per cwd.
    const seenKeys = new Set();
    for (const cwd of S.cwds) {
      const proj = projectForDir(cwd);
      if (!proj || !gitToplevel(cwd) || seenKeys.has(proj.key)) continue;
      seenKeys.add(proj.key);
      allVotes.push([proj.key, 1]);
      S.dirs.set(proj.key, proj.dir);
    }
    // Only genuinely project-less work becomes research. A session that HAS a
    // project which --repo excluded is out of scope, not research.
    if (!allVotes.length) allVotes = [[NO_PROJECT, 1]];
  }

  // The session's home, decided on the full picture.
  const mainProject = allVotes.reduce((a, b) => (b[1] > a[1] ? b : a))[0];

  const votes = allVotes.filter(([k]) => matchesFilter(k));
  if (!votes.length) continue; // nothing of this session is in scope

  const totalVotes = votes.reduce((a, [, n]) => a + n, 0);

  for (const [key, n] of votes) {
    const frac = n / totalVotes;
    const r = repoBucket(key, S.dirs.get(key));
    r.costWeight += S.costWeight * frac;
    // Counts of things that happened once go to the session's main project
    // whole — splitting an integer proportionally and rounding each share
    // breaks the column (one command across two projects rounds to 1+1=2,
    // across three to 0+0+0). And they go there only if that really is the
    // main project: crediting them to whichever row survived the filter would
    // move another project's commits onto this one.
    if (key === mainProject) {
      r.prCreateCmds += S.prCreateCmds;
    }
    // Days and sessions are memberships, not quantities — a session that spans
    // two projects was genuinely in both, so both rows show it. These columns
    // therefore don't sum to the report totals, and the report says so.
    for (const d of S.days) r.activeDays.add(d);
    r.sessions.add(S);
    for (const p of S.prompts) r.prompts.add(p);
  }

  for (const d of S.days) overall.activeDays.add(d);
  overall.sessions.add(S);
  for (const p of S.prompts) overall.prompts.add(p);
  overall.prCreateCmds += S.prCreateCmds;
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

// Commits in this repo that contain work Claude Code did.
//
// NOT "commits by my git identity" — that asks a different question and gets a
// different answer. It counts anything committed under the dev's email,
// including a snapshot cron, a release bot, or a formatter running on their
// behalf; and it silently misses nothing they did by hand. What this report
// cares about is whether the work CC produced actually landed. So: intersect
// each commit's changed files with the files CC touched. A commit qualifies if
// it carries at least one of them.
//
// That join is bot-proof by construction (a cron's files were never touched by
// CC) and it still catches the commit the dev made by hand in their terminal
// after CC wrote the code — which is the case an identity match gets right by
// accident and a "commits CC itself ran" match misses entirely.
// Returns an array of commits, or GIT_UNAVAILABLE when git couldn't answer —
// which is NOT the same as "no commits" and must not be rendered as one.
const GIT_UNAVAILABLE = Symbol('git-unavailable');

function gitCommitsWithOurWork(dir, ourFiles) {
  if (!ourFiles.size) return null;
  const top = gitToplevel(dir);
  if (!top) return null;
  // Resolved per repo, so an includeIf work identity is picked up where it
  // applies rather than being missed by a single global lookup.
  const ourEmail = gitUserEmailFor(top);
  if (!ourEmail) return null;
  // Ask git only about the files CC touched, via a pathspec, and let git do the
  // intersection against its own index. `:(literal)` disables globbing —
  // without it a real filename containing `?` or `*` becomes a wildcard and
  // matches siblings CC never touched, inventing work out of punctuation.
  //
  // Both sides go through norm() before comparing. `git rev-parse` answers with
  // forward slashes even on Windows, where the transcript paths use
  // backslashes — a raw compare matches nothing there, `rel` comes back empty,
  // and every project silently reports no commits. And the pathspec itself must
  // use forward slashes: git treats `\` inside `:(literal)` as a literal
  // character, so a backslash path matches no file and exits 0 — a wrong answer
  // with no error to notice.
  const topN = norm(top);
  const rel = [];
  for (const f of ourFiles) {
    const slashed = fwd(f); // original case — this is handed to git
    if (!norm(slashed).startsWith(topN + '/')) continue;
    rel.push(':(literal)' + slashed.slice(topN.length + 1));
  }
  if (!rel.length) return null;

  // A repo with no commits yet makes `git log` exit non-zero. That's an empty
  // history, not a broken one — it means zero commits, and reporting it as
  // "couldn't read git" would be its own small lie.
  try {
    execFileSync('git', ['-C', top, 'rev-parse', '--verify', '-q', 'HEAD'], {
      timeout: 3000,
      stdio: ['ignore', 'ignore', 'ignore'],
    });
  } catch {
    return [];
  }
  // Paths go on argv, so a big enough set throws E2BIG — which the catch below
  // would otherwise report as "no commits". Chunk it. (`git log` has no
  // --pathspec-from-file; that's an `add`/`commit` flag only.)
  const CHUNK = 400;
  const byShaLocal = new Map();
  for (let i = 0; i < rel.length; i += CHUNK) {
    try {
      // No `--since`. It prunes traversal rather than filtering, and its
      // tolerance is a fixed commit slop, not a date distance — so an in-window
      // commit sitting behind a run of older ones is unreachable at ANY floor.
      // The pathspec already narrows the walk to a handful of files, so walking
      // full history for them is cheap; the date filter happens below.
      const out = execFileSync(
        'git',
        [
          '-C', top, 'log', '--no-merges',
          '--pretty=format:%H %cI %ae', '--', ...rel.slice(i, i + CHUNK),
        ],
        { encoding: 'utf8', timeout: 20000, maxBuffer: 32 * 1024 * 1024, stdio: ['ignore', 'pipe', 'ignore'] }
      );
      for (const line of out.split('\n')) {
        if (!line.trim()) continue;
        const [sha, when, ...emailParts] = line.trim().split(' ');
        // %cI, matching what a window means for a receipt: the commit LANDED in
        // this period. (%aI is when it was first written, which for a rebase or
        // a cherry-pick is a different, older date.)
        const ts = new Date(when);
        if (isNaN(ts) || ts < cutoff || ts > now) continue;
        // BOTH signals are required, and neither is sufficient alone. Identity
        // alone counts a snapshot cron or a release bot running under the dev's
        // email. The pathspec alone counts every unrelated bot commit that
        // happens to touch a file the dev also touched — a bump job editing the
        // same manifest, say. Together: work the dev committed, that CC did.
        //
        // %ae is the AUTHOR, not the committer: if a colleague wrote it and the
        // dev merely applied the patch, it isn't the dev's work.
        if (emailParts.join(' ') !== ourEmail) continue;
        byShaLocal.set(sha, localDay(ts));
      }
    } catch {
      // Git errored — a promisor fetch failure, a timeout, a corrupt object.
      // The honest answer is "couldn't tell", not "none".
      return GIT_UNAVAILABLE;
    }
  }
  return [...byShaLocal].map(([sha, date]) => ({ sha, date }));
}

// The identity git would sign a commit with IN THIS REPO — the same question
// git itself answers, resolved the same way.
//
// Not `--global`: the standard corporate split puts the work identity behind
// `includeIf "gitdir:~/work/"`, which `--global` cannot see, so it comes back
// empty and every commit in the report vanishes for exactly the people most
// likely to need one. Not the repo's raw `--local` either — asked from inside
// the repo, plain `git config` resolves includeIf, local overrides and global
// defaults in git's own precedence order.
//
// A shared or bot identity configured in some repo is not a hazard here: the
// file intersection is the real guard, and a release bot's commits don't touch
// the files Claude Code edited.
const _emailCache = new Map();
function gitUserEmailFor(dir) {
  const key = dir || '';
  if (_emailCache.has(key)) return _emailCache.get(key);
  let email = null;
  try {
    email =
      execFileSync('git', dir ? ['-C', dir, 'config', 'user.email'] : ['config', 'user.email'], {
        encoding: 'utf8',
        timeout: 3000,
        stdio: ['ignore', 'pipe', 'ignore'],
      }).trim() || null;
  } catch {
    email = null;
  }
  _emailCache.set(key, email);
  return email;
}

// Local, not UTC: the date printed on the receipt, and the floor for the git
// walk below.
const sinceDate = localDay(cutoff);
const repoSummaries = {};
const globalCommits = new Map(); // sha -> date, deduped across worktrees
let anyGitData = false;

let anyGitError = false;

for (const [name, agg] of Object.entries(byRepo)) {
  const dir = [...agg.cwd][0];
  // Only ask git about projects that ARE git repos, and only about the files
  // CC actually touched there.
  const raw = dir ? gitCommitsWithOurWork(dir, agg.filesTouched) : null;
  const gitFailed = raw === GIT_UNAVAILABLE;
  if (gitFailed) anyGitError = true;
  const commits = gitFailed ? null : raw;

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
    prCreateCmds: Math.round(agg.prCreateCmds),
    // null, not false, for the research bucket — it isn't a repo, but it isn't
    // a directory either, and `false` makes the renderer footnote it as "work
    // done in a plain directory", which is untrue of the biggest row on the page.
    isRepo: name === NO_PROJECT ? null : !!(dir && gitToplevel(dir)),
    commitsWithOurWork: commits ? commits.length : null,
    // True when git was asked and couldn't answer. Distinct from a null count
    // meaning "not a repo" or "nothing landed" — the renderer must not report
    // a failure as a zero.
    gitUnavailable: gitFailed || undefined,
    gitActiveDayOverlap,
    _costWeight: agg.costWeight, // stripped after pctSpend is computed, below
    _activeDays: agg.activeDays, // stripped after the rollup unions them, below
    _prompts: agg.prompts, // ditto — prompts are a Set and must union, not sum
    _shas: commits ? commits.map((c) => c.sha) : null, // ditto — see the rollup
  };
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
  r.prCreateCmds > 0 ||
  r.commitsWithOurWork ||
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
    prCreateCmds: 0, isRepo: null,
    commitsWithOurWork: null, gitActiveDayOverlap: null, pctSpend: 0,
    projectCount: otherRepos.length,
  };
  // Days, prompts and commits are UNIONS, not sums. One day worked across three
  // of these projects is one active day; one prompt that touched three of them
  // is one prompt. And worktrees of the same checkout each report the same
  // shared ancestor commits, so adding their counts inflates the row — dedupe
  // by SHA, exactly as the report-wide total does.
  const rollupDays = new Set();
  const rollupPrompts = new Set();
  const rollupShas = new Set();
  let anyRollupGit = false;
  for (const [, r] of otherRepos) {
    rollup.sessions += r.sessions;
    rollup.filesTouched += r.filesTouched;
    rollup.linesTouched += r.linesTouched;
    rollup.prCreateCmds += r.prCreateCmds;
    rollup.pctSpend += r.pctSpend;
    for (const d of r._activeDays) rollupDays.add(d);
    for (const p of r._prompts) rollupPrompts.add(p);
    if (r._shas) {
      anyRollupGit = true;
      for (const s of r._shas) rollupShas.add(s);
    }
  }
  rollup.activeDays = rollupDays.size;
  rollup.prompts = rollupPrompts.size;
  rollup.commitsWithOurWork = anyRollupGit ? rollupShas.size : null;
  topRepos['(other repos)'] = rollup;
}

const totalCalendarDays = calendarDaysBetween(cutoff, now);

// Report-wide commit total: de-duplicated by SHA, since worktrees of one
// checkout each report the same shared ancestor commits.
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
    prCreateCmds: Math.round(overall.prCreateCmds),
    // Commits whose changed files include something CC touched — de-duplicated
    // by SHA, since worktrees of one checkout share ancestors.
    commitsWithOurWork: anyGitData ? globalCommits.size : null,
    gitActiveDayOverlap: anyGitData ? gitActiveDayOverlapTotal : null,
    // Why the commit count is null, when it is. These are NOT the same thing
    // and must never be reported as each other: a month spent entirely on
    // research legitimately has no commits, and telling that dev "git couldn't
    // be read" is a specific, checkable, false claim about their machine — on
    // a page whose whole argument is that its numbers are careful.
    //   false -> no project produced commits (research, non-repo work, or a
    //            new checkout). An honest zero.
    //   true  -> at least one project's git actually errored. Unknown.
    gitUnavailable: anyGitError || undefined,
    // firstSeen/lastSeen are deliberately not emitted: nothing in the report
    // uses them, and the exact instant of a dev's first and last turn is a
    // working-hours signal that has no business in a spend receipt.
    //
    // Nor is any activity/category breakdown — see the note above
    // RELATIVE_TOKEN_WEIGHTS for why per-tool spend attribution isn't a
    // measurement. Spend appears once, per project, as byRepo[].pctSpend.
  },
  byRepo: topRepos,
};

// Strip the internal working fields. These are read by the "(other repos)"
// rollup above — which unions them rather than summing — so they have to
// survive until now, but they must not reach the output.
for (const r of Object.values(topRepos)) {
  delete r._activeDays;
  delete r._prompts;
  delete r._shas;
}

process.stdout.write(JSON.stringify(summary, null, 2));

// --- Optional HTML "receipt" ---
if (args.html) {
  try {
    // Mode 0600, and refuse to follow a symlink. The receipt names the dev's
    // projects, and the obvious place to put it is a predictable path in a
    // world-writable /tmp: on a shared box — a dev server, a CI runner —
    // anyone can pre-create that name as a link to a file they want the
    // victim to overwrite, or simply read the receipt afterwards. `wx` fails
    // rather than following an existing link; the unlink-and-retry keeps
    // re-runs working for a file we really did write.
    const write = () =>
      fs.writeFileSync(args.html, renderHTML(summary), { mode: 0o600, flag: 'wx' });
    try {
      write();
    } catch (e) {
      if (e.code !== 'EEXIST') throw e;
      const st = fs.lstatSync(args.html);
      if (st.isSymbolicLink()) {
        throw new Error(`${args.html} is a symlink; refusing to write through it`);
      }
      fs.unlinkSync(args.html);
      write();
    }
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
  if (n == null || !Number.isFinite(Number(n))) return '–';
  return Number(n).toLocaleString('en-US');
}

function fmtPct(pct) {
  if (pct <= 0) return '–';
  if (pct < 1) return '&lt;1%'; // escaped: this is interpolated straight into HTML
  return `${Math.round(pct)}%`;
}

// --- CSV export -------------------------------------------------------------

// One CSV cell.
//
// Two separate jobs. The RFC-4180 part — quote anything containing a comma,
// quote or newline, and double the quotes — is ordinary. The leading-character
// check is the important one: a cell starting `=`, `+`, `-` or `@` is a FORMULA
// to Excel, Sheets and LibreOffice. Project names come from directory names, so
// a folder called `=cmd|'/c calc'!A1` becomes executable the moment someone
// opens the export — and this file is built to be handed to someone else.
// Prefixing with an apostrophe makes the spreadsheet read it as text.
function csvCell(v) {
  let s = v === null || v === undefined ? '' : String(v);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
  if (/[",\n\r]/.test(s)) s = '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function buildCsv(s) {
  const rows = [
    ['Project', 'Sessions', 'Active days', 'Files touched', 'Lines touched', 'Commits', 'Spend %'],
  ];
  for (const [name, r] of Object.entries(s.byRepo)) {
    rows.push([
      name,
      r.sessions,
      r.activeDays,
      r.filesTouched,
      r.linesTouched,
      // Preserve the same three-way distinction the table makes: a number, a
      // known absence, or genuinely unknown. Blanks in a spreadsheet read as
      // zero, and "git failed" is not zero.
      r.gitUnavailable ? 'unknown' : r.commitsWithOurWork === null ? 'n/a' : r.commitsWithOurWork,
      r.pctSpend.toFixed(1),
    ]);
  }
  // The HTML footnotes travel with the table; a CSV arrives naked, in a tool
  // whose first instinct is =SUM() on a column. Sessions and Active days
  // deliberately don't sum — a session spanning two projects is counted in
  // both — so a recipient summing them overstates and never finds out. Carry
  // the caveat into the file rather than leaving it behind in the page.
  rows.push([]);
  rows.push([
    'Note: Sessions and Active days count a project each time work touched it, so a session' +
      ' spanning two projects appears in both rows — these columns do NOT sum to your totals.' +
      ' Neither does Commits: worktrees of one repo share history, so a commit can appear in' +
      ' more than one row, and the report total de-duplicates by commit. Files and lines belong' +
      ' to one project each and do sum. Spend % sums to 100 before rounding.' +
      ' "n/a" = not a git repo or nothing landed; "unknown" = git could not be read.',
  ]);
  return rows.map((r) => r.map(csvCell).join(',')).join('\r\n');
}

// Embed a string in a <script> safely: `</script>` inside a JS string literal
// still closes the tag, because the HTML parser doesn't know it's in a string.
// U+2028/U+2029 too — JSON.stringify leaves them raw, and they were illegal in
// JS string literals before ES2019. Harmless in a current browser, free to fix,
// and a receipt can outlive the engine that opens it.
function jsonForScript(v) {
  return JSON.stringify(v)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

function renderHTML(s) {
  const t = s.totals;

  const repoEntries = Object.entries(s.byRepo);
  let anyNotRepo = false;
  let anyGitUnavailable = false;
  const repoRows = repoEntries
    .map(([name, r]) => {
      let commits;
      if (r.gitUnavailable) {
        commits = '?';
        anyGitUnavailable = true;
      } else {
        commits = r.commitsWithOurWork != null ? fmt(r.commitsWithOurWork) : '–';
      }
      if (r.isRepo === false) anyNotRepo = true;
      return `
      <tr>
        <td>${escapeHtml(name)}${r.isRepo === false ? '*' : ''}</td>
        <td class="num">${fmt(r.sessions)}</td>
        <td class="num">${fmt(r.activeDays)}</td>
        <td class="num">${fmt(r.filesTouched)}</td>
        <td class="num">${fmt(r.linesTouched)}</td>
        <td class="num">${commits}</td>
        <td class="num">${fmtPct(r.pctSpend)}</td>
      </tr>`;
    })
    .join('');
  const repoFootnotes = [
    'Sessions and active days count a project each time work touched it, so a session spanning two projects appears in both rows. Commits can repeat too: worktrees of one repo share history, and the total above de-duplicates by commit. None of those three columns sum to the totals. Files and lines belong to one project each and do.',
    anyNotRepo && '* not a git repository — work done in a plain directory, named for it.',
    '– no commits containing this project’s Claude Code work, or not a git repository.',
    anyGitUnavailable && '? git couldn’t be read for this project, so its commits are unknown — not zero.',
  ].filter(Boolean).map(t => `<div class="note">${escapeHtml(t)}</div>`).join('');


  // The hero number. It is computed here, in code, from figures that are
  // already scoped to work Claude Code did — commits carrying CC's own changes,
  // PRs CC opened. It must never be assembled from a raw identity-wide count:
  // this box is the largest type on a page designed to be handed to someone,
  // and it is generated before any model sees the data, so no instruction
  // written for the model can protect it. Whatever guards this number has to
  // live right here.
  //
  // `commitsWithOurWork` is null in two unrelated cases, and `null || 0` would
  // flatten both to "you shipped 0" in the largest type on the page. Keep them
  // apart: git ERRORING means unknown (say so), while a month with no commits
  // is an honest zero and must not be dressed up as a tool failure — telling a
  // researcher their git is broken when it isn't is exactly the kind of
  // checkable false claim this report can't afford.
  // FOUR states. A null commit count has more than one cause and only one of
  // them is a failure; collapsing them is how this line has now been wrong
  // twice, in both directions.
  //
  //   commits known, git fine      -> the plain sum
  //   commits known, git broke too -> the sum is a floor, say so
  //   commits null, git broke      -> PRs only; commits UNKNOWN, not zero
  //   commits null, git fine       -> PRs only; there was simply nothing to
  //                                   check — no repos in the window, or no
  //                                   git identity configured. NOT a failure.
  //                                   Telling a dev whose month was research
  //                                   in plain directories that their git is
  //                                   broken is a false claim about their
  //                                   machine, which is the whole thing this
  //                                   report can't afford to do.
  const commitsKnown = t.commitsWithOurWork != null;
  const gitBroke = !!t.gitUnavailable;
  const shipped = commitsKnown
    ? (t.commitsWithOurWork || 0) + (t.prCreateCmds || 0)
    : t.prCreateCmds || 0;
  const shippedLabel = commitsKnown ? 'Commits + PRs shipped' : 'PRs shipped';
  const shippedNote = !commitsKnown
    ? gitBroke
      ? 'Git couldn’t be read, so commits carrying this work are unknown — not zero.'
      : 'No git repositories to check this window, so there are no commits to count.'
    : gitBroke
      ? 'At least this many: git couldn’t be read for some projects, so any commits there are missing from this count.'
      : null;
  const overlapNote =
    t.gitActiveDayOverlap != null
      ? `${fmt(t.gitActiveDayOverlap)} of your ${fmt(t.activeDays)} active days ended with work Claude Code did being committed.`
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
  /* The shadow lives on the wrapper, not the receipt: a mask clips box-shadow
     along with everything else, so the torn edge would cut its own shadow off.
     drop-shadow on a parent traces the masked silhouette instead. */
  .receipt-wrap {
    width: 100%; max-width: 440px;
    filter: drop-shadow(0 10px 22px rgba(0,0,0,0.20));
  }
  .receipt {
    --tooth: 13px;  /* width of one perforation triangle */
    --notch: 7px;   /* how deep it bites into the paper */
    background: var(--paper);
    width: 100%;
    /* Pad by the notch depth so the teeth chew into margin, not into text. */
    padding: calc(1.5rem + var(--notch)) 1.75rem calc(1.25rem + var(--notch));
    /* Torn-off top and bottom edges. Two tiled conic gradients cut the
       triangles; the linear gradient keeps everything between them opaque. */
    --torn:
      conic-gradient(from 135deg at top, #0000, #000 1deg 89deg, #0000 90deg)
        top / var(--tooth) var(--notch) repeat-x,
      conic-gradient(from -45deg at bottom, #0000, #000 1deg 89deg, #0000 90deg)
        bottom / var(--tooth) var(--notch) repeat-x,
      linear-gradient(#000 0 0)
        center / 100% calc(100% - 2 * var(--notch)) no-repeat;
    -webkit-mask: var(--torn);
    mask: var(--torn);
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
  table { width:100%; table-layout:fixed; border-collapse:collapse; font-size:0.65rem; }
  th, td { text-align:left; padding:0.3rem 0.2rem; border-bottom:1px dotted var(--line); overflow-wrap:break-word; }
  /* Seven columns in a 440px receipt: budget the widths explicitly rather than
     letting them divide evenly, which leaves each number column too narrow for
     its own heading and breaks "SESSIONS" into "SESSIO / NS". */
  col.c-project { width:26%; }
  col.c-sess    { width:9%;  }
  col.c-days    { width:8%;  }
  col.c-files   { width:11%; }
  /* Lines is the column that actually gets big — a heavy month reaches seven
     digits. Commits almost never passes three, so it lends its width here. */
  col.c-lines   { width:18%; }
  col.c-cmts    { width:14%; }
  col.c-spend   { width:14%; }
  th { font-weight:700; color: var(--muted); text-transform:uppercase; font-size:0.58rem; letter-spacing:0.02em; }
  /* Headings are abbreviated to fit; never let one hyphenate mid-word. */
  th.num { white-space:nowrap; }
  td.num, th.num { text-align:right; }
  /* nowrap keeps "1,234,567" on one line, but with table-layout:fixed a number
     wider than its column paints straight over the neighbouring one instead of
     stopping. A heavy user's million-line month is enough to make the Files and
     Lines columns collide. Clip at the cell edge; the ellipsis says the value
     was cut rather than silently wrong. */
  td.num { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .barcode {
    height: 36px; margin: 1.25rem 0 0.75rem;
    background: repeating-linear-gradient(90deg, var(--ink) 0 2px, transparent 2px 4px, var(--ink) 4px 5px, transparent 5px 9px, var(--ink) 9px 12px, transparent 12px 14px);
    opacity: 0.85;
  }
  .footer { text-align:center; font-size:0.65rem; color:var(--muted); line-height:1.6; }
  .actions { margin-top: 0.9rem; text-align: center; }
  .export {
    font: inherit; font-size: 0.62rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted); background: none; cursor: pointer;
    border: 1px dashed var(--line); border-radius: 2px; padding: 0.4rem 0.9rem;
  }
  .export:hover { color: var(--ink); border-color: var(--muted); }
  .export:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  /* This gets printed and PDF'd — it is a receipt. Two things have to go for
     that to work.

     A drop-shadow filter forces the whole receipt to rasterize in paged
     output: the PDF comes out as a 450KB bitmap with zero embedded fonts, so
     nothing is selectable, searchable, or readable by a screen reader.
     Without it: vector text, a quarter the size.

     The torn edge re-cuts at every page break, so a two-page receipt appears
     to end mid-sentence behind a row of perforations. Print it as plain paper
     and let the page boundary be a page boundary. */
  @media print {
    body { background: #fff; padding: 0; display: block; }
    .receipt-wrap { filter: none; max-width: none; }
    .receipt { -webkit-mask: none; mask: none; padding: 0; }
    tr, .row { break-inside: avoid; }
    .actions { display: none; }
  }
  .note { font-size:0.68rem; color:var(--muted); line-height:1.5; margin-top:0.4rem; }
</style>
</head>
<body>
  <div class="receipt-wrap">
  <div class="receipt">
    <h1>Claude Code</h1>
    <div class="stars">★ ★ ★ ★ ★</div>
    <div class="sub">USAGE RECEIPT${s.userName ? ` — ${escapeHtml(s.userName)}` : ''}</div>
    <div class="sub">${escapeHtml(s.since)} — ${escapeHtml(s.until)} (${fmt(t.activeDays)} of ${fmt(t.calendarDays)} days active)</div>
    <hr>
    <div class="row"><span class="label">Sessions</span><span class="value">${fmt(t.sessions)}</span></div>
    <div class="row"><span class="label">Prompts</span><span class="value">${fmt(t.prompts)}</span></div>
    <div class="row"><span class="label">Files touched</span><span class="value">${fmt(t.filesTouched)}</span></div>
    <div class="row"><span class="label">Lines touched (approx.)</span><span class="value">${fmt(t.linesTouched)}</span></div>
    ${t.commitsWithOurWork != null ? `<div class="row"><span class="label">Commits carrying that work</span><span class="value">${fmt(t.commitsWithOurWork)}</span></div>` : ''}
    ${t.prCreateCmds ? `<div class="row"><span class="label">PRs opened</span><span class="value">${fmt(t.prCreateCmds)}</span></div>` : ''}
    <div class="total"><span>${escapeHtml(shippedLabel)}</span><span class="value">${fmt(shipped)}</span></div>
    <div class="note">${shippedNote ? `${escapeHtml(shippedNote)} ` : 'Commits whose changed files include work Claude Code did, plus PRs it opened. Commits made by anyone else, or by automation running under your name, are not counted. '}${overlapNote ? escapeHtml(overlapNote) : ''}</div>

    <h2>By project</h2>
    <table>
      <colgroup>
        <col class="c-project"><col class="c-sess"><col class="c-days"><col class="c-files">
        <col class="c-lines"><col class="c-cmts"><col class="c-spend">
      </colgroup>
      <thead><tr><th>Project</th><th class="num">Sess</th><th class="num">Days</th><th class="num">Files</th><th class="num">Lines</th><th class="num">Commits</th><th class="num">Spend</th></tr></thead>
      <tbody>${repoRows}</tbody>
    </table>
    ${repoFootnotes}

    <div class="actions">
      <button type="button" class="export" id="export-csv">Export CSV</button>
    </div>

    <div class="barcode"></div>
    <div class="footer">
      Built on this machine from ${fmt(s.filesScanned)} local session files —<br>
      counts and project names only, no code or conversation content.<br>
      ${escapeHtml(s.generatedAt)}
    </div>
  </div>
  </div>
<script>
// The CSV is built by the miner and embedded verbatim — the same numbers the
// page shows, escaped and formula-neutralized once, in one place. Rebuilding it
// here by scraping the DOM would be a second implementation to keep in step.
(function () {
  var csv = ${jsonForScript(buildCsv(s))};
  var name = ${jsonForScript(`claude-code-receipt-${s.since}-to-${s.until}.csv`)};
  var btn = document.getElementById('export-csv');
  if (!btn) return;
  btn.addEventListener('click', function () {
    // A BOM, so Excel reads it as UTF-8 rather than mangling any non-ASCII
    // project name.
    var blob = new Blob(['\\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // Deferred, not immediate: Safari has historically aborted the download
    // when the blob URL is revoked in the same task as the click.
    setTimeout(function () { URL.revokeObjectURL(url); }, 0);
  });
})();
</script>
</body>
</html>`;
}
