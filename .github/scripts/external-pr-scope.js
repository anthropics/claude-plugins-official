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
// before = plugins at the MERGE-BASE (what head forked from), after = plugins at HEAD,
// liveRepos = repos already live on the current base branch. Diffing before->after (not
// base-tip->head) isolates THIS PR's changes; a stale fork no longer shows main's later
// additions as phantom removals.
function analyze({ changedFiles, before, after, liveRepos }) {
  const problems = [];

  const off = changedFiles.filter(n => n !== MARKETPLACE);
  if (off.length) problems.push(`changes files other than ${MARKETPLACE}: ${off.join(', ')}`);

  const baseNames = new Set(Object.keys(before));
  const headNames = new Set(Object.keys(after));
  const removed = [...baseNames].filter(n => !headNames.has(n));
  const added = [...headNames].filter(n => !baseNames.has(n));
  const modified = [...headNames].filter(
    n => baseNames.has(n) && JSON.stringify(before[n]) !== JSON.stringify(after[n])
  );

  if (removed.length)  problems.push(`removes existing entr${removed.length > 1 ? 'ies' : 'y'}: ${removed.join(', ')}`);
  if (modified.length) problems.push(`modifies existing entr${modified.length > 1 ? 'ies' : 'y'}: ${modified.join(', ')}`);
  if (!off.length && !added.length && !removed.length && !modified.length) {
    problems.push('makes no in-scope change (expected additions to marketplace.json)');
  }

  for (const name of added) {
    const u = after[name] && after[name].source && after[name].source.url;
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

  // Diff THIS PR's changes (merge-base -> head), not base-tip -> head, so a fork that is
  // behind main doesn't show main's later additions as phantom removals.
  let mergeBaseSha = pr.base.sha;
  try {
    const cmp = await github.rest.repos.compareCommits({ owner, repo, base: pr.base.sha, head: pr.head.sha });
    if (cmp && cmp.data && cmp.data.merge_base_commit && cmp.data.merge_base_commit.sha) {
      mergeBaseSha = cmp.data.merge_base_commit.sha;
    }
  } catch (e) { /* fall back to base.sha */ }

  const liveBase = await readPlugins(github, owner, repo, pr.base.sha);          // current base branch (for "already live")
  const before = await readPlugins(github, owner, repo, mergeBaseSha);            // what head forked from
  const after = await readPlugins(github, pr.head.repo.owner.login, pr.head.repo.name, pr.head.sha);
  if (liveBase === null || before === null || after === null) {
    return { ok: false, problems: ['could not read marketplace.json at base, merge-base, and/or head'], added: [], removed: [], modified: [] };
  }

  return analyze({ changedFiles, before, after, liveRepos: liveReposOf(liveBase) });
}

// Authors that are NOT subject to the external-contributor scope rules:
//   - the repo's own automation bot — its bump PRs legitimately MODIFY existing entries
//     (SHA bumps), which the additions-only external-contributor rule forbids; AND
//   - org members (write/admin).
// Safe under pull_request_target: a fork PR cannot set its author to github-actions[bot]
// (that login is only ever the org's own GITHUB_TOKEN workflow), and the member path is a
// real permission lookup. Wrapped in try/catch because getCollaboratorPermissionLevel throws
// for a non-collaborator/unknown user — without this, both callers would error the job rather
// than fall through to scope evaluation.
const EXEMPT_BOTS = new Set(['github-actions[bot]']);

async function isExemptAuthor({ github, context }) {
  const author = context.payload.pull_request.user.login;
  if (EXEMPT_BOTS.has(author)) {
    return { exempt: true, reason: `${author} is the trusted automation bot` };
  }
  try {
    const { data } = await github.rest.repos.getCollaboratorPermissionLevel({
      owner: context.repo.owner, repo: context.repo.repo, username: author,
    });
    if (['admin', 'write'].includes(data.permission)) {
      return { exempt: true, reason: `${author} is ${data.permission} (member)` };
    }
  } catch (e) {
    // not a collaborator / lookup failed → not exempt; fall through to scope evaluation
  }
  return { exempt: false };
}

module.exports = { normalizeRepo, liveReposOf, analyze, readPlugins, evaluate, isExemptAuthor, MARKETPLACE };
