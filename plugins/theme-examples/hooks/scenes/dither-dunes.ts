// Dither Dunes: an ordered-dither desert, one terracotta sun. Two stocks: sand paper by day, umber paper by night.
// Pure string building: no DOM, no imports, the same output on every build.

const WIDTH = 1600
const HEIGHT = 1000
/** One dither pixel is 5 units, so a 1200x800 window (scale 0.8) draws it 4 px wide exactly. */
const CELL = 5
/** The threshold matrix is 8x8 dither pixels: 64 tones, so shade runs smoothly. Tone layers are laid out, and moved, in whole tiles, so the dots never leave the grid. */
const MATRIX = 8
const TILE = CELL * MATRIX
const TILE_COLUMNS = WIDTH / TILE
const TILE_ROWS = HEIGHT / TILE
const TONES = MATRIX * MATRIX
/** Spare field above a crest, for the tone layers to move out of: they are clipped to the dune's outline and slide under it. */
const MARGIN = 3 * TILE
/** Both inks stop near a third: above that the matrix draws crosses, and at this size they look like a fault. */
const SOFT_CEILING = 0.34
const DARK_CEILING = 0.28
/** The dark ink only joins in where the shade is already this deep, so it never shows up in stray single pixels. */
const DARK_FLOOR = 0.1
const SUN_CENTER_X = 1376
const SUN_CENTER_Y = 446
const SUN_RADIUS = 34
const BAYER: readonly (readonly number[])[] = bayerMatrix(MATRIX)

/**
 * A stock is the paper and the strengths of the one sand ink printed on it, and the sun's colour.
 * haze prints the sky, lee the thin shadow under a crest where it crosses the conversation, soft prints sand at both edges of the window,
 * strong only at the right edge, where no panel covers it. sands: the flat tone of each dune, back to front, a step apart.
 */
interface Stock {
  readonly paper: string
  readonly haze: string
  readonly lee: string
  readonly soft: string
  readonly strong: string
  readonly sun: string
  readonly sands: readonly string[]
}

const DAY: Stock = { paper: '#ece2cd', haze: '#e3d8c2', lee: '#d3c5a8', soft: '#bfad8b', strong: '#6f5d49', sun: '#c8573a', sands: ['#e8ddc7', '#e4d8c0', '#e0d3ba', '#dccfb4'] }
/** By night the same drawing is printed light on dark: the paper is umber, the dots are pale sand, nearer dunes are a step lighter. */
const NIGHT: Stock = { paper: '#231d17', haze: '#2a231c', lee: '#40362a', soft: '#6b5c47', strong: '#988462', sun: '#c8573a', sands: ['#27211a', '#2b241c', '#2f271f', '#332b21'] }

/** A point a crest line passes through; a third number of 1 marks a peak. */
type CrestPoint = readonly [number, number, number?]

/**
 * Dunes, back to front: four long crests across the whole window. Each is everything under its crest line: a flat sand tone a shade
 * apart from the one behind it (steps of about 3%, so under the conversation the land is there but nothing competes with text),
 * plus dither shading at the window's edges only, strongest in the lee just under the crest and dissolving downward.
 * tone: tone under the crest (0..1). reach: units it takes to dissolve. seconds: period of the light's creep.
 * driftUnits, driftSeconds: how far the whole dune wanders sideways, and how long it takes. glint: the stretch of crest that catches the sun's colour (null: none).
 */
interface Dune {
  readonly crest: readonly CrestPoint[]
  readonly tone: number
  readonly reach: number
  readonly seconds: number
  readonly driftUnits: number
  readonly driftSeconds: number
  readonly glint: readonly [number, number] | null
}

