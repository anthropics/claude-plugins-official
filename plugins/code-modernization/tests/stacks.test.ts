import { describe, expect, mock, test } from 'claude-code/testing'

import { tilesOf } from '../hooks/map/estate'
import { discoverEstate } from '../hooks/reader/discover'
import { xrayOf } from '../hooks/xray/xray'
import { readNotes, stateOfUplift, totalsOfTrx } from '../hooks/reader/modernized'
import { oneLineOf, readSnapshot, systemsOf, type ReadOptions, type Snapshot } from '../hooks/reader/progress'
import { baselineRowOf, changedPathsOf, parseBaseline, parseCatalog } from '../hooks/reader/uplift'
import { pickTrack } from '../hooks/reader/tracks'
import { BAND, command, HINT, PANE, SESSION } from './fixtures/inputs'
import {
  DOTNET_REWRITE,
  LEGACY_ONLY,
  MAVEN_UPLIFT,
  memoryFs,
  NODE_REWRITE,
  PHP_NO_MAP,
  PYTHON_BIG,
  REIMAGINE,
} from './fixtures/stacks'
import { elementsOf, rowsOf, textOf, worldOf } from './fixtures/world'
import { FULL } from './fixtures/workspace'

const NAME = 'code-modernization'
const PREFIX = '/p:modernize-'

async function read(files: Record<string, string>, more: Partial<ReadOptions> = {}): Promise<Snapshot> {
  const snapshot = await readSnapshot(memoryFs(files), new Map(), { commandPrefix: PREFIX, nowMs: 0, ...more })

  if (snapshot === null) {
    throw new Error('no snapshot')
  }

  return snapshot
}

const stateOfUnit = (snapshot: Snapshot, name: string) => snapshot.byNode.get(name)?.state

