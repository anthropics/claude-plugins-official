import { join } from '../paths'
import { linesOf } from '../text'
import { listOrEmpty, readOrNull, type ReaderFs } from './fs'

/**
 * The state of each transformed module, read from `modernized/<system>/`:
 * what exists on disk, what the test reports say, what the notes record.
 * No inference: a fact that is not on disk is absent.
 */

export type TestTotals = {
  tests: number
  failures: number
  errors: number
  skipped: number
  /** How many report files were read. */
  reports: number
}

export type ModuleState =
  | 'scaffolded'
  | 'tests-written'
  | 'tests-red'
  /** An uplift's tests fail and there is no baseline row to say whether the source runtime failed them too. */
  | 'tests-failing'
  | 'tests-green'
  | 'reviewed'
  | 'ported'
  | 'switched'

export type ModernizedModule = {
  /** The directory's name under `modernized/<system>/`. */
  dir: string
  /** Path relative to the working directory. */
  path: string
  hasMain: boolean
  hasTests: boolean
  hasNotes: boolean
  /** The date in the notes' "Architecture review" section; absent when none. */
  reviewDate?: string
  hasReviewSection: boolean
  /** The notes say "ported, not switched". */
  isPortedNotSwitched: boolean
  /** The notes say the route was switched. */
  isSwitched: boolean
  /** Open follow-ups the notes list (bullets under a Follow-ups heading). */
  followUps: number
  tests: TestTotals | null
  state: ModuleState
  /** Newest mtime among the notes and test reports; 0 when unknown. */
  mtimeMs: number
}

/** States a unit of work counts as finished in: the review is done, or the module is ported or switched. */
const DONE_STATES: ReadonlySet<ModuleState> = new Set(['reviewed', 'ported', 'switched'])

/**
 * Whether a module's work is finished. Green tests with notes written count: the notes are where the plugin's
 * review step lists what the critic found, and how they headline it varies, so a missing headline is not unfinished work.
 */
export const isDone = (module: Pick<ModernizedModule, 'state' | 'hasNotes'>): boolean =>
  DONE_STATES.has(module.state) || (module.state === 'tests-green' && module.hasNotes)

const EMPTY: TestTotals = { tests: 0, failures: 0, errors: 0, skipped: 0, reports: 0 }

/** Totals of one Visual Studio test result file (`.trx`), the report `dotnet test --logger trx` leaves. */
export function totalsOfTrx(xml: string): TestTotals | null {
  const counters = /<Counters\b[^>]*>/.exec(xml)?.[0]

  if (counters === undefined || !/\btotal="\d+"/.test(counters)) {
    return null
  }

  return {
    tests: attr(counters, 'total'),
    failures: attr(counters, 'failed'),
    errors: attr(counters, 'error') + attr(counters, 'timeout') + attr(counters, 'aborted'),
    skipped: attr(counters, 'notExecuted') + attr(counters, 'inconclusive'),
    reports: 1,
  }
}

const attr = (tag: string, name: string): number => {
  const match = new RegExp(`\\b${name}="(\\d+)"`).exec(tag)

  return match?.[1] !== undefined ? Number(match[1]) : 0
}

/** Totals of one JUnit-style XML report (`<testsuite ...>` / `<testsuites ...>`). */
export function totalsOfJunitXml(xml: string): TestTotals | null {
  const suites = /<testsuites\b[^>]*>/.exec(xml)?.[0]

  if (suites !== undefined && /\btests="\d+"/.test(suites)) {
    return {
      tests: attr(suites, 'tests'),
      failures: attr(suites, 'failures'),
      errors: attr(suites, 'errors'),
      skipped: attr(suites, 'skipped') + attr(suites, 'disabled'),
      reports: 1,
    }
  }

  const all = [...xml.matchAll(/<testsuite\b[^>]*>/g)].map(match => match[0])

  if (all.length === 0) {
    return null
  }

  return all.reduce<TestTotals>(
    (sum, tag) => ({
      tests: sum.tests + attr(tag, 'tests'),
      failures: sum.failures + attr(tag, 'failures'),
      errors: sum.errors + attr(tag, 'errors'),
      skipped: sum.skipped + attr(tag, 'skipped') + attr(tag, 'disabled'),
      reports: 1,
    }),
    { ...EMPTY, reports: 1 },
  )
}

const add = (a: TestTotals, b: TestTotals): TestTotals => ({
  tests: a.tests + b.tests,
  failures: a.failures + b.failures,
  errors: a.errors + b.errors,
  skipped: a.skipped + b.skipped,
  reports: a.reports + b.reports,
})

