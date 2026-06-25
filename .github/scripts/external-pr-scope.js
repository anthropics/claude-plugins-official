'use strict';
// Shared logic for letting a NON-MEMBER pull request stay open and be reviewed, scoped to
// the contributor's own already-listed plugin repo. No maintained allowlist, no individuals.
//
// Trust model: we do NOT verify the submitter's identity. We trust the SOURCE REPO. A PR is
// in scope only if it ADDS marketplace.json entries whose source.url is a repo that ALREADY
// backs a live entry in this marketplace (derived from the base marketplace.json), pinned to
// a commit in that repo. Because the repo is org-controlled and the SHA pins to a real commit
// there, the shipped code is the org's code regardless of who opened the PR. Merge still
// requires CI + a maintainer approval.
//
// Used by:
//   - close-external-prs.yml      (skip the auto-close when in scope)
//   - external-pr-scope-guard.yml (required status check: fail a non-member PR that is out of scope)
//
// Security: evaluate() reads base + head marketplace.json as DATA via the API and parses them;
// it never checks out or executes head code.

const MARKETPLACE = '.claude-plugin/marketplace.json';

function normalizeRepo(u) {
  return String(u || '').trim().toLowerCase()
    .replace(/^git\+/, '')
    .replace(/^https?:\/\//, '')
    .replace(/\.git$/, '')
    .replace(/\/+$/, '');
}

function pluginsByName(json) {
  const map = {};
  for (const p of (json && json.plugins) || []) { if (p && p.name) map[p.name] = p; }
  return map;
}

// Repos that already back a live entry, derived from the base marketplace.json.
function liveReposOf(base) {
  const s = new Set();
  for (const name of Object.keys(base)) {
    const u = base[name] && base[name].source && base[name].source.url;
    if (!u) continue;
    const r = normalizeRepo(u);
    if (r.split('/').length >= 3) s.add(r);   // host/org/repo
  }
  return s;
}

// Pure decision over an already-computed diff. Returns { ok, problems, added, removed, modified }.
function analyze({ changedFiles, base, head }) {
  const problems = [];

  const off = changedFiles.filter(n => n !== MARKETPLACE);
  if (off.length) problems.push(`changes files other than ${MARKETPLACE}: ${off.join(', ')}`);

  const liveRepos = liveReposOf(base);
  const baseNames = new Set(Object.keys(base));
  const headNames = new Set(Object.keys(head));
  const removed = [...baseNames].filter(n => !headNames.has(n));
  const added = [...headNames].filter(n => !baseNames.has(n));
  const modified = [...headNames].filter(
    n => baseNames.has(n) && JSON.stringify(base[n]) !== JSON.stringify(head[n])
  );

  if (removed.length)  problems.push(`removes existing entr${removed.length > 1 ? 'ies' : 'y'}: ${removed.join(', ')}`);
  if (modified.length) problems.push(`modifies existing entr${modified.length > 1 ? 'ies' : 'y'}: ${modified.join(', ')}`);
  if (!off.length && !added.length && !removed.length && !modified.length) {
    problems.push('makes no in-scope change (expected additions to marketplace.json)');
  }

  for (const name of added) {
    const u = head[name] && head[name].source && head[name].source.url;
    if (!u) { problems.push(`added "${name}" has no source.url to validate`); continue; }
    const r = normalizeRepo(u);
    if (r.split('/').length < 3) { problems.push(`added "${name}" source.url ${u} is not a valid repo URL`); continue; }
    if (!liveRepos.has(r)) {
      problems.push(`added "${name}" points at ${u}, a repo with no existing live plugin in this marketplace`);
    }
  }

  return { ok: problems.length === 0, problems, added, removed, modified, liveRepoCount: liveRepos.size };
}

async function readPlugins(github, owner, repo, ref) {
  try {
    const { data } = await github.rest.repos.getContent({ owner, repo, ref, path: MARKETPLACE });
    return pluginsByName(JSON.parse(Buffer.from(data.content, 'base64').toString('utf8')));
  } catch (e) {
    return null;
  }
}

// API wrapper used by both workflows. Fetches the diff + base/head marketplace.json, delegates to analyze().
async function evaluate({ github, context }) {
  const pr = context.payload.pull_request;
  const owner = context.repo.owner, repo = context.repo.repo;

  const files = await github.paginate(github.rest.pulls.listFiles, {
    owner, repo, pull_number: pr.number, per_page: 100,
  });
  const changedFiles = files.map(f => f.filename);

  const base = await readPlugins(github, owner, repo, pr.base.sha);
  const head = await readPlugins(github, pr.head.repo.owner.login, pr.head.repo.name, pr.head.sha);
  if (base === null || head === null) {
    return { ok: false, problems: ['could not read marketplace.json at base and/or head'], added: [], removed: [], modified: [] };
  }

  return analyze({ changedFiles, base, head });
}

module.exports = { normalizeRepo, liveReposOf, analyze, readPlugins, evaluate, MARKETPLACE };
