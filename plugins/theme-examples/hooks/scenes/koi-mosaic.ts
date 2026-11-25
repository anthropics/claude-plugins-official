// Koi Mosaic: a koi pond seen from above. The koi are tile mosaics that swim a whole cell per step down one side of the pond and up the other;
// their stepped shadows lie down and right of them on the floor. Same family: square tiles on a cell grid, a quiet glyph in each tile.
// Pure string building: no DOM, nothing read from outside this file.

const CELL = 20
const COLUMNS = 80
const ROWS = 50

type Cell = { x: number; y: number; kind: string }
type Tile = { across: number; kind: string }
type Step = { x: number; y: number }
type Paint = { tile: string; glyph: string; glyphOpacity: number; glyphs: string }
type Seed = { x: number; y: number; tone: string }
type Point = readonly [number, number]

/** A deterministic 0..1 value for a cell, so every build is the same. */
function hashOf(x: number, y: number, salt: number): number {
  let h = Math.imul(x + 11, 374761393) ^ Math.imul(y + 7, 668265263) ^ Math.imul(salt + 3, 1274126177)
  h = Math.imul(h ^ (h >>> 13), 1274126177)
  h = h ^ (h >>> 16)
  return (h >>> 0) / 4294967296
}

function tileAt(x: number, y: number): string {
  return `M${x * CELL + 1} ${y * CELL + 1}h18v18h-18z`
}

/** Whole cells in one path, each row's neighbours joined into one rectangle to keep the string short. */
function blocksOf(keys: Iterable<string>, size: number): string {
  const rows = new Map<number, number[]>()
  for (const key of keys) {
    const parts = key.split(',').map(Number)
    const x = parts[0] ?? 0
    const y = parts[1] ?? 0
    const list = rows.get(y) ?? []
    list.push(x)
    rows.set(y, list)
  }
  let d = ''
  for (const [y, list] of rows) {
    list.sort((a, b) => a - b)
    let from = list[0] ?? 0
    for (let i = 1; i <= list.length; i += 1) {
      const previous = list[i - 1] ?? 0
      const current = list[i]
      if (current === previous + 1) continue
      const width = (previous - from + 1) * size
      d += `M${from * size} ${y * size}h${width}v${size}h-${width}z`
      from = current ?? 0
    }
  }
  return d
}

/** Tile kinds: what a cell letter paints. */
const KINDS: Record<string, Paint> = {
  // lily pad greens: main, vein, rim
  a: { tile: '#2f8552', glyph: '#8fd09f', glyphOpacity: 0.5, glyphs: 'o:o;' },
  b: { tile: '#57b56f', glyph: '#1f6b45', glyphOpacity: 0.3, glyphs: ':;o' },
  c: { tile: '#267a50', glyph: '#8fd09f', glyphOpacity: 0.25, glyphs: ':;' },
  // bloom: petals and heart
  p: { tile: '#edb4cc', glyph: '#ffffff', glyphOpacity: 0.7, glyphs: 'o' },
  q: { tile: '#eec25a', glyph: '#d9a93a', glyphOpacity: 0.8, glyphs: '*' },
  // pond-edge stones: warm grey-beige, the scene's one warm neutral
  s: { tile: '#c9bf9a', glyph: '#6f8378', glyphOpacity: 0, glyphs: ':.;.' },
  t: { tile: '#8ea398', glyph: '#64796e', glyphOpacity: 0.4, glyphs: '.:;' },
  u: { tile: '#d9cfa8', glyph: '#7d9085', glyphOpacity: 0, glyphs: '.;:.' },
  v: { tile: '#7d968c', glyph: '#b9c8bd', glyphOpacity: 0.35, glyphs: ':.' },
}