describe('uplift, whatever the stack', () => {
  test('a Maven uplift is followed from its own artifacts: the delta catalog, the baseline, the playbook and the working copy', async () => {
    const snapshot = await read(MAVEN_UPLIFT)

    expect(snapshot.track).toBe('uplift')
    expect(snapshot.stages.map(stage => `${stage.isDone ? '✓' : '·'}${stage.key}`)).toEqual([
      '✓preflight',
      '✓deltas',
      '✓baseline',
      '✓pilot',
      '✓migrate',
      '·compare',
      '·verify',
    ])
    expect(snapshot.stages.find(stage => stage.key === 'deltas')?.detail).toBe('12 deltas')
    expect(snapshot.stages.find(stage => stage.key === 'baseline')?.detail).toBe('78 tests')

    // No map was run: the estate is read off the tree, one unit per module that has a build file of its own.
    expect(snapshot.estate?.source).toBe('tree')
    expect(snapshot.estate?.granularity).toBe('build module')
    expect(snapshot.estate?.units.map(unit => unit.name).sort()).toEqual(['shop', 'shop-batch', 'shop-core', 'shop-web'].sort())
    expect(snapshot.estate?.languages[0]?.name).toBe('Java')

    // shop-core reproduces its baseline; shop-web has three failures the baseline did not; shop-batch was edited, not tested.
    expect(stateOfUnit(snapshot, 'shop-core')).toBe('reviewed')
    expect(stateOfUnit(snapshot, 'shop-web')).toBe('tests-red')
    expect(stateOfUnit(snapshot, 'shop-batch')).toBe('scaffolded')
    expect(snapshot.attention).toContain('shop-web: 3 failing, the baseline had 0')
    expect(snapshot.uplift?.isChangeKnown).toBe(true)

    // The uplift command takes the two versions from what the person said at the start, and asks when it has none: no placeholder.
    expect(snapshot.next?.isByHand).toBe(false)
    expect(snapshot.next?.text).toBe(`${PREFIX}uplift shop`)
    expect(snapshot.next?.reason).toContain('each compared with the baseline')

    expect(oneLineOf(snapshot)).toContain('shop: uplift 5/7 · ')
    expect(snapshot.percent).not.toBe(null)
  })

  test('the working copy is compared with the tree by file name and size, and a write seen in the session counts too', async () => {
    // shop-batch's Nightly.java is 2050 bytes in the copy and 2000 in the tree; shop-web's files are the same size in both.
    const same = { ...MAVEN_UPLIFT, 'modernized/shop-uplifted/shop-batch/src/main/java/Nightly.java': 'x'.repeat(2000) }
    const quiet = await read(same)

    expect(stateOfUnit(quiet, 'shop-batch'), 'an edit that keeps a file the same size is not seen by the comparison').toBe(undefined)
    expect(stateOfUnit(await read(same, { writtenUnits: new Set(['shop-batch']) }), 'shop-batch'), 'but a write the session saw is').toBe('scaffolded')

    const added = await read({ ...same, 'modernized/shop-uplifted/shop-batch/src/main/java/Extra.java': 'x'.repeat(10) })

    expect(stateOfUnit(added, 'shop-batch'), 'a file only the copy has').toBe('scaffolded')

    const removed: Record<string, string> = { ...same }

    delete removed['modernized/shop-uplifted/shop-batch/src/main/java/Nightly.java']
    expect(stateOfUnit(await read(removed), 'shop-batch'), 'a file only the tree has').toBe('scaffolded')
  })

  test('with no working copy there is nothing to compare, and the pane says the changes are unread', async () => {
    const files = Object.fromEntries(Object.entries(MAVEN_UPLIFT).filter(([path]) => !path.startsWith('modernized/')))
    const snapshot = await read(files)

    expect(snapshot.track).toBe('uplift')
    expect(snapshot.uplift?.hasCopy).toBe(false)
    expect(snapshot.uplift?.isChangeKnown).toBe(false)
    expect(snapshot.modules).toEqual([])
  })

  test('a listing of the working copy is reused for a while, then read again', async () => {
    const files: Record<string, string> = { ...MAVEN_UPLIFT, 'modernized/shop-uplifted/shop-batch/src/main/java/Nightly.java': 'x'.repeat(2000) }
    const fs = memoryFs(files)
    const cache = new Map()
    const options = { commandPrefix: PREFIX, nowMs: 0 }
    const first = await readSnapshot(fs, cache, options)

    expect(first?.byNode.get('shop-batch')).toBe(undefined)
    files['modernized/shop-uplifted/shop-batch/src/main/java/Nightly.java'] = 'x'.repeat(2100)

    expect((await readSnapshot(fs, cache, { ...options, nowMs: 5_000 }))?.byNode.get('shop-batch'), 'read again too soon: the earlier listing stands').toBe(undefined)
    expect((await readSnapshot(fs, cache, { ...options, nowMs: 20_000 }))?.byNode.get('shop-batch')?.state, 'past the interval it is read again').toBe('scaffolded')
    expect((await readSnapshot(fs, cache, { ...options, nowMs: 21_000, changedTtlMs: 0 }))?.byNode.get('shop-batch')?.state).toBe('scaffolded')
  })

  test('a module counts as matching only when every baseline pass still passes and none is missing', () => {
    const row = { pass: 40, fail: 1, error: 0, skip: 2 }
    const totals = (tests: number, failures: number, skipped = 0) => ({ tests, failures, errors: 0, skipped, reports: 1 })

    expect(stateOfUplift(totals(43, 1, 2), row, true)).toBe('reviewed')
    expect(stateOfUplift(totals(50, 1, 2), row, true), 'new tests were added').toBe('reviewed')
    expect(stateOfUplift(totals(40, 1, 2), row, true), 'three tests did not run').toBe('tests-green')
    expect(stateOfUplift(totals(43, 2, 2), row, true), 'one more failure than the baseline').toBe('tests-red')
    expect(stateOfUplift(totals(10, 0), null, true), 'nothing to compare with').toBe('tests-green')
    expect(stateOfUplift(null, row, true)).toBe('scaffolded')
    expect(stateOfUplift(null, row, false)).toBe('untouched')
  })

  test('baselines are read whatever the columns are called, and a target-only one has no table', () => {
    const jvm = parseBaseline('| Module | pass | fail | error | skip |\n|---|---:|---:|---:|---:|\n| `a/b` | 3 | 1 | 0 | 2 |\n| **Total** | 3 | 1 | 0 | 2 |')

    expect([...jvm.rows.entries()]).toEqual([['a/b', { pass: 3, fail: 1, error: 0, skip: 2 }]])
    expect(jvm.results).toBe(6)

    const dotnet = parseBaseline('| Project | Passed | Failed | Skipped |\n|---|---|---|---|\n| Ledger.Core | 1,204 | 0 | 12 |')

    expect(dotnet.rows.get('ledger.core')).toEqual({ pass: 1204, fail: 0, error: 0, skip: 12 })

    const target = parseBaseline('target-only: the .NET Framework runtime is not available here')

    expect(target.isTargetOnly).toBe(true)
    expect(target.rows.size).toBe(0)
  })

  test('a baseline of one module has no table of modules: its totals are that module\'s row, and only that module\'s', async () => {
    const pilot = [
      '# BASELINE: shop-web on Java 8 (the oracle)',
      '',
      '## Totals',
      '',
      '| | Count |',
      '|---|---|',
      '| Test cases (per-test XML) | 1039 |',
      '| **Executed** | **946** |',
      '| Passed | 945 |',
      '| Failed | 1 |',
      '| Errors | 0 |',
      '| Skipped | 93 |',
      '',
      '## Per-class results',
      '',
      '| Class | pass | fail | error | skip |',
      '|---|---|---|---|---|',
      '| `PageTest` | 3 | 0 | 0 | 0 |',
    ].join('\n')

    const baseline = parseBaseline(pilot)

    expect(baseline.headline).toEqual({ title: 'BASELINE: shop-web on Java 8 (the oracle)', row: { pass: 945, fail: 1, error: 0, skip: 93 } })
    expect(baselineRowOf(baseline, 'shop-web')).toEqual({ pass: 945, fail: 1, error: 0, skip: 93 })
    expect(baselineRowOf(baseline, 'shop'), 'a module the title does not name has no row').toBe(null)
    expect(baselineRowOf(baseline, 'shop-webapp'), 'nor one whose name only starts the same way').toBe(null)
    expect(baselineRowOf(baseline, ''), 'the root has none').toBe(null)
    expect(baselineRowOf(null, 'shop-web')).toBe(null)
    expect(parseBaseline('| Module | pass | fail |\n|---|---|---|\n| a | 1 | 0 |').headline).toBe(null)

    // In the snapshot: shop-web's three new failures are set against the one the pilot's baseline had.
    const files = { ...MAVEN_UPLIFT, 'analysis/shop/BASELINE.md': pilot }
    const snapshot = await read(files)

    expect(stateOfUnit(snapshot, 'shop-web')).toBe('tests-red')
    expect(snapshot.attention).toContain('shop-web: 3 failing, the baseline had 1')
  })

  test('with no baseline row for a module its failures are said, not called worse than a baseline that is not there', async () => {
    const totals = { tests: 12, failures: 3, errors: 0, skipped: 0, reports: 1 }

    expect(stateOfUplift(totals, null, true)).toBe('tests-failing')
    expect(stateOfUplift({ ...totals, failures: 0 }, null, true)).toBe('tests-green')

    const files = Object.fromEntries(Object.entries(MAVEN_UPLIFT).filter(([path]) => path !== 'analysis/shop/BASELINE.md'))
    const snapshot = await read(files)

    expect(stateOfUnit(snapshot, 'shop-web')).toBe('tests-failing')
    expect(snapshot.attention).toContain('shop-web: 3 tests failing, and the baseline has no row for it to compare with')
  })

  test('the catalog says how many deltas it holds, or its ids do', () => {
    expect(parseCatalog('into **41 distinct deltas** ranked')?.count).toBe(41)
    expect(parseCatalog('| **D01** | a |\n| **D02** | b |\nD01 again')?.count).toBe(2)
    expect(parseCatalog('| **D01** | uses `a/Foo.java:3` and `Bar.java` |\n| **D02** | b `Foo.java` |')?.byFileBase.get('foo.java')).toEqual(['D01', 'D02'])
    expect(parseCatalog('nothing here')).toBe(null)
  })

  test('paths that differ between two trees are those with another size, and those only one of them has', () => {
    const before = new Map([['a', 1], ['b', 2], ['c', 3]])
    const after = new Map([['a', 1], ['b', 5], ['d', 9]])

    expect(changedPathsOf(before, after)).toEqual(['b', 'd', 'c'])
    expect(changedPathsOf(before, before)).toEqual([])
  })

  test('only systems the workflows would accept are listed, so a name from the tree never reaches a command or a note', async () => {
    const fs = memoryFs({
      'legacy/shop/a.java': 'x',
      'legacy/my system/a.java': 'x',
      'legacy/a;rm -rf/a.java': 'x',
      'analysis/-flag/a.md': 'x',
      'analysis/billing/a.md': 'x',
      'legacy/.hidden/a.java': 'x',
    })

    expect(await systemsOf(fs)).toEqual(['billing', 'shop'])
  })

  test('a module id that is not one plain token is never put in a command', async () => {
    const files = { ...MAVEN_UPLIFT }
    const snapshot = await read(files)

    expect(snapshot.next?.text ?? '').not.toContain('$(')
  })

  test('the newest track is the one followed, and a named one is pinned', () => {
    expect(pickTrack('auto', { transformAt: 5, upliftAt: 9, reimagineAt: null })).toBe('uplift')
    expect(pickTrack('auto', { transformAt: 12, upliftAt: 9, reimagineAt: 3 })).toBe('transform')
    expect(pickTrack('auto', { transformAt: null, upliftAt: null, reimagineAt: 1 })).toBe('reimagine')
    expect(pickTrack('auto', { transformAt: null, upliftAt: null, reimagineAt: null })).toBe('transform')
    expect(pickTrack('transform', { transformAt: null, upliftAt: 9, reimagineAt: 3 })).toBe('transform')
  })
})

