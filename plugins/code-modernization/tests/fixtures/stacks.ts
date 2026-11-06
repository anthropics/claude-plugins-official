import { norm } from '../../hooks/paths'
import type { ReaderFs } from '../../hooks/reader/fs'

/**
 * Workspaces in the shape the plugin's commands leave, in stacks that are not COBOL: a Maven
 * project being uplifted, a PHP shop with no map, a .NET solution, a Node monorepo, a greenfield
 * rebuild, and a legacy tree nobody has analysed yet. Sizes are the length of the text given.
 */

/** A file tree in memory, read the way the reader reads `$.fs`. */
export function memoryFs(
  files: Readonly<Record<string, string>>,
  mtimes: Readonly<Record<string, number>> = {},
  /** Paths that are symbolic links to a directory: listed as `other`, as the engine lists a link; `stat` says `dir`. */
  links: readonly string[] = [],
): ReaderFs {
  const dirs = new Set<string>([''])

  for (const path of Object.keys(files)) {
    const parts = path.split('/')

    for (let index = 1; index < parts.length; index += 1) {
      dirs.add(parts.slice(0, index).join('/'))
    }
  }

  const at = (path: string) => mtimes[path] ?? 1_000

  return {
    read: async path => {
      const text = files[norm(path)]

      if (text === undefined) {
        throw new Error(`ENOENT: ${path}`)
      }

      return text
    },
    exists: async path => files[norm(path)] !== undefined || dirs.has(norm(path)),
    stat: async path => {
      const key = norm(path)
      const text = files[key]

      if (text !== undefined) {
        return { kind: 'file' as const, size: text.length, mtimeMs: at(key) }
      }

      if (dirs.has(key)) {
        return { kind: 'dir' as const, size: 0, mtimeMs: at(key) }
      }

      throw new Error(`ENOENT: ${path}`)
    },
    list: async path => {
      const dir = norm(path)
      const names = new Map<string, 'file' | 'dir'>()

      for (const file of Object.keys(files)) {
        if (dir !== '' && !file.startsWith(`${dir}/`)) {
          continue
        }

        const rest = dir === '' ? file : file.slice(dir.length + 1)
        const name = rest.split('/')[0] ?? ''

        names.set(name, rest.includes('/') ? 'dir' : 'file')
      }

      return [...names.entries()].sort().map(([name, kind]) => {
        const isLink = links.includes(dir === '' ? name : `${dir}/${name}`)

        return {
          name,
          kind: isLink ? ('other' as const) : kind,
          size: kind === 'file' ? (files[dir === '' ? name : `${dir}/${name}`]?.length ?? 0) : 0,
          isLink,
        }
      })
    },
  }
}

const code = (bytes: number) => 'x'.repeat(bytes)

const junit = (tests: number, failures: number, errors: number, skipped: number) =>
  `<testsuite name="s" tests="${tests}" failures="${failures}" errors="${errors}" skipped="${skipped}"></testsuite>`

// ---------------------------------------------------------------- Java / Maven uplift

/**
 * `shop`: a three-module Maven system moved to a newer JDK. The baseline is a per-module table; two modules
 * were tested on the new runtime (`shop-core` reproduces its baseline, `shop-web` has three new failures).
 */
export const MAVEN_UPLIFT: Record<string, string> = {
  'legacy/shop/pom.xml': '<project/>',
  'legacy/shop/shop-core/pom.xml': '<project/>',
  'legacy/shop/shop-core/src/main/java/Ledger.java': code(4000),
  'legacy/shop/shop-web/pom.xml': '<project/>',
  'legacy/shop/shop-web/src/main/java/Page.java': code(6000),
  'legacy/shop/shop-batch/pom.xml': '<project/>',
  'legacy/shop/shop-batch/src/main/java/Nightly.java': code(2000),
  'analysis/shop/PREFLIGHT.md': '# Preflight',
  'analysis/shop/DELTA_CATALOG.md': [
    '# Delta catalog',
    '',
    'The survey found **12 distinct deltas** in this code.',
    '',
    '| Delta | What breaks | Where |',
    '|---|---|---|',
    '| **D08** | `Ledger` reflects into `java.base` | `shop-core/src/main/java/Ledger.java:41` |',
    '| **D15** | Mapped buffers | `shop-core/src/main/java/Ledger.java:77-90`, `shop-web/src/main/java/Page.java:12` |',
    '',
  ].join('\n'),
  'analysis/shop/BASELINE.md': [
    '# BASELINE',
    '',
    '**78 test results** in 3 modules: error = 0, fail = 1, pass = 75, skip = 2',
    '',
    '| Module | pass | fail | error | skip |',
    '|---|---:|---:|---:|---:|',
    '| `shop-core` | 40 | 1 | 0 | 2 |',
    '| `shop-web` | 25 | 0 | 0 | 0 |',
    '| `shop-batch` | 10 | 0 | 0 | 0 |',
  ].join('\n'),
  'analysis/shop/PLAYBOOK.md': '# Playbook',
  'modernized/shop-uplifted/pom.xml': '<project/>',
  'modernized/shop-uplifted/shop-core/pom.xml': '<project/>',
  'modernized/shop-uplifted/shop-core/src/main/java/Ledger.java': code(4010),
  'modernized/shop-uplifted/shop-core/target/surefire-reports/TEST-Ledger.xml': junit(43, 1, 0, 2),
  'modernized/shop-uplifted/shop-web/pom.xml': '<project/>',
  'modernized/shop-uplifted/shop-web/src/main/java/Page.java': code(6000),
  'modernized/shop-uplifted/shop-web/target/surefire-reports/TEST-Page.xml': junit(25, 3, 0, 0),
  'modernized/shop-uplifted/shop-batch/pom.xml': '<project/>',
  'modernized/shop-uplifted/shop-batch/src/main/java/Nightly.java': code(2050),
}