/** Where test runners leave JUnit XML, relative to a module's directory. */
const REPORT_DIRS = [
  'target/surefire-reports',
  'target/failsafe-reports',
  'build/test-results/test',
  'build/test-results',
  'build/logs',
  'test-results',
  'test-reports',
  'reports/junit',
  'TestResults',
]

const REPORT_FILES = ['junit.xml', 'report.xml', 'test-report.xml', 'pytest.xml']

/** When a file last changed; 0 when it cannot be said. */
async function changedAt(fs: ReaderFs, path: string): Promise<number> {
  try {
    return (await fs.stat(path)).mtimeMs
  } catch {
    return 0
  }
}

/**
 * The test totals a directory's report files hold: a custom JSON report, JUnit XML, or a `.trx`, and when the newest of
 * the files read last changed (what a verdict about the module is compared with).
 */
export async function readTestsAt(fs: ReaderFs, dir: string, withTime = true): Promise<{ totals: TestTotals; atMs: number } | null> {
  const stamp = (path: string) => (withTime ? changedAt(fs, path) : Promise.resolve(0))
  const customPath = join(dir, '.modernize/test-report.json')
  const custom = await readOrNull(fs, customPath)

  if (custom !== null) {
    try {
      const raw = JSON.parse(custom) as Record<string, unknown>
      const num = (key: string) => (typeof raw[key] === 'number' ? (raw[key] as number) : 0)

      return {
        totals: {
          tests: num('tests'),
          failures: num('failures'),
          errors: num('errors'),
          skipped: num('skipped'),
          reports: 1,
        },
        atMs: await stamp(customPath),
      }
    } catch {
      // fall through to the XML reports
    }
  }

  let total: TestTotals | null = null
  let atMs = 0

  for (const sub of REPORT_DIRS) {
    const entries = await listOrEmpty(fs, join(dir, sub))

    for (const entry of entries) {
      const isTrx = entry.name.endsWith('.trx')

      if (entry.kind !== 'file' || !(entry.name.endsWith('.xml') || isTrx) || entry.size > 3_500_000) {
        continue
      }

      const xml = await readOrNull(fs, join(dir, sub, entry.name))
      const totals = xml === null ? null : isTrx ? totalsOfTrx(xml) : totalsOfJunitXml(xml)

      if (totals !== null) {
        total = total === null ? totals : add(total, totals)
        atMs = Math.max(atMs, await stamp(join(dir, sub, entry.name)))
      }
    }

    if (total !== null) {
      return { totals: total, atMs }
    }
  }

  for (const name of REPORT_FILES) {
    const xml = await readOrNull(fs, join(dir, name))
    const totals = xml !== null ? totalsOfJunitXml(xml) : null

    if (totals !== null) {
      return { totals, atMs: await stamp(join(dir, name)) }
    }
  }

  return null
}

/** The test totals a directory's report files hold, without asking when each file changed. */
export async function readTests(fs: ReaderFs, dir: string): Promise<TestTotals | null> {
  return (await readTestsAt(fs, dir, false))?.totals ?? null
}

const TEST_DIRS = ['src/test', 'tests', 'test', 'spec', '__tests__']
const MAIN_DIRS = ['src/main', 'src', 'app', 'lib']

async function anyDir(fs: ReaderFs, dir: string, names: readonly string[]): Promise<boolean> {
  for (const name of names) {
    if ((await listOrEmpty(fs, join(dir, name))).length > 0) {
      return true
    }
  }

  return false
}