describe('the estate, whatever the language', () => {
  test('a PHP shop with no map and no build file is one tile per source file, and its assets and docs are not source', async () => {
    const snapshot = await read(PHP_NO_MAP)

    expect(snapshot.track).toBe('transform')
    expect(snapshot.hasAnalysis).toBe(true)
    expect(snapshot.estate?.source).toBe('tree')
    expect(snapshot.estate?.granularity).toBe('file')
    expect(snapshot.estate?.units.length).toBe(27)
    expect(snapshot.estate?.units.some(unit => unit.name === 'logo' || unit.name === 'README')).toBe(false)
    expect(snapshot.estate?.languages).toEqual([{ name: 'PHP', share: 1 }])
    expect(snapshot.next?.text).toBe(`${PREFIX}assess webshop`)

    const tiles = tilesOf(snapshot, 44, 12)

    expect(tiles.length).toBeGreaterThan(10)
    expect(new Set(tiles.map(tile => tile.domain))).toEqual(new Set(['catalog', 'includes', 'webshop']))
  })

  test('a .NET solution is one tile per project, named languages included, and its .trx report gives the module its tests', async () => {
    const snapshot = await read(DOTNET_REWRITE)

    expect(snapshot.track).toBe('transform')
    expect(snapshot.estate?.granularity).toBe('build module')
    expect(snapshot.estate?.units.map(unit => unit.name).sort()).toEqual(['Ledger.Core', 'Ledger.Web'])
    expect(snapshot.estate?.languages.map(language => language.name)).toEqual(['C#', 'VB.NET', 'ASP.NET'])

    const core = snapshot.byNode.get('Ledger.Core')

    expect(core?.tests).toEqual({ tests: 14, failures: 0, errors: 0, skipped: 0, reports: 1 })
    expect(core?.state).toBe('tests-green')
    expect(snapshot.totals.done, 'green with the notes written is done').toBe(1)
    expect(totalsOfTrx('<html/>')).toBe(null)
  })

  test('a module tested by a runner that leaves no report is read from the run the session saw', async () => {
    const before = await read(NODE_REWRITE)

    expect(before.modules.map(module => `${module.dir}:${module.state}`)).toEqual(['billing:tests-written'])

    const after = await read(NODE_REWRITE, {
      observed: new Map([['modernized/portal/billing', { tests: 9, failures: 0, errors: 0, skipped: 1, reports: 1 }]]),
    })

    expect(after.modules.map(module => `${module.dir}:${module.state}`)).toEqual(['billing:tests-green'])
    expect(after.estate?.units.map(unit => unit.name).sort()).toEqual(['auth', 'billing', 'portal', 'ui'].sort())
    expect(stateOfUnit(after, 'packages/billing')).toBe('tests-green')
  })

  test('a greenfield rebuild follows its services, and asks for acceptance tests where a service has none', async () => {
    const snapshot = await read(REIMAGINE)

    expect(snapshot.track).toBe('reimagine')
    expect(snapshot.stages.map(stage => `${stage.isDone ? '✓' : '·'}${stage.key}`)).toEqual(['·preflight', '✓spec', '✓design', '✓scaffold', '·tests', '·verify'])
    expect(snapshot.modules.map(module => `${module.dir}:${module.state}`).sort()).toEqual(['accounts:tests-green', 'billing:scaffolded'])
    expect(snapshot.attention).toContain('billing: scaffolded with no acceptance tests')
    expect(snapshot.percent, 'services are not the legacy units').toBe(null)
    expect(snapshot.next?.text).toBe(`${PREFIX}status crm`)
    expect(snapshot.estate?.languages.map(language => language.name)).toEqual(['Perl'])
  })

  test('a legacy tree that is a symbolic link is a system: the engine lists a link as `other`', async () => {
    const fs = memoryFs(LEGACY_ONLY, {}, ['legacy/ops'])

    expect((await fs.list('legacy')).map(entry => [entry.name, entry.kind])).toEqual([['ops', 'other']])
    expect(await systemsOf(fs)).toEqual(['ops'])

    const snapshot = await readSnapshot(fs, new Map(), { commandPrefix: PREFIX, nowMs: 0 })

    expect(snapshot?.system).toBe('ops')
    expect(snapshot?.estate?.languages).toEqual([{ name: 'COBOL', share: 1 }])

    // A link that leads nowhere, or to a file, is no system.
    const broken = memoryFs({ ...LEGACY_ONLY, 'legacy/note.txt': 'x' }, {}, ['legacy/note.txt'])

    expect(await systemsOf(broken)).toEqual(['ops'])
  })

  test('a legacy tree nobody has analysed is a system with an estate and nothing done', async () => {
    const snapshot = await read(LEGACY_ONLY)

    expect(snapshot.hasAnalysis).toBe(false)
    expect(snapshot.stages.every(stage => !stage.isDone)).toBe(true)
    expect(snapshot.estate?.languages).toEqual([{ name: 'COBOL', share: 1 }])
    // Nothing written yet: the front door asks what the person wants, once, and gives the first step.
    expect(snapshot.next?.text).toBe('/p:modernize ops')
    expect(snapshot.next?.isByHand).toBe(false)
  })

  test('a tree too big for a tile per file is read a directory at a time, and a lone wrapper directory is looked through', async () => {
    const estate = await discoverEstate(memoryFs(PYTHON_BIG), 'legacy/erp', 'erp')

    expect(estate?.granularity).toBe('directory')
    expect(estate?.units.map(unit => unit.name).sort()).toEqual(['pkg0', 'pkg1', 'pkg2', 'pkg3', 'pkg4', 'pkg5'])
    expect(estate?.files).toBe(620)
    expect(estate?.isPartial).toBe(false)
  })

  test('a walk that runs out of budget says so instead of pretending the sizes are whole', async () => {
    const estate = await discoverEstate(memoryFs(PYTHON_BIG), 'legacy/erp', 'erp', { dirs: 3, entries: 80_000 })

    expect(estate?.isPartial).toBe(true)
  })

  test('a baseline alone does not make a rewrite an uplift: a rewrite records the legacy behavior it must keep too', async () => {
    const snapshot = await read({ ...FULL, 'analysis/billing/BASELINE.md': '# Legacy baseline\n\nRecorded from the real program.' })

    expect(snapshot.track).toBe('transform')
    expect(snapshot.stages.map(stage => stage.key)).toContain('transform')
  })

  test('what the plain plugin writes is enough: a findings file with no marker is a finished harden step, and notes need no fixed headline', async () => {
    const snapshot = await read({ ...FULL, 'analysis/billing/SECURITY_FINDINGS.md': '# Security findings\n\n| Severity | Finding |\n|---|---|\n| High | x |\n' })

    expect(snapshot.stages.find(stage => stage.key === 'harden')?.isDone).toBe(true)
    expect(snapshot.attention.some(line => line.includes('SECURITY_FINDINGS'))).toBe(false)

    expect(readNotes('## Architecture review\nfine').hasReviewSection).toBe(true)
    expect(readNotes('## Critic findings\n- HIGH: an open endpoint, fixed').hasReviewSection).toBe(true)
    expect(readNotes('The architecture-critic subagent found two issues; both fixed.').hasReviewSection).toBe(true)
    expect(readNotes('## Mapping table\n| a | b |').hasReviewSection).toBe(false)
  })

  test('a workspace with the map uses the map for a rewrite, and the tree for an uplift', async () => {
    const mapped = await read({ ...FULL })

    expect(mapped.estate?.source).toBe('map')
    expect(mapped.estate?.measure).toBe('lines')
    expect(mapped.estate?.languages[0]?.name).toBe('COBOL')
  })
})