/** Koi tile colours by map letter, three shades each so the fish looks made of tesserae; they become CSS classes so each slice stays short. */
const KOI_FILLS: Record<string, readonly string[]> = {
  O: ['#ec7c3c', '#e06c2e', '#d55f25'],
  W: ['#f5f1e6', '#ece7d9', '#f8f5ec'],
  C: ['#d14a3a', '#c03d2e', '#d85544'],
  K: ['#48545b', '#3b464c', '#55626b'],
  E: ['#26343c', '#26343c', '#26343c'],
  f: ['#f5f1e6', '#ece7d9', '#f8f5ec'],
  t: ['#f5f1e6', '#ece7d9', '#f8f5ec'],
  T: ['#f5f1e6', '#ece7d9', '#f8f5ec'],
}
const KOI_OPACITY: Record<string, number> = { f: 0.85, t: 0.74, T: 0.95 }

/** Which tiles carry which glyph class: light glyphs on the coloured tiles, quiet ones on the cream tiles. */
const GLYPH_CLASSES: ReadonlyArray<{ className: string; kinds: string }> = [
  { className: 'kg', kinds: 'OCK' },
  { className: 'kw', kinds: 'WT' },
]

/** One koi heading left: a column of the map is one slice across the body. */
const KOHAKU_BODY = `
....ff..............
...fff..............
..WOOO..............
.EOOOOOWWW..........
WOOOOOOWWWOOOWW.....
WWOOOOOWWOOOOOW.....
WOOOOOWWWWOOOWW.....
.EWOOOOWWW..........
..WWWO..............
...fff..............
....ff..............
`
const TANCHO_BODY = `
....ff..............
...fff..............
..WWWW..............
.EWWWWKKWW..........
WWCWWWKKKWWWWWW.....
WCCCWWWKWWWKKWW.....
WWCWWWWWWWKKWWW.....
.EWWWWWWWW..........
..WWWW..............
...fff..............
....ff..............
`
/** The tail fan, swept to either side: T is solid, t its translucent edge. */
const TAIL_UP = `
....................
..................Tt
................TTTt
................TTT.
...............TTTT.
...............TTTTt
...............TTT..
....................
....................
....................
....................
`
const TAIL_DOWN = `
....................
....................
....................
....................
...............TTT..
...............TTTTt
...............TTTT.
................TTT.
................TTTt
..................Tt
....................
`

/** The koi's two lanes: down the right side, then up the left. Each ends well outside the canvas, so the jump between them is never seen. */
const RIGHT_LANE: readonly Point[] = [[70, -6], [69, 14], [69, 30], [64, 56]]
const LEFT_LANE: readonly Point[] = [[9, 56], [11, 36], [10, 18], [12, -6]]

/** A wake beside each lane: the step it sits at, and how far to the side. */
const WAKES: readonly Point[] = [[40, 5], [82, -4]]

/** The four rings' fades, in percent of the period and opacity. Never more than two rings show at once. */
const RING_TRACKS: ReadonlyArray<readonly Point[]> = [
  [[0, 0], [2, 0.16], [6, 0.12], [12, 0.06], [18, 0]],
  [[0, 0], [9, 0.15], [15, 0.11], [21, 0.06], [27, 0]],
  [[0, 0], [18, 0.13], [24, 0.09], [30, 0.05], [36, 0]],
  [[0, 0], [27, 0.11], [33, 0.08], [39, 0.04], [45, 0]],
]

function linesOf(map: string): string[] {
  return map.split('\n').filter(line => line.length > 0)
}

/** Slices of a koi map: for each column, the tiles across the body, counted from the spine. */
function slicesOf(map: string): Tile[][] {
  const lines = linesOf(map)
  const spine = (lines.length - 1) / 2
  const slices: Tile[][] = []
  const length = (lines[0] ?? '').length
  for (let k = 0; k < length; k += 1) {
    const tiles: Tile[] = []
    for (let row = 0; row < lines.length; row += 1) {
      const kind = (lines[row] ?? '')[k]
      if (kind !== undefined && kind !== '.') tiles.push({ across: row - spine, kind })
    }
    slices.push(tiles)
  }
  return slices
}

