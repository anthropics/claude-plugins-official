import { join } from '../paths'
import { linesOf } from '../text'
import { unitOfPath, type EstateModel, type EstateUnit } from './estate-model'
import type { ReaderFs } from './fs'
import { readTests, stateOfUplift, type ModernizedModule, type ModuleState, type TestTotals } from './modernized'

/**
 * What a same-stack uplift leaves on disk, read without knowing the stack: the
 * baseline's per-module results, the delta catalog's size, and which modules of the
 * working copy differ from the legacy tree.
 */

export type BaselineRow = { pass: number; fail: number; error: number; skip: number }

export type Baseline = {
  /** The file says the source runtime could not run here, so there is no per-test table. */
  isTargetOnly: boolean
  /** Test results in all, from the table or the file's own totals line. */
  results: number | null
  /** One row per module, keyed by the module path lower-cased with no trailing slash. */
  rows: Map<string, BaselineRow>
  /**
   * A baseline of one module has no per-module table: its title names the module and a small table gives the totals
   * (`| Passed | 945 |`). Those totals are that module's row.
   */
  headline: { title: string; row: BaselineRow } | null
}

const int = (text: string | undefined): number => {
  const value = Number((text ?? '').replace(/[,\s_]/g, ''))

  return Number.isFinite(value) ? value : 0
}

const cellsOf = (line: string): string[] =>
  line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map(cell => cell.trim())