const DUNES: readonly Dune[] = [
  { crest: [[0, 566], [250, 532, 1], [560, 592], [900, 604], [1200, 574], [1430, 524, 1], [1600, 552]], tone: 0.34, reach: 150, seconds: 104, driftUnits: 40, driftSeconds: 200, glint: null },
  { crest: [[0, 676], [330, 640, 1], [700, 724], [1000, 734], [1290, 644, 1], [1600, 706]], tone: 0.42, reach: 190, seconds: 88, driftUnits: -60, driftSeconds: 150, glint: null },
  { crest: [[0, 806], [200, 764, 1], [520, 864], [820, 904], [1100, 844], [1390, 724, 1], [1600, 794]], tone: 0.48, reach: 220, seconds: 96, driftUnits: 80, driftSeconds: 120, glint: [1230, 1600] },
  { crest: [[0, 934], [300, 904], [640, 962], [900, 972], [1250, 930, 1], [1600, 902]], tone: 0.5, reach: 160, seconds: 80, driftUnits: -100, driftSeconds: 100, glint: null },
]

/** A tone field to be dithered: the sky's haze, the sun, or one dune's shading in the soft or the strong ink. */
interface Field {
  readonly kind: 'haze' | 'sun' | 'soft' | 'strong'
  readonly dune: Dune | null
  readonly index: number
}

/** How a stack of layers creeps: tiles per step on each axis, the period, and where in the period it starts. A period of 0 stands still. */
interface Creep {
  readonly x: number
  readonly y: number
  readonly seconds: number
  readonly phase: number
}

const STILL: Creep = { x: 0, y: 0, seconds: 0, phase: 0 }

/** The ordered-dither threshold matrix, built by the usual doubling: each quarter is the smaller matrix times four, plus 0, 2, 3, 1. */
function bayerMatrix(size: number): number[][] {
  if (size === 1) return [[0]]
  const half = bayerMatrix(size / 2)
  const matrix: number[][] = []
  for (let y = 0; y < size; y += 1) {
    const row: number[] = []
    for (let x = 0; x < size; x += 1) {
      const top = y < size / 2
      const left = x < size / 2
      const quarter = top ? (left ? 0 : 2) : left ? 3 : 1
      row.push(4 * (half[y % (size / 2)]?.[x % (size / 2)] ?? 0) + quarter)
    }
    matrix.push(row)
  }
  return matrix
}

/** The matrix's threshold for the dither pixel at a point (in units): a tone between 0 and 1. */
function thresholdAt(x: number, y: number): number {
  return ((BAYER[(y / CELL) % MATRIX]?.[(x / CELL) % MATRIX] ?? 0) + 0.5) / TONES
}

function smoothstep(low: number, high: number, value: number): number {
  const t = Math.min(1, Math.max(0, (value - low) / (high - low)))
  return t * t * (3 - 2 * t)
}

/**
 * Height of a crest line at x. Between plain points it eases like a cosine, so it never overshoots.
 * It runs into a peak steeply and concave, the way sand lies.
 */
function crestAt(points: readonly CrestPoint[], x: number): number {
  let last = 0
  for (let index = 0; index < points.length; index += 1) {
    const to = points[index]
    if (to === undefined) continue
    last = to[1]
    if (x > to[0]) continue
    const from = index === 0 ? undefined : points[index - 1]
    if (from === undefined) return to[1]
    const t = (x - from[0]) / (to[0] - from[0])
    let eased = (1 - Math.cos(Math.PI * t)) / 2
    if (to[2] === 1 && from[2] !== 1) eased = Math.pow(t, 1.7)
    if (from[2] === 1 && to[2] !== 1) eased = 1 - Math.pow(1 - t, 1.7)
    return from[1] + (to[1] - from[1]) * eased
  }
  return last
}

/** The crest's height at x, on the dither grid. */
function crestRow(dune: Dune, x: number): number {
  return Math.round(crestAt(dune.crest, x + CELL / 2) / CELL) * CELL
}

/** 0 under the conversation (24% to 76% of the width), 1 at the window's edges: where dots are allowed at all. */
function edgeWeight(x: number): number {
  const u = x / WIDTH
  return Math.max(1 - smoothstep(0.06, 0.24, u), smoothstep(0.76, 0.93, u))
}

/** A dune's tone at a point. Above the crest it keeps the crest's tone. A slow swell keeps the bands from running parallel to the crest. */
function duneTone(dune: Dune, index: number, x: number, y: number): number {
  const depth = Math.max(0, y - crestAt(dune.crest, x))
  const swell = 0.86 + 0.14 * Math.sin(x / 120 + index * 2.3)
  return dune.tone * swell * Math.pow(Math.max(0, 1 - depth / dune.reach), 1.4)
}