/** What the notes record, read by heading and phrase. */
export function readNotes(notes: string): {
  hasReviewSection: boolean
  reviewDate?: string
  isPortedNotSwitched: boolean
  isSwitched: boolean
  followUps: number
} {
  const lines = linesOf(notes)
  // The plugin's review step spawns the architecture critic and lists what it found in the notes; how the notes
  // headline that varies, so any heading that says review or critic counts, and so does naming the critic.
  const named = lines.findIndex(line => /^#{1,4}\s+.*\b(?:review|critic)/i.test(line))
  const start = named >= 0 ? named : -1
  let reviewDate: string | undefined

  if (start >= 0) {
    const level = /^(#+)/.exec(lines[start] ?? '')?.[1]?.length ?? 2

    const end = lines.findIndex(
      (line, index) => index > start && new RegExp(`^#{1,${level}}\\s`).test(line),
    )

    const section = lines.slice(start, end < 0 ? undefined : end).join('\n')

    reviewDate = /\b(\d{4}-\d{2}-\d{2})\b/.exec(section)?.[1]
  }

  const followStart = lines.findIndex(line => /^#{1,4}\s+.*follow-?ups?/i.test(line))
  let followUps = 0

  if (followStart >= 0) {
    for (const line of lines.slice(followStart + 1)) {
      if (/^#{1,4}\s/.test(line)) {
        break
      }

      if (/^\s*[-*]\s+(?!\[[xX]\])/.test(line) || /^\s*\d+\.\s+/.test(line)) {
        followUps += 1
      }
    }
  }

  const isPortedNotSwitched = /ported,?\s+not\s+switched/i.test(notes)

  return {
    hasReviewSection: start >= 0 || /architecture[- ]critic/i.test(notes),
    ...(reviewDate !== undefined && { reviewDate }),
    isPortedNotSwitched,
    isSwitched:
      !isPortedNotSwitched &&
      /\b(?:route|traffic)\b[^\n]{0,40}\bswitched\b|\bswitched\b[^\n]{0,20}\b\d{4}-\d{2}-\d{2}\b/i.test(
        notes,
      ),
    followUps,
  }
}

/** The state a module's facts add up to, furthest first. */
export function stateOf(module: Omit<ModernizedModule, 'state'>): ModuleState {
  const tests = module.tests
  const isRed = tests !== null && tests.failures + tests.errors > 0
  const isGreen = tests !== null && tests.tests > 0 && !isRed

  if (module.isSwitched && isGreen && module.hasReviewSection) {
    return 'switched'
  }

  if (module.isPortedNotSwitched && isGreen) {
    return 'ported'
  }

  if (isGreen && module.hasReviewSection) {
    return 'reviewed'
  }

  if (isRed) {
    return 'tests-red'
  }

  if (isGreen) {
    return 'tests-green'
  }

  if (module.hasTests) {
    return 'tests-written'
  }

  return 'scaffolded'
}

/**
 * The state of one unit of an uplift's working copy: worse than its baseline, matching or exceeding it
 * (every test that passed on the source runtime still passes, none is missing), tested but not comparable
 * to a baseline row, changed and not yet tested, or not touched at all.
 */
export function stateOfUplift(
  tests: TestTotals | null,
  baseline: { pass: number; fail: number; error: number; skip: number } | null,
  isChanged: boolean,
): ModuleState | 'untouched' {
  if (tests !== null && tests.tests > 0) {
    const bad = tests.failures + tests.errors

    // With no baseline row there is nothing to be worse than: the failures are said, not judged.
    if (baseline === null && bad > 0) {
      return 'tests-failing'
    }

    if (baseline !== null && bad > baseline.fail + baseline.error) {
      return 'tests-red'
    }

    const passed = tests.tests - bad - tests.skipped
    const isCovered = baseline !== null && tests.tests >= baseline.pass + baseline.fail + baseline.error + baseline.skip && passed >= baseline.pass

    return isCovered ? 'reviewed' : 'tests-green'
  }

  return isChanged ? 'scaffolded' : 'untouched'
}

/** Reads every code directory under `modernized/<system>/`. */
export async function readModernized(
  fs: ReaderFs,
  system: string,
): Promise<ModernizedModule[]> {
  return readModernizedIn(fs, join('modernized', system))
}

/** Reads every code directory directly under `root`: a transformed system's modules, or a reimagined system's services. */
export async function readModernizedIn(
  fs: ReaderFs,
  root: string,
  observed: ReadonlyMap<string, TestTotals> = new Map(),
): Promise<ModernizedModule[]> {
  const entries = await listOrEmpty(fs, root)
  const out: ModernizedModule[] = []

  for (const entry of entries) {
    if (entry.kind !== 'dir' || entry.name.startsWith('.')) {
      continue
    }

    const path = join(root, entry.name)
    const notes = await readOrNull(fs, join(path, 'TRANSFORMATION_NOTES.md'))
    const read = notes !== null ? readNotes(notes) : null
    const reported = await readTestsAt(fs, path)
    const tests = reported?.totals ?? observed.get(path) ?? null
    // The newest of the notes and the test reports: what a verdict about the module is checked against.
    const mtimeMs = Math.max(notes !== null ? await changedAt(fs, join(path, 'TRANSFORMATION_NOTES.md')) : 0, reported?.atMs ?? 0)

    const facts = {
      dir: entry.name,
      path,
      hasMain: await anyDir(fs, path, MAIN_DIRS),
      hasTests: await anyDir(fs, path, TEST_DIRS),
      hasNotes: notes !== null,
      hasReviewSection: read?.hasReviewSection ?? false,
      ...(read?.reviewDate !== undefined && { reviewDate: read.reviewDate }),
      isPortedNotSwitched: read?.isPortedNotSwitched ?? false,
      isSwitched: read?.isSwitched ?? false,
      followUps: read?.followUps ?? 0,
      tests,
      mtimeMs,
    }

    out.push({ ...facts, state: stateOf(facts) })
  }

  return out
}