/** One lane of the swim, a row per step: a slow line through the given points plus a weave of two cells, so the body, which follows the head cell by cell, is always in an S. */
function walkLane(points: readonly Point[]): Step[] {
  const steps: Step[] = []
  for (let i = 0; i + 1 < points.length; i += 1) {
    const from = points[i]
    const to = points[i + 1]
    if (from === undefined || to === undefined) continue
    const count = Math.abs(to[1] - from[1])
    for (let n = 0; n < count; n += 1) {
      const y = from[1] + Math.sign(to[1] - from[1]) * n
      const weave = 1.9 * Math.sin(((y - 8) * 2 * Math.PI) / 21)
      steps.push({ x: Math.round(from[0] + ((to[0] - from[0]) * n) / count + weave), y })
    }
  }
  return steps
}

function placeAt(steps: readonly Step[], index: number): Step {
  const i = ((index % steps.length) + steps.length) % steps.length
  const step = steps[i] ?? { x: 0, y: 0 }
  return { x: step.x * CELL + 10, y: step.y * CELL + 10 }
}

/** The head's place, one keyframe per step, gliding in a line from each to the next. Where the next place is more than a cell away (the jump from one lane's end to the other's start, off the canvas) the keyframe holds and then jumps, so nothing is seen flying across. */
function swimKeyframes(name: string, steps: readonly Step[]): string {
  let out = `@keyframes ${name}{`
  for (let i = 0; i <= steps.length; i += 1) {
    const place = placeAt(steps, i)
    const next = placeAt(steps, i + 1)
    const jumps = i < steps.length && Math.abs(next.x - place.x) + Math.abs(next.y - place.y) > 2 * CELL
    const percent = i === steps.length ? '100' : ((i * 100) / steps.length).toFixed(3).replace(/\.?0+$/, '')
    out += `${percent}%{transform:translate(${place.x}px,${place.y}px)${jumps ? ';animation-timing-function:step-end' : ''}}`
  }
  return `${out}}`
}

/** The tiles of one slice, laid across x: one path per shade, then one row of glyphs per glyph class. */
function sliceTiles(tiles: readonly Tile[], sliceIndex: number): string {
  const byShade = new Map<string, string>()
  for (const tile of tiles) {
    const shade = tile.kind + Math.floor(hashOf(sliceIndex, tile.across + 9, 61) * 3)
    byShade.set(shade, (byShade.get(shade) ?? '') + `M${tile.across * CELL - 9} -9h18v18h-18z`)
  }
  let out = ''
  for (const [shade, d] of byShade) out += `<path class="k${shade}" d="${d}"/>`
  for (const glyphClass of GLYPH_CLASSES) {
    const marked = tiles.filter(tile => glyphClass.kinds.includes(tile.kind))
    if (marked.length === 0) continue
    const glyphs = marked.map(tile => 'S%t:$;tS'[Math.floor(hashOf(sliceIndex, tile.across + 9, 62) * 8)] ?? '').join('')
    out += `<text class="${glyphClass.className}" x="${marked.map(tile => tile.across * CELL).join(' ')}" y="4.5">${glyphs}</text>`
  }
  return out
}

/** The same slice in plain blocks, for the shadow on the floor. */
function sliceShadow(tiles: readonly Tile[]): string {
  const list = tiles.map(tile => tile.across).sort((a, b) => a - b)
  let out = ''
  let from = list[0] ?? 0
  for (let i = 1; i <= list.length; i += 1) {
    const previous = list[i - 1] ?? 0
    const current = list[i]
    if (current === previous + 1) continue
    out += `M${from * CELL - 10} -10h${(previous - from + 1) * CELL}v20h-${(previous - from + 1) * CELL}z`
    from = current ?? 0
  }
  return `<path d="${out}"/>`
}

function paintSlice(tiles: readonly Tile[], sliceIndex: number, shadow: boolean): string {
  if (tiles.length === 0) return ''
  return shadow ? sliceShadow(tiles) : sliceTiles(tiles, sliceIndex)
}