/** The tone of a field at a point. */
function fieldTone(field: Field, x: number, y: number): number {
  if (field.kind === 'haze') {
    const sides = Math.max(1 - smoothstep(0.08, 0.27, x / WIDTH), smoothstep(0.73, 0.92, x / WIDTH))
    return 0.2 * smoothstep(0, 620, y + 50 * Math.sin(x / 210)) * sides
  }
  if (field.kind === 'sun') {
    const distance = Math.hypot(x - SUN_CENTER_X, y - SUN_CENTER_Y)
    if (distance <= SUN_RADIUS) return 1
    if (distance <= SUN_RADIUS * 1.45) return 0.5
    return distance <= SUN_RADIUS * 1.9 ? 0.25 : 0
  }
  const dune = field.dune
  if (dune === null || y - crestAt(dune.crest, x) <= -MARGIN) return 0
  const tone = duneTone(dune, field.index, x, y)
  if (field.kind === 'soft') return Math.min(SOFT_CEILING, tone * edgeWeight(x))
  /** The strong ink: the right edge only, and later than the soft ink. */
  return Math.min(DARK_CEILING, 1.4 * Math.max(0, tone * smoothstep(0.82, 0.97, x / WIDTH) - DARK_FLOOR))
}

/**
 * One threshold of the matrix, drawn in tile units, between two tile columns: every tile whose pixel at that threshold passes the field's tone.
 * Rows of runs; identical runs on consecutive rows are merged into taller boxes.
 */
function levelPath(level: number, firstColumn: number, lastColumn: number, field: Field): string {
  let pixelColumn = 0
  let pixelRow = 0
  for (let y = 0; y < MATRIX; y += 1) {
    for (let x = 0; x < MATRIX; x += 1) {
      if (BAYER[y]?.[x] === level) {
        pixelColumn = x
        pixelRow = y
      }
    }
  }
  const threshold = (level + 0.5) / TONES
  const open = new Map<string, number>()
  let path = ''
  for (let row = 0; row <= TILE_ROWS; row += 1) {
    const seen = new Set<string>()
    let runStart = -1
    for (let column = firstColumn; column <= lastColumn && row < TILE_ROWS; column += 1) {
      const inked = column < lastColumn && fieldTone(field, column * TILE + (pixelColumn + 0.5) * CELL, row * TILE + (pixelRow + 0.5) * CELL) > threshold
      if (inked && runStart < 0) runStart = column
      if (!inked && runStart >= 0) {
        const key = `${runStart} ${column - runStart}`
        seen.add(key)
        if (!open.has(key)) open.set(key, row)
        runStart = -1
      }
    }
    for (const [key, firstRow] of [...open]) {
      if (seen.has(key)) continue
      const [start, length] = key.split(' ').map(Number)
      path += `M${start ?? 0} ${firstRow}h${length ?? 0}v${row - firstRow}h${-(length ?? 0)}z`
      open.delete(key)
    }
  }
  return path
}

/** A stack of threshold layers for one field in one ink. Every layer creeps a whole tile at a time, three tiles there and back, each a little after the last. */
function layerStack(ink: string, firstColumn: number, lastColumn: number, field: Field, creep: Creep): string {
  let layers = ''
  for (let level = 0; level < TONES; level += 1) {
    const path = levelPath(level, firstColumn, lastColumn, field)
    if (path === '') continue
    let motion = ''
    if (creep.seconds !== 0) {
      const delay = ((creep.phase + level * 2.9) % creep.seconds).toFixed(1)
      motion = ` class="creep" style="--x:${creep.x * 3}px;--y:${creep.y * 3}px;animation-duration:${creep.seconds}s;animation-delay:-${delay}s"`
    }
    layers += `<path${motion} d="${path}" fill="url(#${ink}${level})"/>`
  }
  return layers
}

