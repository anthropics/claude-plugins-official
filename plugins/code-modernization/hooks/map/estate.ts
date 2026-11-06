import { estateOfTopology, languageOf, type EstateUnit } from '../reader/estate-model'
import type { ModuleState } from '../reader/modernized'
import type { Snapshot } from '../reader/progress'
import { STATE_WORDS_BY_TRACK, type TrackKey } from '../reader/tracks'
import { DEFAULT_COLOR, luma, mix, packCells, type Cell } from './raster'
import { layoutGroups, type Rect } from './treemap'

/**
 * The estate map: every unit of the legacy system as a tile, sized by its lines of code
 * (or bytes of source, where there is no map), grouped by domain or directory, coloured by
 * how far its modernization has come, and lit for a moment when a file beneath it is read or written.
 */

export type TouchKind = 'read' | 'write'

export type Touch = { atMs: number; kind: TouchKind }

export type TileState = ModuleState | 'untouched'

/** A module's verdict, as the map marks it: a tile's label starts with the mark. */
export type TileProof = 'proven' | 'partly' | 'not'

export const PROOF_MARKS: Record<TileProof, string> = { proven: '✓', partly: '±', not: '✗' }

export type Tile = {
  id: string
  name: string
  /** What the tile shows of its name: the last path segment, without its extension and without the prefix most tiles share. */
  label: string
  domain: string
  loc: number
  state: TileState
  /** What the proof says of the module, once the verify command has checked it. */
  proof?: TileProof
  rect: Rect
  isNext: boolean
}

export type Estate = {
  columns: number
  rows: number
  tiles: Tile[]
  /** Base64 for the Raster's `cells`. */
  cells: string
  /** True while any tile is still fading from a touch, so another frame is due. */
  isAnimating: boolean
}

/** How long a touch stays visible, in milliseconds. */
export const FLASH_MS = 4000

/**
 * Mid-tones on purpose: a tile has to show against a dark terminal and a light one, and the map cannot ask which it is.
 * The labels are drawn in whichever of light or dark ink reads on the tile.
 */
export const STATE_COLORS: Record<TileState, number> = {
  untouched: 0x5b6577,
  scaffolded: 0x4a6cb0,
  'tests-written': 0x94741f,
  'tests-red': 0xb23b3b,
  'tests-failing': 0xc2683a,
  'tests-green': 0x2c7a4c,
  reviewed: 0x2fa568,
  ported: 0x2b8ea6,
  switched: 0x3bd184,
}

/** What a state is called in a track: the same colors, worded for what the work is. */
export const stateWord = (track: TrackKey, state: TileState): string => STATE_WORDS_BY_TRACK[track][state] ?? state

const FLASH_COLORS: Record<TouchKind, number> = {
  read: 0x9fd4ff,
  write: 0xffe27a,
}

/** A stable small jitter per tile, so neighbours of one state still read as separate tiles. */
const jitterOf = (id: string): number => {
  let hash = 2166136261

  for (let index = 0; index < id.length; index += 1) {
    hash = Math.imul(hash ^ id.charCodeAt(index), 16777619)
  }

  return ((hash >>> 0) % 1000) / 1000
}

/** The module ids of the step the snapshot says comes next, when it is a transform. */
function nextModuleOf(snapshot: Snapshot): string | null {
  const text = snapshot.next?.text ?? ''
  const match = /transform\s+\S+\s+(\S+)/.exec(text)

  return snapshot.next?.isByHand === false ? (match?.[1] ?? null) : null
}

/**
 * Short names for tiles, which show a few letters: a path is cut to its last segment, a source file's extension goes, and
 * the prefix most of the units share (`jetty-` in `jetty-server`, `jetty-client`) goes too, so the letters that tell
 * one tile from the next are the ones drawn.
 */
export function labelsOf(names: readonly string[]): string[] {
  const stems = names.map(name => {
    const last = name.includes('/') ? (name.split('/').filter(part => part !== '').at(-1) ?? name) : name

    return languageOf(last) !== undefined ? last.replace(/\.[^.]+$/, '') : last
  })

  const counts = new Map<string, number>()

  for (const stem of stems) {
    const head = /^[^-_.\s]{2,}[-_.]/.exec(stem)?.[0]

    if (head !== undefined) {
      counts.set(head, (counts.get(head) ?? 0) + 1)
    }
  }

  const [top, count] = [...counts.entries()].sort((a, b) => b[1] - a[1])[0] ?? ['', 0]
  const isShared = top !== '' && count >= 4 && count >= names.length * 0.4

  return stems.map(stem => (isShared && stem.startsWith(top) && stem.length > top.length ? stem.slice(top.length) : stem))
}

/** The tile's proof, when its module has a fresh verdict; nothing for a module nobody has checked or that changed since. */
function proofMarkOf(snapshot: Snapshot, unitId: string): { proof: TileProof } | Record<string, never> {
  const module = snapshot.byNode.get(unitId)

  if (module === undefined || snapshot.track === 'uplift') {
    return {}
  }

  const state = snapshot.proofs.get(module.dir.toLowerCase())?.state

  return state === 'proven' || state === 'partly' || state === 'not' ? { proof: state } : {}
}

