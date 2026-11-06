import type { EngineInterface, On, PluginOptions, ResultOf } from 'claude-code'

import { lineOf, missingPathOf, noteCall, noteDone, noteFailure, prune, subjectOf, tallyOf } from './fleet/fleet'
import type { Host, OpenResult } from './host'
import { paint, tilesOf, type TouchKind } from './map/estate'
import { absOf, baseName, isUnder, join, norm, relTo } from './paths'
import { keysOfUnit, unitOfPath } from './reader/estate-model'
import { readOrNull } from './reader/fs'
import type { TestTotals } from './reader/modernized'
import { oneLineOf, readSnapshot, REVIEWS_FILE } from './reader/progress'
import type { ReviewVerdict } from './reader/progress'
import { nodeOfFile } from './reader/topology'
import { decide, ledgerJson, ledgerMarkdown, nextUnreviewed, queueOf, undecide, type DeckScope } from './review/deck'
import { mergeLedger, parseLedger } from './review/ledger'
import { signBrief } from './sign'
import {
  newActivity,
  newState,
  PANE_ID,
  PLUGIN_NAME,
  RASTER_KEY,
  SIGN_ID,
  type FinishedCall,
  type State,
} from './state'
import { readTestRun, TEST_COMMAND } from './tests-run'
import { deckView, signView } from './views/deck'
import { headerRowsOf, legendRowsOf, nextRowsOf, paneView, planOf, showBar, type Kit } from './views/pane'
import { plain } from './text'
import { xrayOf } from './xray/xray'

const REFRESH_DEBOUNCE_MS = 450
/** While a fleet of agents is writing, a read of everything on disk is due this often, not after every call. */
const REFRESH_BUSY_MS = 2500
const FRAME_MS = 140
const CLOCK_MS = 1000
const POLL_MS = 20_000
const WRITE_TOOLS = new Set(['Edit', 'Write', 'NotebookEdit', 'MultiEdit'])
const QUIET_TOOLS = new Set(['Read', 'Glob', 'Grep', 'LS', 'WebFetch', 'WebSearch', 'TodoWrite', 'ToolSearch'])
const PARENT_TOOLS = new Set(['Agent', 'Task', 'Workflow'])
const STEP = /\/(?:[\w-]+:)?(modernize-[a-z-]+)\b[^\n]*/

const nowMs = (): number => Date.now()

/** A cell count as the engine reports it, made safe to do layout arithmetic on. */
const wholeOf = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0

/**
 * Binds a Host from `$`. Declared in this file, each member spelled
 * `$.noun.event(...)`, so the engine reads what the module calls off its source.
 */
function hostOf($: EngineInterface): Host {
  return {
    fs: {
      read: path => $.fs.read(path),
      write: (path, text) => $.fs.write(path, text),
      list: path => $.fs.list(path),
      exists: path => $.fs.exists(path),
      stat: path => $.fs.stat(path),
    },
    now: () => $.clock.now(),
    after: (ms, fn) => $.clock.after(ms, fn),
    every: (ms, fn) => $.clock.every(ms, fn),
    storeGet: key => $.store.get(key),
    storeSet: (key, value) => $.store.set(key, value),
    invalidate: () => $.ui.invalidate('ui.render'),
    blit: args => $.ui.blit(args),
    status: text => $.ui.status(text),
    toast: (text, timeoutMs) => $.ui.toast(text, timeoutMs !== undefined ? { timeoutMs } : undefined),
    log: text => $.ui.log(text),
    openPane: pane => $.ui.open(pane) as Promise<OpenResult>,
    closePane: pane => $.ui.close(pane),
    registerCommand: spec => $.command.register(spec),
    fillPrompt: input => $.prompt.fill(input),
    submitPrompt: input => $.prompt.submit(input),
    abortTurn: turnId => $.turn.abort({ turnId }),
  }
}

/**
 * `fs` with every relative path rooted at `cwd`: the artifacts live under the
 * session's working directory, wherever the process itself happens to stand.
 */
function rootedAt(fs: Host['fs'], cwd: string): Host['fs'] {
  return {
    read: path => fs.read(absOf(cwd, path)),
    write: (path, text) => fs.write(absOf(cwd, path), text),
    list: path => fs.list(absOf(cwd, path)),
    exists: path => fs.exists(absOf(cwd, path)),
    stat: path => fs.stat(absOf(cwd, path)),
  }
}

/**
 * Registers the plugin's live hooks: the pane and its estate map, x-ray
 * reads, the rule review deck, the fleet view and the sign-off dialog.
 * `session.start` binds the engine; every hook after
 * it works over that binding and one state object.
 *
 * @param on the engine's registrar
 * @param raw the plugin's options as the settings hold them
 */