/** A koi is a train of slices that all follow the head's keyframes, each one step later: the body bends along its path. */
function koi(bodyMap: string, steps: readonly Step[], seconds: number, startStep: number, shadow: boolean): string {
  const body = slicesOf(bodyMap)
  const tailUp = slicesOf(TAIL_UP)
  const tailDown = slicesOf(TAIL_DOWN)
  const stepSeconds = seconds / steps.length
  let out = ''
  for (let k = body.length - 1; k >= 0; k -= 1) {
    const place = placeAt(steps, startStep - k)
    const up = tailUp[k] ?? []
    const down = tailDown[k] ?? []
    let inner = paintSlice(body[k] ?? [], k, shadow)
    if (up.length > 0 || down.length > 0) {
      inner += `<g class="poseA">${paintSlice(up, k, shadow)}</g><g class="poseB">${paintSlice(down, k, shadow)}</g>`
    }
    out += `<g class="swim" transform="translate(${place.x} ${place.y})" style="animation-delay:-${((startStep - k) * stepSeconds).toFixed(2)}s">${inner}</g>`
  }
  return out
}

/** Both koi in one layer: the fish themselves, or (for a shade layer) their plain shadows. */
function fishLayer(steps: readonly Step[], seconds: number, kohakuStart: number, tanchoStart: number, className: string, attributes: string): string {
  const shadow = className !== 'fish'
  return `<g class="${className}"${attributes}>${koi(KOHAKU_BODY, steps, seconds, kohakuStart, shadow)}${koi(TANCHO_BODY, steps, seconds, tanchoStart, shadow)}</g>`
}

/** Tiles of one kind in a single path; glyphs in one text per row with a per-glyph x list. */
function mosaic(cells: readonly Cell[]): string {
  const byKind = new Map<string, Cell[]>()
  for (const cell of cells) {
    const list = byKind.get(cell.kind) ?? []
    list.push(cell)
    byKind.set(cell.kind, list)
  }
  let out = ''
  for (const [kind, list] of byKind) {
    const paint = KINDS[kind]
    if (paint === undefined) continue
    out += `<path d="${list.map(c => tileAt(c.x, c.y)).join('')}" fill="${paint.tile}" stroke="#fff" stroke-opacity="0.22"/>`
    const rows = new Map<number, Cell[]>()
    for (const c of list) {
      const row = rows.get(c.y) ?? []
      row.push(c)
      rows.set(c.y, row)
    }
    for (const [y, row] of rows) {
      const xs = row.map(c => c.x * CELL + 10).join(' ')
      const text = row.map(c => paint.glyphs[Math.floor(hashOf(c.x, c.y, 5) * paint.glyphs.length)] ?? '').join('')
      out += `<text x="${xs}" y="${y * CELL + 14.5}" fill="${paint.glyph}" opacity="${paint.glyphOpacity}">${text}</text>`
    }
  }
  return out
}

/** Darker water around a thing: its footprint grown by `reach` cells, moved by (shiftX, shiftY) cells, on the grid so the edge steps. */
function halo(cells: readonly Cell[], reach: number, shiftX: number, shiftY: number, opacity: number): string {
  const seen = new Set<string>()
  for (const c of cells) {
    for (let dx = -reach; dx <= reach; dx += 1) {
      for (let dy = -reach; dy <= reach; dy += 1) {
        if (Math.abs(dx) + Math.abs(dy) > reach + (reach > 1 ? 1 : 0)) continue
        seen.add(`${c.x + dx + shiftX},${c.y + dy + shiftY}`)
      }
    }
  }
  return `<path d="${blocksOf(seen, CELL)}" fill="#0d5a66" opacity="${opacity}"/>`
}