/** How many tiles carry each proof, in the order a legend draws them. */
export function proofCountsOf(tiles: readonly Tile[]): { kind: TileProof; count: number }[] {
  return (['proven', 'partly', 'not'] as const)
    .map(kind => ({ kind, count: tiles.filter(tile => tile.proof === kind).length }))
    .filter(entry => entry.count > 0)
}

/** Lays the snapshot's estate out in `columns` by `rows` cells. */
export function tilesOf(snapshot: Snapshot, columns: number, rows: number): Tile[] {
  const estate = snapshot.estate ?? (snapshot.topology !== null ? estateOfTopology(snapshot.topology, 0) : null)

  if (estate === null || columns < 4 || rows < 2) {
    return []
  }

  const next = nextModuleOf(snapshot)
  const groups = new Map<string, EstateUnit[]>()
  const short = labelsOf(estate.units.map(unit => unit.name))
  const labels = new Map(estate.units.map((unit, index) => [unit.id, short[index] ?? unit.name] as const))

  for (const unit of estate.units) {
    const members = groups.get(unit.group) ?? []

    members.push(unit)
    groups.set(unit.group, members)
  }

  const placed = layoutGroups(
    [...groups.entries()].map(([name, members]) => ({
      name,
      items: members.map(unit => ({ item: unit, size: Math.max(1, unit.size) })),
    })),
    { x: 0, y: 0, w: columns, h: rows },
  )

  return placed.flatMap(group =>
    group.items
      .filter(entry => entry.rect.w > 0 && entry.rect.h > 0)
      .map(entry => ({
        id: entry.item.id,
        name: entry.item.name,
        label: labels.get(entry.item.id) ?? entry.item.name,
        domain: group.name,
        loc: entry.item.size,
        state: snapshot.byNode.get(entry.item.id)?.state ?? ('untouched' as const),
        ...proofMarkOf(snapshot, entry.item.id),
        rect: entry.rect,
        isNext: entry.item.id === next,
      })),
  )
}

/** Paints the tiles into cells and packs them for the Raster. */
export function paint(
  tiles: readonly Tile[],
  columns: number,
  rows: number,
  touches: ReadonlyMap<string, Touch>,
  nowMs: number,
): Estate {
  const blank: Cell = { glyph: ' ', fg: DEFAULT_COLOR, bg: DEFAULT_COLOR }
  const cells: Cell[] = Array.from({ length: columns * rows }, () => blank)
  let isAnimating = false

  for (const tile of tiles) {
    const base = mix(STATE_COLORS[tile.state], 0xffffff, (jitterOf(tile.id) - 0.5) * 0.14 + 0.02)
    const touch = touches.get(tile.id)
    const age = touch !== undefined ? nowMs - touch.atMs : Infinity
    const heat = age < FLASH_MS ? 1 - age / FLASH_MS : 0

    if (heat > 0) {
      isAnimating = true
    }

    const body = heat > 0 && touch !== undefined ? mix(base, FLASH_COLORS[touch.kind], heat * 0.85) : base
    const edge = mix(body, 0x000000, 0.32)
    const ink = luma(body) > 140 ? 0x101418 : 0xf2f5f8
    const { x, y, w, h } = tile.rect
    const hasBevel = w >= 3 && h >= 2
    const label = w >= 5 && tile.proof !== undefined ? `${tile.isNext ? '▸' : ''}${PROOF_MARKS[tile.proof]}${tile.label}` : w >= 4 ? (tile.isNext ? '▸' : '') + tile.label : w >= 2 && tile.isNext ? '▸' : ''
    const shown = label.slice(0, Math.max(0, w - (hasBevel ? 1 : 0)))

    for (let row = 0; row < h; row += 1) {
      for (let col = 0; col < w; col += 1) {
        const cx = x + col
        const cy = y + row

        if (cx >= columns || cy >= rows) {
          continue
        }

        const isEdge = hasBevel && (col === w - 1 || row === h - 1)
        const glyph = row === 0 && col < shown.length ? (shown[col] ?? ' ') : ' '

        cells[cy * columns + cx] = { glyph, fg: ink, bg: isEdge ? edge : body }
      }
    }
  }

  return { columns, rows, tiles: [...tiles], cells: packCells(cells), isAnimating }
}

/** How many modules sit in each state, in the order the legend draws them. */
export function countsOf(tiles: readonly Tile[]): { state: TileState; count: number }[] {
  const order: TileState[] = [
    'untouched',
    'scaffolded',
    'tests-written',
    'tests-red',
    'tests-failing',
    'tests-green',
    'reviewed',
    'ported',
    'switched',
  ]

  return order
    .map(state => ({ state, count: tiles.filter(tile => tile.state === state).length }))
    .filter(entry => entry.count > 0)
}

/** `0x00RRGGBB` as the `#rrggbb` a `Text`'s `color` takes. */
export const hexOf = (color: number): string => `#${(color & 0xffffff).toString(16).padStart(6, '0')}`
