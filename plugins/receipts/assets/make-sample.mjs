// make-sample.mjs — regenerate assets/sample-receipt.png for the README.
//
// The README's sample must never contain anyone's real projects, so it isn't a
// screenshot of a real run. This builds a throwaway HOME with invented repos,
// invented files and invented sessions, then points the real miner at it — the
// picture is genuinely what the tool produces, from data that never existed.
//
//   node assets/make-sample.mjs ~/receipts-sample
//   HOME=~/receipts-sample/home node skills/receipts/scripts/mine-transcripts.mjs \
//     --days 30 --html /tmp/sample.html
//   # screenshot /tmp/sample.html at 620px wide, crop to the receipt
//
// Build it somewhere with no symlink above it — NOT /tmp, which on macOS is a
// symlink to /private/tmp. `git rev-parse --show-toplevel` resolves symlinks
// and these transcripts don't, so under /tmp every repo reports zero commits
// and the sample comes out silently wrong.
//
// Keep the invented names obviously fake (acme-*, example.com).

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const ROOT = process.argv[2];
const HOME = path.join(ROOT, 'home');
fs.rmSync(ROOT, { recursive: true, force: true });

const NAME = 'Morgan Lunt';
const EMAIL = 'morgan@example.com';

const git = (cwd, ...a) => execFileSync('git', ['-C', cwd, ...a], { stdio: ['ignore', 'pipe', 'ignore'] });

// --- invented projects -------------------------------------------------------
const REPOS = {
  'acme-api': ['src/routes/orders.ts', 'src/routes/refunds.ts', 'src/db/schema.sql', 'src/lib/auth.ts', 'tests/orders.test.ts'],
  'acme-web': ['app/checkout/page.tsx', 'app/cart/state.ts', 'components/PriceTag.tsx'],
  'billing-service': ['internal/invoice/render.go', 'internal/tax/rates.go'],
  'infra-terraform': ['envs/prod/main.tf', 'modules/rds/variables.tf'],
};
const NOTES = ['migration-plan.md', 'oncall-runbook.md'];

fs.mkdirSync(path.join(HOME, 'notes'), { recursive: true });
fs.writeFileSync(path.join(HOME, '.gitconfig'), `[user]\n\tname = ${NAME}\n\temail = ${EMAIL}\n`);
for (const f of NOTES) fs.writeFileSync(path.join(HOME, 'notes', f), 'note\n'.repeat(40));

for (const [repo, files] of Object.entries(REPOS)) {
  const dir = path.join(HOME, 'code', repo);
  fs.mkdirSync(dir, { recursive: true });
  git(dir, 'init', '-q', '-b', 'main');
  git(dir, 'config', 'user.name', NAME);
  git(dir, 'config', 'user.email', EMAIL);
  git(dir, 'config', 'commit.gpgsign', 'false');
  for (const f of files) {
    fs.mkdirSync(path.dirname(path.join(dir, f)), { recursive: true });
    fs.writeFileSync(path.join(dir, f), 'x\n'.repeat(60));
  }
  git(dir, 'add', '-A');
  git(dir, 'commit', '-qm', 'initial');
}

// --- invented transcripts ----------------------------------------------------
const PROJ = path.join(HOME, '.claude', 'projects', 'sample');
fs.mkdirSync(PROJ, { recursive: true });

let uid = 0;
const U = () => `u${++uid}`;
const day = (back) => {
  const d = new Date();
  d.setDate(d.getDate() - back);
  d.setHours(10 + (back % 6), 15, 0, 0);
  return d.toISOString();
};
const usage = (out) => ({
  input_tokens: 900,
  output_tokens: out,
  cache_creation: { ephemeral_5m_input_tokens: 4000, ephemeral_1h_input_tokens: 0 },
  cache_read_input_tokens: 30000,
});
const asst = (sid, ts, cwd, blocks, out = 300) => ({
  type: 'assistant', sessionId: sid, uuid: U(), requestId: `r${uid}`, timestamp: ts, cwd,
  message: { usage: usage(out), content: blocks },
});
const user = (sid, ts, cwd, text) => ({
  type: 'user', sessionId: sid, uuid: U(), promptId: `p${uid}`, timestamp: ts, cwd,
  message: { content: text },
});
const tool = (name, input) => ({ type: 'tool_use', id: `t${++uid}`, name, input });

// One .jsonl per session, the way Claude Code actually lays them out.
const bySession = new Map();
const emit = (o) => {
  const k = o.sessionId;
  if (!bySession.has(k)) bySession.set(k, []);
  bySession.get(k).push(JSON.stringify(o));
};