/** A lily pad: a round cluster of green tiles with one notch cut to the middle, darker at the rim, a ring of light veins on the larger ones. */
function lilyPad(centerX: number, centerY: number, radius: number, notchDegrees: number, bloom: Point | null): Cell[] {
  const cells: Cell[] = []
  const notch = (notchDegrees * Math.PI) / 180
  const reach = Math.ceil(radius)
  for (let dy = -reach; dy <= reach; dy += 1) {
    for (let dx = -reach; dx <= reach; dx += 1) {
      const distance = Math.hypot(dx, dy)
      if (distance > radius) continue
      let off = Math.atan2(dy, dx) - notch
      while (off > Math.PI) off -= 2 * Math.PI
      while (off < -Math.PI) off += 2 * Math.PI
      if (distance > 0.6 && Math.abs(off) < 0.24 + 0.28 / Math.max(distance, 1)) continue
      const x = centerX + dx
      const y = centerY + dy
      let kind = 'a'
      if (distance > radius - 0.85) kind = 'c'
      else if (radius > 3 && Math.abs(distance - radius * 0.5) < 0.5) kind = 'b'
      cells.push({ x, y, kind })
    }
  }
  if (bloom !== null) {
    for (const c of cells) {
      const dx = c.x - (centerX + bloom[0])
      const dy = c.y - (centerY + bloom[1])
      if (dx === 0 && dy === 0) c.kind = 'q'
      else if (Math.abs(dx) <= 1 && Math.abs(dy) <= 1) c.kind = 'p'
    }
  }
  return cells
}

/** The pond's stone rim in the bottom right corner: a quarter ring of cobbles two to three tiles thick, each cobble one tone, a little moss. */
function stoneBank(): Cell[] {
  const seeds: Seed[] = []
  for (let n = 0; n < 40; n += 1) seeds.push({ x: 62 + hashOf(n, 1, 31) * 20, y: 34 + hashOf(n, 2, 32) * 18, tone: 'su'[Math.floor(hashOf(n, 3, 33) * 2)] ?? 's' })
  const cells: Cell[] = []
  for (let y = 30; y < ROWS; y += 1) {
    for (let x = 60; x < COLUMNS; x += 1) {
      // a coarse wobble, so the rim's edges bulge instead of running true
      const fromCorner = Math.hypot((x + 0.5 - 80) / 1.3, y + 0.5 - 50) + (hashOf(Math.floor(x / 2), Math.floor(y / 2), 34) - 0.5) * 0.9
      if (fromCorner < 4.4 || fromCorner > 6.9) continue
      let tone = 's'
      let bestDistance = Infinity
      for (const seed of seeds) {
        const d = Math.hypot(seed.x - x, seed.y - y)
        if (d < bestDistance) {
          bestDistance = d
          tone = seed.tone
        }
      }
      cells.push({ x, y, kind: hashOf(x, y, 35) < 0.06 ? 'c' : tone })
    }
  }
  return cells
}

/** Deeper water in terraces growing out of a corner; the edge of each is a one-tile checker, so it looks like tesserae and not like banding. */
function stairZone(cornerX: number, cornerY: number, radius: number, squash: number, opacity: number, fill: string): string {
  const seen = new Set<string>()
  for (let y = 0; y < ROWS; y += 1) {
    for (let x = 0; x < COLUMNS; x += 1) {
      const distance = Math.hypot(x + 0.5 - cornerX, (y + 0.5 - cornerY) * squash)
      const coarse = Math.sin(x * 0.45 + cornerY) * 1.2 + Math.sin(y * 0.6 + cornerX) * 1.2
      const dither = (x + y) % 2 === 0 ? 1.1 : -1.1
      if (distance < radius + coarse + dither) seen.add(`${x},${y}`)
    }
  }
  return `<path d="${blocksOf(seen, CELL)}" fill="${fill}" opacity="${opacity}"/>`
}

/** A ring ripple on the grid: the whole cells a circle of this radius passes through, to be lightened a little. */
function ringOutline(centerX: number, centerY: number, radius: number): string {
  const seen = new Set<string>()
  const reach = Math.ceil(radius) + 1
  for (let dy = -reach; dy <= reach; dy += 1) {
    for (let dx = -reach; dx <= reach; dx += 1) {
      if (Math.abs(Math.hypot(dx, dy) - radius) < 0.62) seen.add(`${centerX + dx},${centerY + dy}`)
    }
  }
  return blocksOf(seen, CELL)
}