export function register(on: On, raw: PluginOptions) {
  const state: State = newState(raw)

  // ---------------------------------------------------------------- reading

  async function refresh(host: Host): Promise<void> {
    if (state.isRefreshing) {
      state.isRefreshQueued = true

      return
    }

    state.isRefreshing = true

    try {
      const snapshot = await readSnapshot(host.fs, state.cache, {
        ...((state.pickedSystem ?? state.options.system) !== '' && { system: state.pickedSystem ?? state.options.system }),
        commandPrefix: state.options.commandPrefix,
        legacyDir: state.options.legacyDir,
        track: state.options.track,
        writtenUnits: state.writtenUnits,
        observed: state.observed,
        nowMs: nowMs(),
      })

      // The pane opens by itself once there is modernization to show: the first artifact under analysis/,
      // not only a legacy system that has not been touched.
      const isFirstSight = snapshot !== null && snapshot.hasAnalysis && state.snapshot?.hasAnalysis !== true

      state.snapshot = snapshot
      state.readError = null

      if (isFirstSight) {
        maybeAutoOpen()
      }

      if (snapshot !== null) {
        if (!state.deck.isOpen) {
          state.deck.ledger = snapshot.reviews
        }

        // The pane says all of this already, and so does the bar that stands where it was while it is hidden. The
        // pinned line is for a person who turned the pane off. A workspace that holds a legacy system and nothing
        // yet under analysis/ has no modernization to report.
        host.status(state.pane.isOpen || !snapshot.hasAnalysis || state.options.panel !== 'off' ? undefined : oneLineOf(snapshot))
      }

      if (state.estate !== null) {
        state.estate = { ...state.estate, tiles: [] }
      }
    } catch (error) {
      state.readError = error instanceof Error ? error.message : String(error)
    } finally {
      state.isRefreshing = false
      host.invalidate()

      if (state.isRefreshQueued) {
        state.isRefreshQueued = false
        scheduleRefresh(host)
      }
    }
  }

  function scheduleRefresh(host: Host): void {
    // A read is already due, and it will see everything written so far. Pushing it out with every call would starve
    // it for as long as agents keep writing, and the map would show nothing of a fan-out until it was over.
    if (state.timers.has('refresh')) {
      return
    }

    const isBusy = tallyOf(state.fleet, nowMs()).active >= 3

    state.timers.set(
      'refresh',
      host.after(isBusy ? REFRESH_BUSY_MS : REFRESH_DEBOUNCE_MS, () => {
        state.timers.delete('refresh')
        void refresh(host)
      }),
    )
  }

  // ------------------------------------------------------------- animation

  function frameOf(): { cells: string; isAnimating: boolean } | null {
    const estate = state.estate

    if (estate === null || state.snapshot === null) {
      return null
    }

    const painted = paint(estate.tiles, estate.columns, estate.rows, state.touches, nowMs())

    return { cells: painted.cells, isAnimating: painted.isAnimating }
  }

  function animate(host: Host): void {
    if (state.timers.has('frames') || !state.pane.isOpen) {
      return
    }

    state.timers.set(
      'frames',
      host.every(FRAME_MS, () => {
        const estate = state.estate
        const frame = frameOf()

        if (estate === null || frame === null || !state.pane.isOpen) {
          state.timers.get('frames')?.cancel()
          state.timers.delete('frames')

          return
        }

        void host
          .blit({
            requestId: PANE_ID,
            key: RASTER_KEY,
            cells: frame.cells,
            columns: estate.columns,
            rows: estate.rows,
          })
          .then(result => {
            // Said once: a refused repaint means the map is stale, which is worth knowing.
            if (result.deny !== undefined && !state.timers.has('blit-refused')) {
              state.timers.set('blit-refused', host.after(60_000, () => state.timers.delete('blit-refused')))
              host.log(`estate map: repaint refused (${result.deny})`)
            }
          })
          .catch(() => undefined)

        if (!frame.isAnimating) {
          state.timers.get('frames')?.cancel()
          state.timers.delete('frames')
        }
      }),
    )
  }

  function touch(host: Host, nodeId: string, kind: TouchKind): void {
    const held = state.touches.get(nodeId)

    // A write outranks a read that is still fading.
    if (held !== undefined && held.kind === 'write' && kind === 'read' && nowMs() - held.atMs < 1200) {
      return
    }

    state.touches.set(nodeId, { atMs: nowMs(), kind })
    animate(host)
  }

  /** The estate unit ids a tool call's paths and command text name, with how each was touched. */
  function nodesTouched(tool: string, args: Readonly<Record<string, unknown>>): { id: string; kind: TouchKind }[] {
    const snapshot = state.snapshot
    const estate = snapshot?.estate

    if (snapshot === null || estate === null || estate === undefined) {
      return []
    }

    const legacyRoot = join(state.options.legacyDir, snapshot.system)
    const modernRoot = join('modernized', snapshot.system)
    const upliftRoot = join('modernized', `${snapshot.system}-uplifted`)
    const out = new Map<string, TouchKind>()
    const kind: TouchKind = WRITE_TOOLS.has(tool) ? 'write' : 'read'

    const take = (path: string, how: TouchKind) => {
      const rel = relTo(state.cwd, path)

      if (rel === null) {
        return
      }

      if (isUnder(rel, legacyRoot) && rel !== legacyRoot) {
        const unit = unitOfPath(estate, snapshot.topology, rel.slice(legacyRoot.length + 1))

        if (unit !== null) {
          out.set(unit.id, how)
        }
      } else if (isUnder(rel, upliftRoot) && rel !== upliftRoot) {
        // An uplift's working copy has the legacy tree's own layout, so the same path names the same unit.
        const unit = unitOfPath(estate, snapshot.topology, rel.slice(upliftRoot.length + 1))

        if (unit !== null) {
          out.set(unit.id, how)

          // An edit that keeps a file's size is invisible to the size comparison; a write seen here is not.
          if (how === 'write') {
            state.writtenUnits.add(unit.id)
          }
        }
      } else if (isUnder(rel, modernRoot) && rel !== modernRoot) {
        const dir = (rel.slice(modernRoot.length + 1).split('/')[0] ?? '').toLowerCase()

        const unit = estate.units.find(candidate => keysOfUnit(candidate).some(key => key.toLowerCase() === dir))

        if (unit !== undefined) {
          out.set(unit.id, how === 'read' ? 'read' : 'write')
        }
      }
    }

    for (const key of ['file_path', 'path', 'notebook_path']) {
      const value = args[key]

      if (typeof value === 'string') {
        take(value, kind)
      }
    }

    const command = typeof args.command === 'string' ? args.command : ''

    if (command !== '') {
      const paths = command.match(/(?:\.{0,2}\/)?[\w.@~+-]+(?:\/[\w.@~+-]+)+/g) ?? []
      const writes = /(?:>|\btee\b|\bsed\s+-i|\bmv\b|\bcp\b|\brm\b|\bpatch\b|\bgit\s+(?:apply|checkout|restore))/.test(command)

      for (const path of paths.slice(0, 24)) {
        const rel = relTo(state.cwd, path) ?? ''

        take(path, writes && (isUnder(rel, modernRoot) || isUnder(rel, upliftRoot)) ? 'write' : 'read')
      }
    }

    return [...out.entries()].map(([id, how]) => ({ id, kind: how }))
  }

  /** The module a shell command's text names by path, of those the pane knows: the longest path wins. */
  function moduleOfCommand(command: string): string | null {
    const snapshot = state.snapshot

    if (snapshot === null) {
      return null
    }

    const upliftRoot = join('modernized', `${snapshot.system}-uplifted`)

    const candidates = [
      ...snapshot.modules.map(module => module.path),
      ...(snapshot.track === 'uplift'
        ? (snapshot.estate?.units ?? []).flatMap(unit => (unit.dir !== undefined && unit.dir !== '' ? [join(upliftRoot, unit.dir)] : []))
        : []),
    ].sort((a, b) => b.length - a.length)

    const escaped = (path: string) => path.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

    return (
      candidates.find(path => new RegExp(`(?:^|[\\s'"=:@])(?:\\./)?${escaped(path)}(?=[\\s/'"]|$)`).test(command)) ?? null
    )
  }

  // ------------------------------------------------------------------ deck

  async function openDeck(host: Host, scope: DeckScope, filter: string): Promise<string> {
    const snapshot = state.snapshot

    if (snapshot === null || snapshot.rules === null) {
      return 'No BUSINESS_RULES.md to review yet. Run the extract-rules command first.'
    }

    const queue = queueOf(snapshot.rules, scope, filter)

    state.deck = {
      isOpen: true,
      scope,
      filter,
      queue,
      ledger: snapshot.reviews,
      edits: new Map(),
      index: nextUnreviewed(queue, snapshot.reviews, 0),
      source: null,
      isSourceShown: false,
    }

    // The deck draws in the band above the prompt: nothing to open, only to draw.
    host.invalidate()

    return queue.length === 0
      ? 'Nothing to review under that scope.'
      : `Reviewing ${queue.length} rule${queue.length === 1 ? '' : 's'}.`
  }

  async function saveLedger(host: Host): Promise<void> {
    const system = state.snapshot?.system

    if (system === undefined) {
      return
    }

    // The review command writes this file too: what it added while the deck was open is kept, this session's decisions go on top.
    const onDisk = parseLedger(await readOrNull(host.fs, join('analysis', system, REVIEWS_FILE)))
    const merged = mergeLedger(onDisk, state.deck.edits)

    state.deck.ledger = merged
    await host.fs.write(join('analysis', system, REVIEWS_FILE), ledgerJson(system, merged))
    await host.fs.write(join('analysis', system, 'RULE_REVIEWS.md'), ledgerMarkdown(system, merged))
    scheduleRefresh(host)
  }

  async function loadSource(host: Host): Promise<void> {
    const rule = state.deck.queue[state.deck.index]
    const snapshot = state.snapshot
    const citation = rule?.citations[0]

    if (rule === undefined || snapshot === null || citation === undefined) {
      return
    }

    const legacyRoot = join(state.options.legacyDir, snapshot.system)
    const written = norm(citation.path)

    // A citation comes from a file in the analysis tree: it names a file inside the code, never a way out of it.
    if (written.startsWith('/') || /^[A-Za-z]:/.test(written) || written.split('/').includes('..')) {
      return
    }
    const viaMap = snapshot.topology !== null ? nodeOfFile(snapshot.topology, written)?.file : undefined

    const candidates = [
      written,
      join(legacyRoot, written),
      ...(viaMap !== undefined ? [join(legacyRoot, viaMap)] : []),
    ]

    for (const path of candidates) {
      const text = await readOrNull(host.fs, path)

      if (text === null) {
        continue
      }

      const lines = text.split('\n')
      // From the cited line itself: in a short band every row of lead-in costs a row of the rule's own code.
      const from = Math.max(1, citation.from)
      const to = Math.min(lines.length, Math.max(citation.to + 2, from + 11), from + 39)

      state.deck.source = {
        ruleId: rule.id,
        path,
        startLine: from,
        text: lines
          .slice(from - 1, to)
          .join('\n')
          .replace(/[^\x09\x0a\x20-\x7e -￿]/g, ' ')
          .slice(0, 9000),
      }

      return
    }

    state.deck.source = { ruleId: rule.id, path: written, startLine: citation.from, text: '(source file not found)' }
  }

  const deckActionsOf = (host: Host) => ({
    decide: (verdict: ReviewVerdict) => {
      const rule = state.deck.queue[state.deck.index]

      if (rule === undefined) {
        return
      }

      state.deck.ledger = decide(state.deck.ledger, rule, verdict, new Date(nowMs()).toISOString())
      state.deck.edits.set(rule.id, state.deck.ledger[rule.id] ?? null)
      state.deck.index = nextUnreviewed(state.deck.queue, state.deck.ledger, state.deck.index + 1)
      state.deck.isSourceShown = false
      void saveLedger(host).catch(() => undefined)
      host.invalidate()
    },
    undo: () => {
      const rule = state.deck.queue[state.deck.index]

      if (rule !== undefined) {
        state.deck.ledger = undecide(state.deck.ledger, rule.id)
        state.deck.edits.set(rule.id, null)
        void saveLedger(host).catch(() => undefined)
        host.invalidate()
      }
    },
    prev: () => {
      const size = state.deck.queue.length

      state.deck.index = size === 0 ? 0 : (state.deck.index - 1 + size) % size
      state.deck.isSourceShown = false
      host.invalidate()
    },
    next: () => {
      const size = state.deck.queue.length

      state.deck.index = size === 0 ? 0 : (state.deck.index + 1) % size
      state.deck.isSourceShown = false
      host.invalidate()
    },
    source: () => {
      state.deck.isSourceShown = !state.deck.isSourceShown

      if (state.deck.isSourceShown) {
        void loadSource(host).then(() => host.invalidate())
      }

      host.invalidate()
    },
    close: () => {
      state.deck.isOpen = false
      host.invalidate()
    },
  })

  // ------------------------------------------------------------------ sign

  async function openSign(host: Host, name = ''): Promise<string> {
    const snapshot = state.snapshot

    if (snapshot === null || snapshot.brief === null) {
      return 'There is no brief to sign yet. Run the brief command first.'
    }

    if (snapshot.brief.approval.isSigned) {
      return `The brief is already signed${snapshot.brief.approval.by !== undefined ? ` by ${snapshot.brief.approval.by}` : ''}.`
    }

    if (state.activity.isWorking) {
      return 'Wait for the running turn to finish before signing.'
    }

    state.sign = { isOpen: true, name: name !== '' ? name : state.sign.name, covers: 'phase-1', error: null }

    await host.openPane({
      id: SIGN_ID,
      title: 'Sign the brief',
      focus: true,
      closeOnEscape: true,
      holdToasts: true,
      rows: 12,
    })

    host.invalidate()

    return ''
  }

  const signActionsOf = (host: Host) => ({
    name: (value: string) => {
      state.sign.name = value
    },
    covers: (value: 'phase-1' | 'full') => {
      state.sign.covers = value
      host.invalidate()
    },
    cancel: () => {
      state.sign.isOpen = false
      void host.closePane({ id: SIGN_ID }).catch(() => undefined)
    },
    sign: () => {
      void (async () => {
        const system = state.snapshot?.system
        const name = state.sign.name.trim()

        if (system === undefined) {
          return
        }

        if (name === '') {
          state.sign.error = 'Type the approver\'s name first.'
          host.invalidate()

          return
        }

        if (state.activity.isWorking) {
          state.sign.error = 'A turn is running; sign once it has finished.'
          host.invalidate()

          return
        }

        const path = join('analysis', system, 'MODERNIZATION_BRIEF.md')
        const text = await readOrNull(host.fs, path)
        const signed = text !== null ? signBrief(text, name, new Date(nowMs()).toISOString().slice(0, 10), state.sign.covers) : null

        if (signed === null) {
          state.sign.error = 'The brief has no approval block to sign.'
          host.invalidate()

          return
        }

        await host.fs.write(path, signed)
        state.sign.isOpen = false
        await host.closePane({ id: SIGN_ID }).catch(() => undefined)
        host.log(`brief signed by ${name} (${state.sign.covers === 'full' ? 'full plan' : 'Phase 1 only'})`)
        await refresh(host)
      })()
    },
  })

  // ------------------------------------------------------------------ pane

  /**
   * Opens the pane. Opened unasked on a terminal too narrow to dock a pane, the engine holds it undrawn: it is not open to
   * the person, so the bar with the show button stays where it was, and pressing that button (the person asking) seats
   * the pane at any width.
   */
  async function openPane(host: Host): Promise<{ isPlaced: boolean; reason: string }> {
    const result: OpenResult = await host.openPane({ id: PANE_ID, title: 'Modernization' })
    const isPlaced = result === undefined || result.isPlaced !== false

    state.pane.isOpen = isPlaced
    state.pane.isWaiting = !isPlaced
    state.pane.isClosedByPerson = false
    void refresh(host)

    return { isPlaced, reason: result !== undefined && result.reason !== undefined ? result.reason : '' }
  }

  const paneActionsOf = (host: Host) => ({
    system: () => {
      const systems = state.snapshot?.systems ?? []
      const current = state.snapshot?.system

      if (systems.length < 2 || current === undefined) {
        return
      }

      // A different system is a different estate, a different brief and a different set of lit tiles.
      state.pickedSystem = systems[(systems.indexOf(current) + 1) % systems.length] ?? current
      state.touches.clear()
      state.writtenUnits.clear()
      state.estate = null
      void refresh(host)
    },
    next: () => {
      const next = state.snapshot?.next

      if (next === null || next === undefined || next.isByHand) {
        return
      }

      void host
        .fillPrompt({ text: next.text })
        .then(result => {
          if (!result.isFilled) {
            host.toast(`Next: ${next.text}`, 8000)
          }
        })
        .catch(() => undefined)
    },
    review: () => {
      void openDeck(host, 'flagged', '').catch(() => undefined)
    },
    sign: () => {
      void openSign(host)
        .then(message => {
          if (message !== '') {
            host.toast(message, 6000)
          }
        })
        .catch(() => undefined)
    },
    close: () => {
      state.pane.isOpen = false
      state.pane.isWaiting = false
      state.pane.isClosedByPerson = true
      void host.closePane({ id: PANE_ID }).catch(() => undefined)
    },
    stop: () => {
      const turnId = state.activity.turnId

      if (turnId !== null) {
        void host.abortTurn(turnId).catch(() => undefined)
      }
    },
  })

  /**
   * Opens the pane by itself once there is something to show, the person has not closed it, and
   * the layout docks panes (the fullscreen layout). What the layout is comes from whichever render
   * last said: not every build draws every site, so each render hook reports what it saw.
   */
  function maybeAutoOpen(viewport?: { columns?: number; isFullscreen?: boolean }): void {
    state.viewport.columns = viewport?.columns ?? state.viewport.columns
    state.viewport.isFullscreen = viewport?.isFullscreen ?? state.viewport.isFullscreen

    const host = state.host

    const shouldOpen =
      host !== null &&
      state.options.panel === 'auto' &&
      !state.pane.isOpen &&
      !state.pane.isWaiting &&
      !state.pane.isClosedByPerson &&
      !state.timers.has('auto-open') &&
      state.snapshot !== null &&
      state.snapshot.hasAnalysis &&
      state.viewport.isFullscreen === true

    if (shouldOpen && host !== null) {
      // Opened from a timer: a render hook only draws.
      state.timers.set(
        'auto-open',
        host.after(50, () => {
          state.timers.delete('auto-open')
          void openPane(host).catch(() => undefined)
        }),
      )
    }
  }

  // ------------------------------------------------------------- lifecycle

  on('session.start', async ($, e, next) => {
    const bound = hostOf($)
    const host: Host = { ...bound, fs: rootedAt(bound.fs, e.cwd) }

    state.host = host
    state.cwd = e.cwd

    for (const timer of state.timers.values()) {
      timer.cancel()
    }

    state.timers.clear()

    await Promise.all([
      host
        .registerCommand({
          name: 'modernize-panel',
          description: 'Show or hide the modernization progress pane and estate map',
          argumentHint: '[open|close|json]',
          immediate: true,
        })
        .catch(() => undefined),
      host
        .registerCommand({
          name: 'modernize-review-pane',
          description: 'Review business rules one card at a time in the pane: confirm, wrong, or discuss',
          argumentHint: '[flagged|p0|all] [filter]',
        })
        .catch(() => undefined),
      host
        .registerCommand({
          name: 'modernize-sign',
          description: 'Sign the modernization brief\'s approval block (a person\'s action)',
          argumentHint: '[approver name, role]',
        })
        .catch(() => undefined),
    ])

    await refresh(host)

    state.timers.set(
      'clock',
      host.every(CLOCK_MS, () => {
        if (state.pane.isOpen && (state.activity.isWorking || state.activity.running.size > 0)) {
          host.invalidate()
        }
      }),
    )

    state.timers.set(
      'poll',
      host.every(POLL_MS, () => {
        if (state.pane.isOpen && !state.activity.isWorking) {
          scheduleRefresh(host)
        }
      }),
    )

    return next(e)
  })

  on('ui.render', { component: 'PromptHint' }, ($, e, next) => {
    if (e.surface === 'terminal') {
      maybeAutoOpen(e.viewport)
    }

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, ($, e, next) => {
    const host = state.host

    if (e.surface === 'terminal') {
      // Not every build reports `isFullscreen`. The band's `maxRows` tells the same fact: under the
      // fullscreen layout it is what the bottom slot has left; otherwise it is the terminal's height.
      const rows = e.viewport?.rows
      const inferred = rows !== undefined && e.props.maxRows > 0 ? e.props.maxRows < rows : undefined

      maybeAutoOpen({
        ...(e.viewport?.columns !== undefined && { columns: e.viewport.columns }),
        ...((e.viewport?.isFullscreen ?? inferred) !== undefined && {
          isFullscreen: e.viewport?.isFullscreen ?? inferred,
        }),
      })
    }

    // A survey holds the band first; the deck waits behind it.
    if (host === null || e.props.hasSurvey || e.surface !== 'terminal') {
      return next(e)
    }

    const table = $.ui.resolve(e)

    // With no deck open, a hidden pane leaves one row and a button to bring it back: the pane is
    // always one press away, on a terminal too narrow to open it unasked as well as on a wide one.
    if (!state.deck.isOpen) {
      const snapshot = state.snapshot

      if (state.options.panel === 'off' || state.pane.isOpen || snapshot === null || !snapshot.hasAnalysis) {
        return next(e)
      }

      return showBar(
        { Box: table.Box, Text: table.Text, Button: table.Button },
        oneLineOf(snapshot),
        e.props.bodyColumns,
        () => {
          void openPane(host)
            .then(result => {
              if (!result.isPlaced) {
                host.toast(`The pane could not be shown: ${result.reason}`, 8000)
              }
            })
            .catch(() => undefined)
        },
      )
    }

    return deckView(
      { Box: table.Box, Text: table.Text, Button: table.Button, Code: table.Code },
      state.deck,
      e.props.bodyColumns,
      e.props.maxRows,
      deckActionsOf(host),
    )
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    const host = state.host

    if (host === null || (e.requestId !== PANE_ID && e.requestId !== SIGN_ID)) {
      return next(e)
    }

    const table = $.ui.resolve(e)
    const kit: Kit = {
      Box: table.Box,
      Text: table.Text,
      Button: table.Button,
      ...('Raster' in table && { Raster: table.Raster }),
      ...('Code' in table && { Code: table.Code }),
      ...('Input' in table && { Input: table.Input }),
      ...('Select' in table && { Select: table.Select }),
    }

    const columns = Math.max(24, wholeOf(e.props.bodyColumns) - 1)

    if (e.requestId === SIGN_ID) {
      return signView(
        kit,
        state.sign,
        state.snapshot?.system ?? '',
        state.snapshot?.brief?.openQuestions ?? 0,
        columns,
        signActionsOf(host),
      )
    }

    // A squeezed pane (a dialog or another panel has its rows) can report a body of no rows at all.
    const rows = wholeOf(e.props.scroll.bodyRows)

    state.pane.isOpen = true
    state.pane.isWaiting = false
    state.pane.bodyColumns = columns
    state.pane.bodyRows = rows
    state.pane.placement = e.props.placement

    const snapshot = state.snapshot

    const plan = planOf(rows, e.props.placement, {
      phases: snapshot?.brief?.phases.length ?? 0,
      modules: snapshot?.modules.length ?? 0,
      attention:
        (snapshot?.attention.length ?? 0) +
        [...state.fleet.signatures.values()].filter(signature => signature.agents.size >= 3).length,
      hasMap: snapshot !== null && snapshot.estate !== null && kit.Raster !== undefined,
      headerRows: headerRowsOf(snapshot, columns),
      nextRows: nextRowsOf(snapshot, state, columns),
      legendRows: legendRowsOf(snapshot, columns),
    })

    let estate: { cells: string; columns: number; rows: number; tiles: State['estate'] extends infer T ? (T extends { tiles: infer U } ? U : never) : never } | null = null

    // The plan sheds the map first when the body is too short; a Raster of no rows is refused.
    if (snapshot !== null && snapshot.estate !== null && kit.Raster !== undefined && plan.estate >= 1 && columns >= 1) {
      const mapRows = Math.min(256, plan.estate)
      const held = state.estate

      const tiles =
        held !== null && held.columns === columns && held.rows === mapRows && held.tiles.length > 0
          ? held.tiles
          : tilesOf(snapshot, columns, mapRows)

      state.estate = { tiles, columns, rows: mapRows, isMounted: true }

      const painted = paint(tiles, columns, mapRows, state.touches, nowMs())

      estate = { cells: painted.cells, columns, rows: mapRows, tiles }

      if (painted.isAnimating) {
        animate(host)
      }
    } else {
      // No map drawn: nothing for the frame timer to repaint.
      state.estate = null
    }

    return paneView(
      kit,
      state,
      { columns, rows, placement: e.props.placement, nowMs: nowMs(), estate, plan },
      paneActionsOf(host),
    )
  })

  on('ui.close', async ($, e, next) => {
    const result = await next(e)

    if (result.deny !== undefined) {
      return result
    }

    if (e.id === PANE_ID) {
      state.pane.isOpen = false
      state.pane.isWaiting = false
      state.pane.isClosedByPerson = e.origin.kind === 'person' || state.pane.isClosedByPerson

      if (state.estate !== null) {
        state.estate.isMounted = false
      }
    } else if (e.id === SIGN_ID) {
      state.sign.isOpen = false
    }

    return result
  })

  // -------------------------------------------------------------- commands

  on('command.run', { command: 'modernize-panel' }, async ($, e, next) => {
    const host = state.host

    if (host === null) {
      return next(e)
    }

    state.viewport.isFullscreen = e.presentation.isFullscreen
    state.viewport.columns = e.presentation.columns

    const arg = e.args.trim().toLowerCase()

    if (arg === 'json') {
      await refresh(host)

      const snapshot = state.snapshot

      return {
        text:
          snapshot === null
            ? 'no system under analysis/'
            : `\`\`\`json\n${JSON.stringify(
                {
                  system: snapshot.system,
                  stages: snapshot.stages.map(stage => ({ key: stage.key, done: stage.isDone, detail: stage.detail })),
                  brief: snapshot.brief && {
                    target: snapshot.brief.target,
                    approval: snapshot.brief.approval,
                    phases: snapshot.brief.phases.map(phase => ({
                      number: phase.number,
                      title: phase.title,
                      size: phase.size,
                      modules: phase.modules,
                      criteria: phase.criteria.length,
                      ticked: phase.criteria.filter(criterion => criterion.isTicked).length,
                    })),
                  },
                  modules: snapshot.modules.map(module => ({
                    dir: module.dir,
                    state: module.state,
                    tests: module.tests,
                    reviewDate: module.reviewDate,
                  })),
                  proof:
                    snapshot.verification === null
                      ? null
                      : {
                          overall: snapshot.verification.overall,
                          modules: [...snapshot.proofs].map(([name, proof]) => ({ name, state: proof.state, verdict: proof.verdict ?? null, reason: proof.reason })),
                        },
                  totals: snapshot.totals,
                  percent: snapshot.percent,
                  attention: snapshot.attention,
                  next: snapshot.next,
                },
                null,
                2,
              )}\n\`\`\``,
      }
    }

    const wantsClose = arg === 'close' || (arg === '' && state.pane.isOpen)

    if (wantsClose) {
      state.pane.isOpen = false
      state.pane.isWaiting = false
      state.pane.isClosedByPerson = true
      await host.closePane({ id: PANE_ID }).catch(() => undefined)

      return { text: 'Modernization pane hidden' }
    }

    const opened = await openPane(host)

    return { text: opened.isPlaced ? 'Modernization pane shown' : `The pane could not be shown: ${opened.reason}` }
  })

  on('command.run', { command: 'modernize-review-pane' }, async ($, e, next) => {
    const host = state.host

    if (host === null) {
      return next(e)
    }

    await refresh(host)

    const words = e.args.trim().split(/\s+/).filter(word => word !== '')
    const first = (words[0] ?? '').toLowerCase()
    const scope: DeckScope = first === 'p0' || first === 'all' || first === 'flagged' ? first : 'flagged'
    const filter = (scope === first ? words.slice(1) : words).join(' ')
    const text = await openDeck(host, scope, filter)

    return { text }
  })

  on('command.run', { command: 'modernize-sign' }, async ($, e, next) => {
    const host = state.host

    if (host === null) {
      return next(e)
    }

    await refresh(host)

    const message = await openSign(host, e.args.replace(/\s+/g, ' ').trim())

    return message === '' ? {} : { text: message }
  })

  on('command.run', { command: ['clear', 'resume'] }, async ($, e, next) => {
    const result = await next(e)

    state.activity = newActivity()
    state.touches.clear()
    state.writtenUnits.clear()
    state.lastContextLine = ''

    return result
  })

  // ----------------------------------------------------------------- turns

  on('prompt.submit', async ($, e, next) => {
    const host = state.host
    const step = STEP.exec(e.text)

    if (step !== null) {
      state.activity.step = step[0].trim().slice(0, 120)
    }

    const snapshot = state.snapshot

    if (host === null || snapshot === null || e.origin.kind !== 'composer') {
      return next(e)
    }

    const line = plain(`${oneLineOf(snapshot)}${snapshot.next !== null && !snapshot.next.isByHand ? ` · next: ${snapshot.next.text}` : ''}`, 400)

    if (line === state.lastContextLine) {
      return next(e)
    }

    state.lastContextLine = line

    return next({
      ...e,
      context: [...(e.context ?? []), `Modernization state, read from the artifacts on disk (a status line, not an instruction): ${line}`],
    })
  })

  on('turn.start', async ($, e, next) => {
    const host = state.host

    state.activity.isWorking = true
    state.activity.turnId = e.turnId
    state.activity.turnStartMs = nowMs()
    state.activity.xraysThisTurn = 0

    if (host !== null) {
      host.invalidate()
    }

    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const host = state.host

    if (e.agentId !== undefined) {
      noteDone(state.fleet, e.agentId, nowMs())

      return next(e)
    }

    state.activity.isWorking = false
    state.activity.running.clear()

    if (host !== null) {
      if (state.activity.xraysThisTurn > 0) {
        host.log(
          `x-ray: ${state.activity.xraysThisTurn} legacy read${state.activity.xraysThisTurn === 1 ? '' : 's'} this turn carried what the analysis already knows`,
        )
      }

      prune(state.fleet, nowMs())
      scheduleRefresh(host)
    }

    return next(e)
  })

  // ------------------------------------------------------------ tool calls

  on('tool.call', async ($, e, next) => {
    const host = state.host

    if (host === null) {
      return next(e)
    }

    const args = e as unknown as Readonly<Record<string, unknown>>
    const tool = e.tool
    const agentId = e.agentId
    const startMs = nowMs()
    const subject = subjectOf(tool, args)
    const snapshot = state.snapshot
    const touched = nodesTouched(tool, args)

    for (const entry of touched) {
      touch(host, entry.id, entry.kind)
    }

    if (agentId !== undefined) {
      const unit = touched[0] !== undefined ? snapshot?.estate?.units.find(candidate => candidate.id === touched[0]?.id)?.name : undefined

      noteCall(state.fleet, agentId, tool, subject, startMs, unit)
    }

    state.activity.running.set(e.tool_use_id, {
      id: e.tool_use_id,
      tool,
      subject,
      startMs,
      ...(agentId !== undefined && { agentId }),
    })

    const path = typeof args.file_path === 'string' ? args.file_path : typeof args.notebook_path === 'string' ? args.notebook_path : undefined
    const rel = path !== undefined ? relTo(state.cwd, path) : null

    let result: ResultOf['tool.call'] | undefined
    let note: string | undefined

    try {
      result = await next(e)

      if (result.deny !== undefined) {
        return result
      }

      const extra: string[] = []
      const isError = result.isError === true
      const text = typeof result.text === 'string' ? result.text : ''

      if (isError && agentId !== undefined) {
        // What the call was aimed at is half of the cause: the path as the agent gave it, else the command's head.
        const missing = missingPathOf(text)
        const example = rel ?? (missing !== undefined ? (relTo(state.cwd, missing) ?? missing) : subject)
        const signature = noteFailure(state.fleet, agentId, text, nowMs(), example)

        if (signature !== null) {
          const line = lineOf(signature)

          host.toast(`Fleet: ${line}`, 9000)
          host.log(`fleet: ${line}. One cause across agents usually belongs in the playbook, not in each agent.`)
        }
      }

      if (tool === 'Read' && !isError && state.options.isXrayOn && snapshot !== null && rel !== null) {
        const legacyRoot = join(state.options.legacyDir, snapshot.system)

        if (isUnder(rel, legacyRoot) && rel !== legacyRoot) {
          const xray = xrayOf(snapshot, {
            fileRel: rel.slice(legacyRoot.length + 1),
            ...(typeof args.offset === 'number' && { offset: args.offset }),
            ...(typeof args.limit === 'number' && { limit: args.limit }),
          })

          if (xray !== null) {
            extra.push(xray.text)
            note = xray.summary.replace(/^x-ray [^:]+: /, 'x-ray ')
            state.activity.xrays += 1

            if (agentId === undefined) {
              state.activity.xraysThisTurn += 1
            }
          }
        }
      }

      // A citation in the analysis is relative to the legacy system's root, and an agent handed one
      // often reads it from the workspace root. Say where the file is rather than let it search.
      if (tool === 'Read' && isError && state.options.isXrayOn && snapshot !== null && rel !== null && /does not exist/i.test(text)) {
        const legacyRoot = join(state.options.legacyDir, snapshot.system)
        const candidate = join(legacyRoot, rel)

        // Only a plain path is echoed back: the note is read by the model, and a name is text from the legacy tree.
        if (plain(rel, 300) === rel && !isUnder(rel, state.options.legacyDir) && (await host.fs.exists(candidate))) {
          extra.push(
            `There is no ${rel} in the workspace, but ${candidate} exists. Paths cited under analysis/${snapshot.system}/ are relative to ${legacyRoot}/.`,
          )
          note = 'x-ray: the path exists under the legacy root'
        }
      }

      if ((tool === 'Bash' || tool === 'PowerShell') && typeof args.command === 'string' && TEST_COMMAND.test(args.command)) {
        const run = readTestRun(text)

        if (run !== null) {
          note = `${run.executed} executed${run.skipped > 0 ? `, ${run.skipped} skipped` : ''}${run.failed > 0 ? `, ${run.failed} failed` : ''}`

          // A run in a module's own directory is its result even where its runner left no report file behind.
          const home = moduleOfCommand(args.command)

          if (home !== null && run.executed + run.skipped > 0) {
            const seen: TestTotals = { tests: run.executed + run.skipped, failures: run.failed, errors: 0, skipped: run.skipped, reports: 1 }

            state.observed.set(home, seen)
          }
        }
      }

      return extra.length > 0 ? { ...result, context: [...(result.context ?? []), ...extra] } : result
    } finally {
      const ms = nowMs() - startMs

      state.activity.running.delete(e.tool_use_id)

      if (agentId === undefined) {
        const finished: FinishedCall = {
          tool,
          subject,
          isOk: result !== undefined && result.deny === undefined && result.isError !== true,
          ms,
          ...(note !== undefined && { note }),
        }

        state.activity.finished = [...state.activity.finished, finished].slice(-8)
      }

      if (!QUIET_TOOLS.has(tool) || tool === 'Read') {
        const wrote = WRITE_TOOLS.has(tool) || tool === 'Bash' || tool === 'PowerShell' || PARENT_TOOLS.has(tool)

        if (wrote) {
          // A write may have changed the working copy: the next read lists it afresh.
          for (const key of [...state.cache.keys()]) {
            if (key.startsWith('changed:')) {
              state.cache.delete(key)
            }
          }

          scheduleRefresh(host)
        } else if (state.pane.isOpen) {
          host.invalidate()
        }
      }
    }
  })
}

export { PLUGIN_NAME }