// Sessions that build things, spread across the invented repos.
const plan = [
  { repo: 'acme-api', sessions: 9, daysBack: [2, 3, 5, 6, 9, 12, 16, 20, 24], edits: 5, writes: 2 },
  { repo: 'acme-web', sessions: 5, daysBack: [4, 7, 11, 18, 22], edits: 3, writes: 1 },
  { repo: 'billing-service', sessions: 3, daysBack: [8, 15, 26], edits: 2, writes: 1 },
  { repo: 'infra-terraform', sessions: 2, daysBack: [13, 19], edits: 2, writes: 0 },
];
let sid = 0;
for (const p of plan) {
  const dir = path.join(HOME, 'code', p.repo);
  const files = REPOS[p.repo];
  for (let i = 0; i < p.sessions; i++) {
    const S = `s-${p.repo}-${++sid}`;
    const ts = day(p.daysBack[i % p.daysBack.length]);
    emit(user(S, ts, dir, 'add the thing'));
    for (let e = 0; e < p.edits; e++) {
      const f = path.join(dir, files[e % files.length]);
      emit(asst(S, ts, dir, [tool('Read', { file_path: f })], 120));
      emit(asst(S, ts, dir, [tool('Edit', { file_path: f, old_string: 'x\n'.repeat(9), new_string: 'y\n'.repeat(14) })], 400));
    }
    for (let w = 0; w < p.writes; w++) {
      const f = path.join(dir, files[(w + 1) % files.length]);
      emit(asst(S, ts, dir, [tool('Write', { file_path: f, content: 'z\n'.repeat(70) })], 700));
    }
    emit(asst(S, ts, dir, [tool('Bash', { command: 'npm test' })], 200));
    if (i % 3 === 0) {
      emit(user(S, ts, dir, 'open the PR'));
      emit(asst(S, ts, dir, [tool('Bash', { command: 'gh pr create --fill' })], 150));
    }
  }
}

// Work in a plain directory — no repo.
for (let i = 0; i < 4; i++) {
  const S = `s-notes-${i}`;
  const ts = day([6, 10, 17, 23][i]);
  const dir = path.join(HOME, 'notes');
  emit(user(S, ts, dir, 'draft the migration plan'));
  emit(asst(S, ts, dir, [tool('Write', { file_path: path.join(dir, NOTES[i % 2]), content: 'n\n'.repeat(55) })], 900));
}

// Research: no files touched, not in a repo. The row that surprises people.
for (let i = 0; i < 17; i++) {
  const S = `s-res-${i}`;
  const ts = day([1, 2, 3, 5, 7, 8, 9, 11, 12, 14, 16, 18, 20, 21, 25, 27, 28][i]);
  emit(user(S, ts, HOME, 'what changed in the pricing API?'));
  for (let k = 0; k < 6; k++) {
    emit(asst(S, ts, HOME, [tool('WebFetch', { url: 'https://example.com/docs' })], 350));
    emit(asst(S, ts, HOME, [tool('WebSearch', { query: 'pricing api changelog' })], 250));
  }
  emit(user(S, ts, HOME, 'and the rate limits?'));
  emit(asst(S, ts, HOME, [tool('WebFetch', { url: 'https://example.com/limits' })], 400));
}

for (const [k, ls] of bySession) fs.writeFileSync(path.join(PROJ, `${k}.jsonl`), ls.join('\n') + '\n');

// --- commits carrying that work ---------------------------------------------
const COMMITS = {
  'acme-api': [
    ['src/routes/orders.ts', 'orders: handle partial refunds', 2],
    ['src/lib/auth.ts', 'auth: rotate signing keys', 5],
    ['src/db/schema.sql', 'schema: add refund_reason', 9],
    ['tests/orders.test.ts', 'tests: cover partial refunds', 16],
  ],
  'acme-web': [
    ['app/checkout/page.tsx', 'checkout: inline tax breakdown', 4],
    ['app/cart/state.ts', 'cart: fix stale totals', 11],
  ],
  'billing-service': [['internal/invoice/render.go', 'invoice: round to minor units', 8]],
  'infra-terraform': [['envs/prod/main.tf', 'prod: bump rds instance class', 13]],
};
// Date each commit to the day the session that produced it ran, so the
// "N of your M active days ended in a commit" line reflects a real rhythm
// rather than a fixture written all at once.
for (const [repo, cs] of Object.entries(COMMITS)) {
  const dir = path.join(HOME, 'code', repo);
  for (const [f, msg, back] of cs) {
    fs.appendFileSync(path.join(dir, f), 'changed\n');
    const when = day(back);
    execFileSync('git', ['-C', dir, 'add', '-A'], { stdio: 'ignore' });
    execFileSync('git', ['-C', dir, 'commit', '-qm', msg], {
      stdio: 'ignore',
      env: { ...process.env, GIT_AUTHOR_DATE: when, GIT_COMMITTER_DATE: when },
    });
  }
}
console.log(HOME);