const keyOf = (text: string): string =>
  text
    .replace(/[`*]/g, '')
    .replace(/^\.\//, '')
    .replace(/\/+$/, '')
    .trim()
    .toLowerCase()

/** Reads a baseline file: any table with pass and fail columns gives a row per module. */
export function parseBaseline(text: string): Baseline {
  const rows = new Map<string, BaselineRow>()
  const lines = linesOf(text)

  for (let index = 0; index < lines.length - 1; index += 1) {
    const head = lines[index] ?? ''

    if (!head.trim().startsWith('|') || !/^\s*\|?\s*:?-{2,}/.test(lines[index + 1] ?? '')) {
      continue
    }

    const names = cellsOf(head).map(name => name.replace(/[`*]/g, '').toLowerCase())
    const passAt = names.findIndex(name => /^pass/.test(name))
    const failAt = names.findIndex(name => /^fail/.test(name))

    if (passAt < 0 || failAt < 0) {
      continue
    }

    const errorAt = names.findIndex(name => /^err/.test(name))
    const skipAt = names.findIndex(name => /^(skip|ignor|pending)/.test(name))
    const found = names.findIndex(name => /^(module|project|unit|suite|package|assembly|component|name)/.test(name))
    const keyAt = found >= 0 ? found : 0

    for (let row = index + 2; row < lines.length && (lines[row] ?? '').trim().startsWith('|'); row += 1) {
      const cells = cellsOf(lines[row] ?? '')
      const key = keyOf(cells[keyAt] ?? '')

      if (key === '' || /^(total|totals|sum|all|overall)\b/.test(key)) {
        continue
      }

      rows.set(key, {
        pass: int(cells[passAt]),
        fail: int(cells[failAt]),
        error: errorAt >= 0 ? int(cells[errorAt]) : 0,
        skip: skipAt >= 0 ? int(cells[skipAt]) : 0,
      })
    }
  }

  const totals = /(?<![\d,])(\d[\d,]{0,14})\s+test\s+results?/i.exec(text)?.[1] ?? /\btotal\b[^\n]{0,40}?([\d,]{2,15})\s+tests?\b/i.exec(text)?.[1]
  const summed = [...rows.values()].reduce((sum, row) => sum + row.pass + row.fail + row.error + row.skip, 0)

  // The first `| Passed | 945 |` style lines, whatever else the file holds.
  const counts: Partial<Record<keyof BaselineRow, number>> = {}

  for (const line of lines) {
    const found = /^\s*\|\s*\**\s*(pass(?:ed)?|fail(?:ed|ures?)?|errors?|skipped|skip)\s*\**\s*\|\s*\**\s*([\d,]+)\s*\**\s*\|?\s*$/i.exec(line)

    if (found !== null) {
      const word = (found[1] ?? '').toLowerCase()
      const key: keyof BaselineRow = word.startsWith('pass') ? 'pass' : word.startsWith('fail') ? 'fail' : word.startsWith('err') ? 'error' : 'skip'

      counts[key] ??= int(found[2])
    }
  }

  const title = (lines.find(line => /^#\s+/.test(line)) ?? '').replace(/^#\s+/, '').replace(/[`*]/g, '').trim()

  return {
    isTargetOnly: /^\s*target-only:/im.test(text),
    results: totals !== undefined ? int(totals) : rows.size > 0 ? summed : null,
    rows,
    headline:
      counts.pass !== undefined && counts.fail !== undefined && title !== ''
        ? { title, row: { pass: counts.pass, fail: counts.fail, error: counts.error ?? 0, skip: counts.skip ?? 0 } }
        : null,
  }
}

/**
 * The baseline's row for one module: its own row, else the file's headline totals when its title names the module
 * (a pilot's baseline is one module's, and says so in its title). Null when there is nothing to compare with.
 */
export function baselineRowOf(baseline: Baseline | null, dir: string): BaselineRow | null {
  if (baseline === null || dir === '') {
    return null
  }

  const own = baseline.rows.get(keyOf(dir))

  if (own !== undefined) {
    return own
  }

  if (baseline.headline === null) {
    return null
  }

  const escaped = keyOf(dir).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

  return new RegExp(`(?<![\\w./-])${escaped}(?![\\w./-])`, 'i').test(baseline.headline.title) ? baseline.headline.row : null
}

export type Catalog = {
  count: number
  /** Lower-cased base name of a file the catalog cites, to the delta ids it is cited under. */
  byFileBase: Map<string, string[]>
}

/**
 * What the delta catalog holds: how many deltas (its own statement of the count, else its `D<n>` ids), and which
 * delta each file it names is cited under: the delta a table row or a heading names last, before the file.
 */
export function parseCatalog(text: string): Catalog | null {
  const stated = /\b(\d+)\s+(?:distinct\s+)?deltas\b/i.exec(text)?.[1]
  const ids = new Set<string>()
  const byFileBase = new Map<string, string[]>()
  let current: string | null = null

  for (const line of linesOf(text)) {
    const opens = /^\s*(?:\|\s*\**|#{1,6}\s+\**)(D-?\d{1,3})\b/.exec(line)?.[1]

    if (opens !== undefined) {
      current = opens
      ids.add(opens)
    }

    for (const found of line.matchAll(/D-?\d{1,3}\b/g)) {
      ids.add(found[0])
    }

    if (current === null) {
      continue
    }

    for (const cited of line.matchAll(/`([\w./@+-]+\.[A-Za-z0-9]{1,8})(?::\d+(?:[-–]\d+)?)?`/g)) {
      const base = (cited[1] ?? '').split('/').at(-1)?.toLowerCase() ?? ''
      const held = byFileBase.get(base) ?? []

      if (base !== '' && !held.includes(current)) {
        held.push(current)
        byFileBase.set(base, held)
      }
    }
  }

  const count = stated !== undefined && int(stated) > 0 ? int(stated) : ids.size

  return count > 0 ? { count, byFileBase } : null
}

/**
 * The paths that differ between a tree and the working copy made from it: a file present in both with another size,
 * one only the copy has, and one only the tree has. It compares names and sizes, so an edit that keeps a file's size
 * exactly is not seen here; a test run in that module, or an edit made during the session, shows it.
 */
export function changedPathsOf(before: ReadonlyMap<string, number>, after: ReadonlyMap<string, number>): string[] {
  const out: string[] = []

  for (const [path, size] of after) {
    if (before.get(path) !== size) {
      out.push(path)
    }
  }

  for (const path of before.keys()) {
    if (!after.has(path)) {
      out.push(path)
    }
  }

  return out
}

/** The estate's unit ids that hold at least one of the changed paths. */
export function changedUnitsOf(estate: EstateModel, changed: readonly string[]): Set<string> {
  const ids = new Set<string>()

  for (const path of changed) {
    const unit = unitOfPath(estate, null, path)

    if (unit !== null) {
      ids.add(unit.id)
    }
  }

  return ids
}

/**
 * Each unit of the working copy that the uplift has touched or tested, with its state:
 * changed, tested, matching the baseline, or worse than it. `observed` holds the totals of test
 * runs seen this session, used where no report file was left.
 */
export async function readUpliftUnits(
  fs: ReaderFs,
  workingRoot: string,
  estate: EstateModel,
  changed: ReadonlySet<string>,
  baseline: Baseline | null,
  observed: ReadonlyMap<string, TestTotals>,
): Promise<{ unit: EstateUnit; module: ModernizedModule }[]> {
  const out: { unit: EstateUnit; module: ModernizedModule }[] = []

  for (const unit of estate.units) {
    if (unit.dir === undefined) {
      if (changed.has(unit.id)) {
        out.push({ unit, module: moduleOf(unit.name, join(workingRoot, unit.file ?? unit.id), null, 'scaffolded') })
      }

      continue
    }

    const path = unit.dir === '' ? workingRoot : join(workingRoot, unit.dir)
    const tests = (await readTests(fs, path)) ?? observed.get(path) ?? null
    const row = baselineRowOf(baseline, unit.dir)
    const state = stateOfUplift(tests, row, changed.has(unit.id))

    if (state !== 'untouched') {
      out.push({ unit, module: moduleOf(unit.dir === '' ? unit.name : unit.dir, path, tests, state) })
    }
  }

  return out
}

function moduleOf(dir: string, path: string, tests: TestTotals | null, state: ModuleState): ModernizedModule {
  return {
    dir,
    path,
    hasMain: true,
    hasTests: tests !== null,
    hasNotes: false,
    hasReviewSection: false,
    isPortedNotSwitched: false,
    isSwitched: false,
    followUps: 0,
    tests,
    state,
    mtimeMs: 0,
  }
}