describe('the pane in another stack', () => {
  test('an uplift is drawn as an uplift: its stages, the modules against their baseline, and a next step it can put in the prompt', async ($, on) => {
    const world = worldOf(on, MAVEN_UPLIFT)
    mock.clock(on)
    await $.session.start(SESSION)

    const tree = await $.ui.render(PANE)
    const text = textOf(tree)

    expect(text).toContain('shop · uplift')
    expect(text).toContain('deltas')
    expect(text).toContain('baseline')
    expect(text).toContain('Java 100%')
    expect(text).toContain('matches baseline')
    expect(text).toContain('worse than baseline')
    // Two rows of modules fit: problems first, then what is finished; what is only edited so far waits behind them.
    expect(text).toContain('shop-web  worse than baseline')
    expect(text).toContain('shop-core  matches baseline')
    expect(text).not.toContain('shop-batch  changed')
    expect(text).toContain('… 1 more')
    expect(text).toContain('/code-modernization:modernize-uplift shop')
    expect(text).not.toContain('<from>')
    expect(text).not.toContain('(by hand)')
    expect(text).not.toContain('extract-rules')

    // The button puts that command in the prompt, whatever the track.
    await $.ui.press({ plugin: NAME, key: 'next' })
    expect(world.fills).toEqual(['/code-modernization:modernize-uplift shop'])
  })

  test('a rewrite in PHP with no map still draws an estate map and its legend', async ($, on) => {
    worldOf(on, PHP_NO_MAP)
    mock.clock(on)
    await $.session.start(SESSION)

    const tree = await $.ui.render(PANE)

    expect(elementsOf(tree, 'Raster').length).toBe(1)
    expect(textOf(tree)).toContain('PHP 100% · 27 files')
    expect(textOf(tree)).toContain('untouched 27')
  })

  for (const [name, files] of Object.entries({
    'a Maven uplift': MAVEN_UPLIFT,
    'a PHP shop': PHP_NO_MAP,
    'a .NET rewrite': DOTNET_REWRITE,
    'a Node monorepo': NODE_REWRITE,
    'a reimagine': REIMAGINE,
    'a legacy tree': LEGACY_ONLY,
    'the COBOL fixture': FULL,
  })) {
    test(`the pane fits its rows and columns for ${name}, tall or short, narrow or wide`, async ($, on) => {
      worldOf(on, files)
      mock.clock(on)
      await $.session.start(SESSION)

      for (const [bodyRows, bodyColumns] of [
        [44, 72],
        [30, 60],
        [20, 44],
        [12, 36],
      ] as const) {
        const input = { ...PANE, props: { ...PANE.props, bodyColumns, scroll: { offset: 0, bodyRows } } }
        const rows = rowsOf(await $.ui.render(input))

        expect(rows <= bodyRows, `fits ${bodyRows} rows at ${bodyColumns} columns (drew ${rows})`).toBe(true)
      }
    })
  }
})