// ---------------------------------------------------------------------- PHP, no map

const phpPages = Object.fromEntries(
  Array.from({ length: 24 }, (_, index) => [`legacy/webshop/catalog/page${index}.php`, code(300 + index * 40)]),
)

/** `webshop`: a PHP shop with no build files and no map, one file per unit; only the preflight has run. */
export const PHP_NO_MAP: Record<string, string> = {
  ...phpPages,
  'legacy/webshop/includes/db.php': code(2500),
  'legacy/webshop/includes/cart.php': code(3100),
  'legacy/webshop/index.php': code(900),
  'legacy/webshop/images/logo.png': code(50_000),
  'legacy/webshop/README.md': code(4000),
  'analysis/webshop/PREFLIGHT.md': '# Preflight',
}

// ----------------------------------------------------------------------------- .NET

/** `ledger`: a .NET solution rewritten module by module; the core module's tests left a .trx report. */
export const DOTNET_REWRITE: Record<string, string> = {
  'legacy/ledger/Ledger.sln': 'sln',
  'legacy/ledger/Ledger.Core/Ledger.Core.csproj': '<Project/>',
  'legacy/ledger/Ledger.Core/Accounts.cs': code(5000),
  'legacy/ledger/Ledger.Core/Interest.vb': code(3000),
  'legacy/ledger/Ledger.Web/Ledger.Web.csproj': '<Project/>',
  'legacy/ledger/Ledger.Web/Default.aspx': code(2000),
  'analysis/ledger/ASSESSMENT.md': '# Assessment',
  'modernized/ledger/Ledger.Core/src/main/Accounts.cs': code(4800),
  'modernized/ledger/Ledger.Core/tests/AccountsTests.cs': code(900),
  'modernized/ledger/Ledger.Core/TestResults/run.trx':
    '<TestRun><ResultSummary><Counters total="14" executed="14" passed="14" failed="0" error="0" timeout="0" aborted="0" inconclusive="0" notExecuted="0"/></ResultSummary></TestRun>',
  'modernized/ledger/Ledger.Core/TRANSFORMATION_NOTES.md': '# Notes\n\n## Follow-ups\n- none\n',
}

// ------------------------------------------------------------------- Node monorepo

/** `portal`: a Node monorepo; a module of the rewrite is tested by a runner that leaves no report file. */
export const NODE_REWRITE: Record<string, string> = {
  'legacy/portal/package.json': '{"workspaces":["packages/*"]}',
  'legacy/portal/packages/auth/package.json': '{}',
  'legacy/portal/packages/auth/index.js': code(3000),
  'legacy/portal/packages/billing/package.json': '{}',
  'legacy/portal/packages/billing/index.js': code(9000),
  'legacy/portal/packages/ui/package.json': '{}',
  'legacy/portal/packages/ui/index.js': code(5000),
  'analysis/portal/ASSESSMENT.md': '# Assessment',
  'modernized/portal/billing/src/main.ts': code(2000),
  'modernized/portal/billing/tests/billing.test.ts': code(800),
}

// -------------------------------------------------------------------- reimagine

/** `crm`: a greenfield rebuild with two scaffolded services; only one has acceptance tests. */
export const REIMAGINE: Record<string, string> = {
  'legacy/crm/app.pl': code(4000),
  'legacy/crm/lib/Contact.pm': code(3000),
  'analysis/crm/AI_NATIVE_SPEC.md': '# Spec',
  'analysis/crm/REIMAGINED_ARCHITECTURE.md': '# Architecture',
  'modernized/crm-reimagined/CLAUDE.md': '# Context',
  'modernized/crm-reimagined/accounts/src/main.py': code(1200),
  'modernized/crm-reimagined/accounts/tests/test_accounts.py': code(600),
  'modernized/crm-reimagined/accounts/pytest.xml': junit(6, 0, 0, 0),
  'modernized/crm-reimagined/billing/src/main.py': code(900),
}

// ------------------------------------------------------------ legacy, not analysed

/** `ops`: a legacy system somebody dropped in `legacy/`; nothing has been run on it. */
export const LEGACY_ONLY: Record<string, string> = {
  'legacy/ops/jobs/nightly.cbl': code(4000),
  'legacy/ops/jobs/monthly.cbl': code(2500),
  'legacy/ops/copy/rates.cpy': code(700),
}

// ------------------------------------------------------------------ bigger trees

/** 620 Python files in six packages under `src/`, no build files: too many for a tile each. */
export const PYTHON_BIG: Record<string, string> = Object.fromEntries(
  Array.from({ length: 620 }, (_, index) => [`legacy/erp/src/pkg${index % 6}/mod${index}.py`, code(200 + (index % 17) * 30)]),
)