/** The dune's outline, a staircase on the dither grid, so its edge is made of the pixels its shading is made of. It runs past both sides of the window, for the drift. */
function outlinePath(dune: Dune): string {
  const spare = 120
  let path = `M${-spare} ${HEIGHT}`
  let previous = -1
  for (let x = -spare; x < WIDTH + spare; x += CELL) {
    const top = crestRow(dune, x)
    if (top !== previous) {
      path += previous < 0 ? `V${top}` : `H${x}V${top}`
      previous = top
    }
  }
  return `${path}H${WIDTH + spare}V${HEIGHT}z`
}

/** A lit crest: sun-coloured pixels lying on a stretch of crest, nearly solid for two pixels and thinning out over the four below, and toward both ends. */
function glintPath(dune: Dune, stock: Stock): string {
  if (dune.glint === null) return ''
  const [from, to] = dune.glint
  let path = ''
  for (let x = from; x < to; x += CELL) {
    const ends = Math.min(smoothstep(from, from + 120, x), 1 - smoothstep(to - 60, to + 60, x))
    for (let deep = 0; deep < 6; deep += 1) {
      const y = crestRow(dune, x) + deep * CELL
      const tone = deep < 2 ? 0.9 : 0.55 * Math.pow(1 - (deep - 2) / 4, 1.5)
      if (tone * ends > thresholdAt(x, y)) path += `M${x} ${y}h${CELL}v${CELL}h${-CELL}z`
    }
  }
  return `<path d="${path}" fill="${stock.sun}"/>`
}

/** Where a crest crosses the conversation it still gets shaded in dots: a band two pixels deep, half then a quarter, in an ink barely apart from the sand. */
function leePath(dune: Dune, stock: Stock): string {
  let path = ''
  for (let x = 240; x < 1360; x += CELL) {
    const middle = 1 - edgeWeight(x)
    for (let deep = 0; deep < 2; deep += 1) {
      const y = crestRow(dune, x) + deep * CELL
      if ((deep === 0 ? 0.5 : 0.25) * middle > thresholdAt(x, y)) path += `M${x} ${y}h${CELL}v${CELL}h${-CELL}z`
    }
  }
  return `<path d="${path}" fill="${stock.lee}"/>`
}

/**
 * One dune. Its outline (the flat sand, the clip, the lee and the glint) wanders sideways one dither pixel at a time, while its dots stay where they are
 * on the screen: the shape slides across a still dither screen, the way a one-bit game does it, so only the pixels along the crest ever change.
 */
function dunePart(dune: Dune, index: number, stock: Stock): string {
  const outline = outlinePath(dune)
  const softField: Field = { kind: 'soft', dune, index }
  const strongField: Field = { kind: 'strong', dune, index }
  const softLeft = layerStack('soft', 0, TILE_COLUMNS / 2, softField, { x: -1, y: 1, seconds: dune.seconds * 1.3, phase: index * 19 })
  const softRight = layerStack('soft', TILE_COLUMNS / 2, TILE_COLUMNS, softField, { x: 1, y: 1, seconds: dune.seconds * 1.3, phase: index * 23 })
  const strong = layerStack('strong', TILE_COLUMNS / 2, TILE_COLUMNS, strongField, { x: 1, y: 1, seconds: dune.seconds, phase: index * 29 })
  const wander = `style="--d:${dune.driftUnits}px;animation-duration:${dune.driftSeconds}s;animation-delay:-${(index * 31) % dune.driftSeconds}s;animation-timing-function:steps(${Math.abs(dune.driftUnits) / CELL})"`
  const sand = stock.sands[index] ?? stock.paper
  return `<clipPath id="c${index}"><path d="${outline}"/></clipPath><g class="drift" ${wander}><path d="${outline}" fill="${sand}"/><g clip-path="url(#c${index})"><g class="undrift" ${wander}><g transform="scale(${TILE})">${softLeft}${softRight}${strong}</g></g></g>${leePath(dune, stock)}${glintPath(dune, stock)}</g>`
}

/** The sky is not left blank at the window's edges: a haze of the faintest ink gathers toward the horizon. Like the sand's dots it keeps out from under the conversation. */
function skyPart(): string {
  return `<g transform="scale(${TILE})">${layerStack('haze', 0, TILE_COLUMNS, { kind: 'haze', dune: null, index: 0 }, STILL)}</g>`
}