describe('a workspace of several systems', () => {
  const TWO = { ...MAVEN_UPLIFT, ...PHP_NO_MAP }

  test('the pane follows one system and has a button that moves it to the next', async ($, on) => {
    worldOf(on, TWO)
    const clock = mock.clock(on)

    await $.session.start(SESSION)

    const first = textOf(await $.ui.render(PANE))

    expect(first).toContain('shop · uplift')
    expect(first).toContain('system 1/2')

    await $.ui.press({ plugin: NAME, key: 'system' })
    await clock.settle()

    const second = textOf(await $.ui.render(PANE))

    expect(second).toContain('webshop · rewrite')
    expect(second).toContain('system 2/2')
    expect(second).toContain('PHP 100%')
    expect(second).not.toContain('baseline')
  })

  test('a workspace of one system draws no such button', async ($, on) => {
    worldOf(on, MAVEN_UPLIFT)
    mock.clock(on)
    await $.session.start(SESSION)

    expect(textOf(await $.ui.render(PANE))).not.toContain('system 1/')
  })
})

describe('showing and hiding the pane', () => {
  test('a hidden pane leaves one bar with a button; pressing it shows the pane, and the pane has a button that hides it again', async ($, on) => {
    const world = worldOf(on, FULL)
    const clock = mock.clock(on)
    // The main screen, where nothing opens unasked: the pane is hidden until the person shows it.
    const band = { ...BAND, viewport: { columns: 100, rows: 45, isFullscreen: false }, props: { ...BAND.props, maxRows: 45 } }

    on('ui.render', () => ({ type: 'Text', children: ['engine'] }))
    await $.session.start(SESSION)

    const bar = await $.ui.render(band)

    expect(textOf(bar)).toContain('show pane')
    expect(textOf(bar), 'the bar says where the workspace stands').toContain('billing: analysis 5/5')

    await $.ui.press({ plugin: NAME, key: 'show-pane' })
    await clock.settle()

    expect(world.opened).toEqual([{ id: 'modernize', focus: false }])
    expect(textOf(await $.ui.render(band)), 'the bar gives the band back while the pane is up').toBe('engine')

    const pane = await $.ui.render(PANE)

    expect(elementsOf(pane, 'Button').map(button => textOf(button))).toContain('hide')

    await $.ui.press({ plugin: NAME, key: 'hide' })
    await clock.settle()

    expect(world.closed).toEqual(['modernize'])
    expect(textOf(await $.ui.render(band))).toContain('show pane')

    // Hidden by a person, it stays hidden until a person shows it: nothing reopens it unasked.
    await $.ui.render(HINT)
    await clock.advance(500)
    expect(world.opened.length).toBe(1)
  })

  test('on a terminal too narrow to dock the pane the engine holds it back: the bar stays, and pressing its button seats the pane', async ($, on) => {
    const world = worldOf(on, FULL)
    const clock = mock.clock(on)

    // Opened unasked below the width a pane docks at, the engine answers `isPlaced: false` and draws nothing.
    world.unplaced = 1
    on('ui.render', () => ({ type: 'Text', children: ['engine'] }))
    await $.session.start(SESSION)
    await $.ui.render(HINT)
    await clock.advance(200)

    expect(world.opened).toEqual([{ id: 'modernize', focus: false }])
    expect(textOf(await $.ui.render(BAND)), 'the pane is not on screen, so the bar that shows it is').toContain('show pane')

    // Nothing asks the engine again on every redraw.
    await $.ui.render(HINT)
    await clock.advance(500)
    expect(world.opened.length).toBe(1)

    // The person asks: the engine seats it at any width, and the bar gives the band back.
    await $.ui.press({ plugin: NAME, key: 'show-pane' })
    await clock.settle()
    expect(world.opened.length).toBe(2)
    expect(textOf(await $.ui.render(BAND))).toBe('engine')

    // The pane then draws, and a later /modernize-panel hides it.
    await $.ui.render(PANE)
    expect(await $.command.run(command('modernize-panel'))).toEqual({ text: 'Modernization pane hidden' })
  })

  test('/modernize-panel on a pane the engine is holding back shows it, and says why when it still cannot', async ($, on) => {
    const world = worldOf(on, FULL)
    const clock = mock.clock(on)

    world.unplaced = 1
    on('ui.render', () => ({ type: 'Text', children: ['engine'] }))
    await $.session.start(SESSION)
    await $.ui.render(HINT)
    await clock.advance(200)

    // The first command is not a "hide": there was nothing on screen to hide.
    expect(await $.command.run(command('modernize-panel'))).toEqual({ text: 'Modernization pane shown' })
  })

  test('a pane the engine will not draw says so, instead of claiming it is shown', async ($, on) => {
    const world = worldOf(on, FULL)

    mock.clock(on)
    world.unplaced = 5
    await $.session.start(SESSION)

    const answer = await $.command.run(command('modernize-panel'))

    expect(answer.text).toContain('The pane could not be shown')
    expect(answer.text).toContain('144 columns')
  })

  test('/modernize-panel is the same switch from the keyboard', async ($, on) => {
    const world = worldOf(on, FULL)

    mock.clock(on)
    await $.session.start(SESSION)

    expect(await $.command.run(command('modernize-panel'))).toEqual({ text: 'Modernization pane shown' })
    expect(await $.command.run(command('modernize-panel'))).toEqual({ text: 'Modernization pane hidden' })
    expect(world.opened.length).toBe(1)
    expect(world.closed).toEqual(['modernize'])
  })

  test('a legacy tree with nothing analysed opens nothing and draws no bar, but the command still shows the pane and its estate', async ($, on) => {
    const world = worldOf(on, LEGACY_ONLY)
    const clock = mock.clock(on)

    on('ui.render', () => ({ type: 'Text', children: ['engine'] }))
    await $.session.start(SESSION)
    await $.ui.render(HINT)
    await clock.advance(500)

    expect(world.opened).toEqual([])
    expect(textOf(await $.ui.render(BAND))).toBe('engine')
    expect(await $.command.run(command('modernize-panel'))).toEqual({ text: 'Modernization pane shown' })
    expect(textOf(await $.ui.render(PANE))).toContain('COBOL 100%')
  })
})