/** Four rings that show one after another, each fainter, then nothing for the rest of the period. */
function ripple(centerX: number, centerY: number, seconds: number, delaySeconds: number, family: string): string {
  return [1.8, 3.6, 5.3, 7].map((radius, i) => `<path class="ring ${family}${i}" style="animation-duration:${seconds}s;animation-delay:-${delaySeconds.toFixed(2)}s" d="${ringOutline(centerX, centerY, radius)}"/>`).join('')
}

/** The rings' fade, squeezed into the first `fraction` of the period: a long period can then hold one short ripple. */
function ringKeyframes(family: string, fraction: number): string {
  return RING_TRACKS.map((track, i) => `@keyframes ${family}${i}{${track.map(([percent, opacity]) => `${(percent * fraction).toFixed(2).replace(/\.?0+$/, '')}%{opacity:${opacity}}`).join('')}100%{opacity:0}}.${family}${i}{animation-name:${family}${i}}`).join('')
}

/** A wake beside a lane: the ring set's period starts when the head of the koi that started at `startStep` reaches `wakeStep`. */
function wakeRipple(steps: readonly Step[], seconds: number, wakeStep: number, startStep: number, shiftX: number): string {
  const stepSeconds = seconds / steps.length
  const delay = ((((startStep - wakeStep) % steps.length) + steps.length) % steps.length) * stepSeconds
  const at = steps[wakeStep] ?? { x: 0, y: 0 }
  return ripple(at.x + shiftX, at.y, seconds, delay, 'turn')
}

function floatingPad(cells: readonly Cell[], className: string, seconds: number, delay: number): string {
  return `<g class="${className}" style="animation-duration:${seconds}s;animation-delay:-${delay}s">${halo(cells, 0, 1, 1, 0.3)}${mosaic(cells)}</g>`
}