/** The sun is dithered too: a solid disc inside two clean rings of its own dots, a half and a quarter. It starts clear of the far dune and climbs up and a little to the left, one pixel at a time. */
function sunPart(): string {
  return `<g class="rise"><g class="veer"><g transform="scale(${TILE})">${layerStack('sun', 0, TILE_COLUMNS, { kind: 'sun', dune: null, index: 0 }, STILL)}</g></g></g>`
}

/** Grains blown along two crests, at the window's edges only: single soft pixels, stepping one pixel at a time, downwind. */
function grainsPart(stock: Stock): string {
  let out = ''
  for (let grain = 0; grain < 22; grain += 1) {
    const right = grain % 3 !== 0
    const startX = right ? 1260 + ((grain * 29) % 120) : 40 + ((grain * 31) % 120)
    const dune = right ? DUNES[2] : DUNES[1]
    if (dune === undefined) continue
    const y = crestRow(dune, startX + 110) - CELL * (2 + ((grain * 37) % 5))
    const seconds = 34 + ((grain * 13) % 25)
    out += `<rect class="grain" style="animation-duration:${seconds}s;animation-delay:-${(grain * 6.1).toFixed(1)}s" x="${startX - (startX % CELL)}" y="${y}" width="${CELL}" height="${CELL}" fill="${stock.soft}"/>`
  }
  return out
}

/** One pattern per threshold of the matrix, each a single dither pixel in its place in the tile, in one ink. */
function bayerPatterns(name: string, colour: string, levels: number): string {
  let out = ''
  for (let y = 0; y < MATRIX; y += 1) {
    for (let x = 0; x < MATRIX; x += 1) {
      const level = BAYER[y]?.[x] ?? 0
      if (level < levels) out += `<pattern id="${name}${level}" width="1" height="1" patternUnits="userSpaceOnUse"><rect x="${x / MATRIX}" y="${y / MATRIX}" width="${1 / MATRIX}" height="${1 / MATRIX}" fill="${colour}"/></pattern>`
    }
  }
  return out
}

/** The whole scene on one stock. */
function sceneSvg(stock: Stock): string {
  const style = `
.creep{animation:creep 90s steps(3) infinite alternate}
.rise{animation:rise 200s steps(38) infinite alternate}
.veer{animation:veer 200s steps(19) infinite alternate}
.drift{animation:drift 120s steps(12) infinite alternate}
.undrift{animation:undrift 120s steps(12) infinite alternate}
.grain{animation:grain 50s steps(44) infinite}
@keyframes creep{from{transform:translate(0,0)}to{transform:translate(var(--x),var(--y))}}
@keyframes rise{from{transform:translate(0,0)}to{transform:translate(0,-${38 * CELL}px)}}
@keyframes veer{from{transform:translate(0,0)}to{transform:translate(-${19 * CELL}px,0)}}
@keyframes drift{from{transform:translate(0,0)}to{transform:translate(var(--d),0)}}
@keyframes undrift{from{transform:translate(0,0)}to{transform:translate(calc(var(--d) * -1),0)}}
@keyframes grain{0%{transform:translate(0,0);opacity:0}8%{opacity:1}80%{opacity:1}100%{transform:translate(${44 * CELL}px,0);opacity:0}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}.grain{opacity:0}}`
  const inked = Math.ceil(SOFT_CEILING * TONES)
  const patterns = bayerPatterns('haze', stock.haze, inked) + bayerPatterns('soft', stock.soft, inked) + bayerPatterns('strong', stock.strong, inked) + bayerPatterns('sun', stock.sun, TONES)
  const dunes = DUNES.map((dune, index) => dunePart(dune, index, stock)).join('')
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${patterns}</defs>
<rect width="${WIDTH}" height="${HEIGHT}" fill="${stock.paper}"/>
${skyPart()}${sunPart()}${dunes}${grainsPart(stock)}
</svg>`
}

/** Dither Dunes: dunes on sand paper, for a light window. */
export function ditherDunesSvg(): string {
  return sceneSvg(DAY)
}

/** Dither Dunes Night: the same dunes printed pale on umber paper, for a dark window. */
export function ditherDunesNightSvg(): string {
  return sceneSvg(NIGHT)
}