export function koiMosaicSvg(): string {
  // The pond is larger than the window: a koi swims down the right side, leaves by the bottom edge, and comes back up the left side.
  const steps = [...walkLane(RIGHT_LANE), ...walkLane(LEFT_LANE)]
  const seconds = Math.round(steps.length * 2.2)
  const kohakuStart = 34
  const tanchoStart = 34 + 49

  const bigPad = lilyPad(73, 20, 3.6, 150, [0, -1])
  const smallPad = lilyPad(75, 37, 2.6, 300, null)
  const leftPad = lilyPad(7, 30, 3.6, 60, null)
  const stones = stoneBank()

  const style = `
text{font:700 12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;text-anchor:middle}
${Object.entries(KOI_FILLS).map(([kind, fills]) => fills.map((fill, i) => `.k${kind}${i}{fill:${fill}${KOI_OPACITY[kind] === undefined ? '' : `;opacity:${KOI_OPACITY[kind]}`}}`).join('')).join('')}
.fish path{stroke:#0d5a66;stroke-opacity:.3}.kg{fill:#fff1dc;opacity:.5}.kw{fill:#b7c3bd;opacity:.8}
.swim{animation:swim ${seconds}s linear infinite}
.poseA{animation:flipA 3.2s linear infinite}.poseB{animation:flipB 3.2s linear infinite}
.rockX{animation:rockX 37s ease-in-out infinite}.rockY{animation:rockY 41s ease-in-out infinite}
.glint{opacity:.02;animation:glint 13s ease-in-out infinite}
.swell{animation:swell 52s ease-in-out infinite alternate}.swell.b{animation-duration:67s;animation-direction:alternate-reverse}
.band{animation:sweep 71s linear infinite}.band.b{animation-duration:97s;animation-delay:-40s}
.ring{fill:#f2fffb;opacity:0;animation-timing-function:linear;animation-iteration-count:infinite}
${ringKeyframes('slow', 1)}${ringKeyframes('turn', 50 / seconds)}
@keyframes flipA{0%,37.5%{opacity:1}50%,87.5%{opacity:0}100%{opacity:1}}
@keyframes flipB{0%,37.5%{opacity:0}50%,87.5%{opacity:1}100%{opacity:0}}
@keyframes rockX{0%{transform:translate(0,0)}30%{transform:translate(20px,0)}55%{transform:translate(20px,20px)}80%{transform:translate(0,20px)}100%{transform:translate(0,0)}}
@keyframes rockY{0%{transform:translate(0,0)}35%{transform:translate(0,20px)}60%{transform:translate(-20px,20px)}85%{transform:translate(-20px,0)}100%{transform:translate(0,0)}}
@keyframes glint{0%,100%{opacity:.02}50%{opacity:.13}}
@keyframes swell{from{transform:translate(-50px,-16px)}to{transform:translate(60px,22px)}}
@keyframes sweep{from{transform:translate(-600px,0)}to{transform:translate(2300px,0)}}
${swimKeyframes('swim', steps)}
@media (prefers-reduced-motion: reduce){*{animation:none!important}.poseB,.ring{opacity:0}}`

  const defs = `
<linearGradient id="water" x1="0" y1="0" x2="1" y2="0.62"><stop offset="0" stop-color="#6fc3bb"/><stop offset="0.2" stop-color="#90d5ca"/><stop offset="0.52" stop-color="#93d6cb"/><stop offset="0.74" stop-color="#4fb1b1"/><stop offset="1" stop-color="#17697d"/></linearGradient>
<radialGradient id="shallow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#e6f7ee" stop-opacity="0.6"/><stop offset="1" stop-color="#e6f7ee" stop-opacity="0"/></radialGradient>
<radialGradient id="deep" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#17838c" stop-opacity="0.5"/><stop offset="1" stop-color="#17838c" stop-opacity="0"/></radialGradient>
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#f2fffb" stop-opacity="0"/><stop offset="0.5" stop-color="#f2fffb" stop-opacity="0.08"/><stop offset="1" stop-color="#f2fffb" stop-opacity="0"/></linearGradient>
<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M0 0.5h20M0.5 0v20" stroke="#f1fbf5" stroke-opacity="0.16" fill="none"/></pattern>
<linearGradient id="sides" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="0.24" stop-color="#fff" stop-opacity="0.18"/><stop offset="0.76" stop-color="#fff" stop-opacity="0.18"/><stop offset="0.97" stop-color="#fff" stop-opacity="1"/></linearGradient>
<mask id="outward" maskUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1000"><rect width="1600" height="1000" fill="url(#sides)"/></mask>`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
<rect width="1600" height="1000" fill="url(#water)"/>
<g class="swell b"><ellipse cx="1440" cy="820" rx="560" ry="460" fill="url(#deep)"/><ellipse cx="40" cy="60" rx="440" ry="360" fill="url(#deep)" opacity="0.7"/></g>
${[28, 24, 20, 16, 12].map(radius => stairZone(86, 56, radius, 1.1, 0.045, '#0f6a73')).join('')}${[27, 23, 19, 15, 11].map(radius => stairZone(-4, -4, radius, 1.3, 0.04, '#0f6a73')).join('')}${stairZone(84, -6, 18, 1.2, 0.05, '#12767f')}
<rect width="1600" height="1000" fill="url(#grid)" mask="url(#outward)"/>
${WAKES.map(([step, shift]) => wakeRipple(steps, seconds, step, kohakuStart, shift) + wakeRipple(steps, seconds, step, tanchoStart, shift)).join('')}
${ripple(73, 29, 29, 4, 'slow')}${ripple(11, 14, 37, 20, 'slow')}${ripple(72, 46, 43, 31, 'slow')}${ripple(11, 43, 31, 9, 'slow')}
${fishLayer(steps, seconds, kohakuStart, tanchoStart, 'shade', ' transform="translate(40 40)" fill="#0d5a66" opacity="0.07"')}${fishLayer(steps, seconds, kohakuStart, tanchoStart, 'shade', ' transform="translate(20 20)" fill="#0d5a66" opacity="0.16"')}
${fishLayer(steps, seconds, kohakuStart, tanchoStart, 'fish', '')}
${halo(stones, 1, 0, 0, 0.22)}${mosaic(stones)}
${floatingPad(bigPad, 'rockX', 37, 5)}${floatingPad(smallPad, 'rockY', 53, 21)}${floatingPad(leftPad, 'rockY', 47, 30)}
</svg>`
}
