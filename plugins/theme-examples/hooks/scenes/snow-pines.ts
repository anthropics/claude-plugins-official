// Snow Pines: an ASCII forest in falling snow at dusk. A dark-window scene.
// Pure string building: no DOM, nothing read from outside, the same string on every call.

const WIDTH = 1600
const HEIGHT = 1000

type NeedleTone = 'shadow' | 'mid' | 'lit'
type Tone = NeedleTone | 'rim' | 'cap'

interface Mark {
  x: number
  y: number
  glyph: string
}

interface Cell extends Mark {
  tone: Tone
}

interface Grid {
  cellWidth: number
  cellHeight: number
  fontSize: number
  weight: number
}

interface Depth extends Grid {
  rimChance: number
  tile: Record<Tone, string>
  glyph: Record<Tone, string>
}

/** A pine: the column of its apex, the row of its foot, its height in rows. */
type Stand = readonly [number, number, number]

interface Wood {
  from: number
  to: number
  tallest: number
  chance: number
}

interface SnowLayer {
  id: string
  seed: number
  cellWidth: number
  cellHeight: number
  rows: number
  seconds: readonly number[]
  swaySeconds: number
  density: number
  everywhere: boolean
  full: number
  none: number
  glyphs: string
  fontSize: number
  colour: string
  opacity: number
}

/**
 * The three depths of forest: each has its own character grid, so far trees are small type and near trees large type.
 * Every tree is built from cells, a coloured ground and a glyph per cell, like a terminal with background colours.
 * Each depth has three needle values (shadow side, mid, lit side) and two snow values, so the light from the horizon models the trees.
 */
const FAR: Depth = {
  cellWidth: 9, cellHeight: 11, fontSize: 10, weight: 700, rimChance: 0.5,
  tile: { shadow: '#33336a', mid: '#3e4079', lit: '#4c5090', rim: '#6c70a6', cap: '#8a8ebe' },
  glyph: { shadow: '#565a96', mid: '#6a70a8', lit: '#8e94c8', rim: '#bcc1e6', cap: '#d6daf4' },
}
const MIDDLE: Depth = {
  cellWidth: 13, cellHeight: 16, fontSize: 15, weight: 700, rimChance: 0.65,
  tile: { shadow: '#142d44', mid: '#1b4358', lit: '#275e68', rim: '#5a7396', cap: '#869fbe' },
  glyph: { shadow: '#44708a', mid: '#5a98a6', lit: '#78b6b0', rim: '#ccd6f2', cap: '#e8eeff' },
}
const NEAR: Depth = {
  cellWidth: 18, cellHeight: 22, fontSize: 21, weight: 700, rimChance: 0.75,
  tile: { shadow: '#0c2832', mid: '#134048', lit: '#1a5456', rim: '#5a7396', cap: '#869fbe' },
  glyph: { shadow: '#3a7480', mid: '#4f9a96', lit: '#6cb4a6', rim: '#d0d9f2', cap: '#eef2ff' },
}

const NEEDLE_TONES: readonly NeedleTone[] = ['shadow', 'mid', 'lit']

/** A deterministic hash to 0..1, so every build is the same (nothing here is random at run time). */
function hash(a: number, b: number, c: number): number {
  let value = (a * 374761393 + b * 668265263 + c * 2147483647) | 0
  value = (value ^ (value >>> 13)) * 1274126177
  value = value ^ (value >>> 16)
  return ((value >>> 0) % 100000) / 100000
}

/** Half-width of a pine at a row below its apex: a slim taper, with boughs that flare within a tier and tuck back in at the next. */
function halfWidthAt(row: number, tierLength: number): number {
  if (row === 0) return 0
  const within = (row - 1) % tierLength
  return Math.max(1, Math.round(row * 0.25 + within * 0.55))
}

/**
 * One pine, cell by cell, on its depth's grid. Light comes from the horizon in the middle of the frame: the bough ends that face it are lit,
 * the far edge and the row tucked under each tier's overhang are in shadow, and a bough cell with nothing above it carries snow.
 */
function pineCells(cells: Map<string, Cell>, apexColumn: number, baseRow: number, height: number, tierLength: number, seed: number, depth: Depth): void {
  const boughRows = height - (height > 12 ? 2 : 1)
  const towardLight = (apexColumn + 0.5) * depth.cellWidth < WIDTH / 2 ? 1 : -1
  for (let row = 0; row < height; row += 1) {
    const y = baseRow - height + 1 + row
    const isTrunk = row >= boughRows
    const half = isTrunk ? 0 : halfWidthAt(row, tierLength)
    const halfAbove = row === 0 ? -1 : halfWidthAt(row - 1, tierLength)
    for (let offset = -half; offset <= half; offset += 1) {
      const x = apexColumn + offset
      const chance = hash(x, y, seed)
      const isExposed = !isTrunk && Math.abs(offset) > halfAbove
      const facing = offset * towardLight
      const slash = (offset < 0 || (offset === 0 && row % 2 === 0)) ? '/' : '\\'
      let glyph = row === 0 ? '^' : isTrunk ? '|' : slash
      if (!isExposed && offset !== 0 && Math.abs(offset) < half && hash(x, y, seed + 2) < 0.1) glyph = ':'
      const within = (row - 1) % tierLength
      let tone: Tone = 'mid'
      if (within === 0 && row > 1) tone = 'shadow'
      if (half >= 2 && facing <= -half + (half > 4 ? 1 : 0)) tone = 'shadow'
      if (facing > 0 && facing >= half - 1 && within > 0) tone = 'lit'
      if (tone === 'shadow' && hash(x, y, seed + 1) < 0.15) tone = 'mid'
      if (isTrunk) tone = 'shadow'
      if (isExposed && chance < depth.rimChance) tone = chance < 0.08 || row === 0 ? 'cap' : 'rim'
      cells.set(`${x},${y}`, { x, y, glyph, tone })
    }
  }
}

function escapeGlyph(glyph: string): string {
  return glyph === '<' ? '&lt;' : glyph === '&' ? '&amp;' : glyph
}

/**
 * ONE text element for a whole list of glyphs, with a per-glyph x list and y list, so every glyph sits on its grid cell whatever the font.
 * One element, not one per row: what a browser pays for is the number of text elements, far more than the number of glyphs in them.
 */
function glyphRows(list: readonly Mark[], grid: Grid, colour: string, opacity: number): string {
  if (list.length === 0) return ''
  const sorted = [...list].sort((left, right) => left.y - right.y || left.x - right.x)
  const xs = sorted.map(cell => cell.x * grid.cellWidth + grid.cellWidth / 2).join(' ')
  const ys = sorted.map(cell => cell.y * grid.cellHeight + Math.round(grid.cellHeight * 0.8)).join(' ')
  const text = sorted.map(cell => escapeGlyph(cell.glyph)).join('')
  const faint = opacity < 1 ? ` fill-opacity="${opacity}"` : ''
  return `<text x="${xs}" y="${ys}" fill="${colour}"${faint} style="font-size:${grid.fontSize}px;font-weight:${grid.weight}">${text}</text>`
}

/** The coloured ground behind a list of cells: one rectangle per run of neighbours in a row, with no gaps, so there is no mesh of grid lines. */
function tiles(list: readonly Mark[], grid: Grid, colour: string, opacity: number): string {
  const rows = new Map<number, number[]>()
  for (const cell of list) {
    const row = rows.get(cell.y)
    if (row) row.push(cell.x)
    else rows.set(cell.y, [cell.x])
  }
  let path = ''
  for (const [y, columns] of rows) {
    columns.sort((left, right) => left - right)
    let start = columns[0] ?? 0
    let previous = start
    for (let index = 1; index <= columns.length; index += 1) {
      const column = columns[index]
      if (column !== undefined && column === previous + 1) {
        previous = column
        continue
      }
      const width = (previous - start + 1) * grid.cellWidth
      path += `M${start * grid.cellWidth} ${y * grid.cellHeight}h${width}v${grid.cellHeight}h-${width}z`
      if (column === undefined) break
      start = column
      previous = column
    }
  }
  const faint = opacity < 1 ? ` fill-opacity="${opacity}"` : ''
  return `<path d="${path}" fill="${colour}"${faint}/>`
}

function cellsOfTone(all: readonly Cell[], tone: Tone): Cell[] {
  return all.filter(cell => cell.tone === tone)
}

/** Which of the four waves of settling snow a snowy cell belongs to. */
function waveOf(cell: Mark, seed: number): number {
  return Math.floor(hash(cell.x, cell.y, seed + 5) * 4)
}

/** A stand of pines at one depth: shadow ground under everything, mid and lit over it, a glyph in every cell, then the snowy cells, which arrive in four waves. */
function forest(stands: readonly Stand[], depth: Depth, tierLength: number, seed: number): string {
  const cells = new Map<string, Cell>()
  for (const [column, baseRow, height] of stands) pineCells(cells, column, baseRow, height, tierLength, seed, depth)
  const all = [...cells.values()]
  const rims = cellsOfTone(all, 'rim')
  const caps = cellsOfTone(all, 'cap')
  let frost = ''
  for (let which = 0; which < 4; which += 1) {
    const rim = rims.filter(cell => waveOf(cell, seed) === which)
    const cap = caps.filter(cell => waveOf(cell, seed) === which)
    frost += `<g class="settle" style="animation-delay:-${which * 14}s">${tiles(rim, depth, depth.tile.rim, 1)}${tiles(cap, depth, depth.tile.cap, 1)}${glyphRows(rim, depth, depth.glyph.rim, 1)}${glyphRows(cap, depth, depth.glyph.cap, 1)}</g>`
  }
  // each cell's ground is painted once, in its own value, so the grounds can be faint without a group opacity
  const shaded = cellsOfTone(all, 'shadow').concat(rims, caps)
  return tiles(shaded, depth, depth.tile.shadow, 0.78) + tiles(cellsOfTone(all, 'mid'), depth, depth.tile.mid, 0.78) + tiles(cellsOfTone(all, 'lit'), depth, depth.tile.lit, 0.78) +
    NEEDLE_TONES.map(tone => glyphRows(cellsOfTone(all, tone), depth, depth.glyph[tone], 1)).join('') +
    // under the frost a snowy cell is an ordinary needle cell, so a bough never shows a hole while its snow is away
    glyphRows(rims.concat(caps), depth, depth.glyph.mid, 1) + frost
}

/** How far a point is from the reading column, 0 in the middle of the window and 1 at the left and right edges. */
function edgeness(x: number): number {
  const fromCentre = Math.abs(x - WIDTH * 0.51) / (WIDTH * 0.5)
  return Math.min(1, Math.max(0, (fromCentre - 0.4) / 0.5))
}

/** Feathering for the brighter snow and the flake glyphs: 1 at the far left and right, falling in a straight line to 0 at the edge of the reading column. */
function feather(x: number, full: number, none: number): number {
  const left = (none - x) / (none - full)
  const right = (x - (WIDTH - none + 30)) / (none - full)
  return Math.min(1, Math.max(0, left, right))
}

/** The crests of the three snow hills, back to front. The whole ground leans: higher on the left, lower on the right. */
function lean(x: number): number {
  return (x - WIDTH / 2) * 0.03
}
function backCrest(x: number): number {
  return 716 - edgeness(x) * 52 + Math.sin(x * 0.0061 + 0.4) * 9 + lean(x)
}
function middleCrest(x: number): number {
  return 790 - edgeness(x) * 30 + Math.sin(x * 0.0043 + 2.2) * 13 + lean(x)
}
function frontCrest(x: number): number {
  return 880 - edgeness(x) * 20 + Math.sin(x * 0.0035 + 4.6) * 12 + lean(x)
}

const FAR_WOODS: readonly Wood[] = [
  { from: -2, to: 52, tallest: 11, chance: 0.4 },
  { from: 58, to: 74, tallest: 5, chance: 0.34 },
  { from: 131, to: 141, tallest: 6, chance: 0.4 },
  { from: 147, to: 180, tallest: 8, chance: 0.4 },
]

/** The far tree line: a wood on the left, a smaller one on the right, and one small copse left of centre. */
function farForest(): string {
  const stands: Stand[] = []
  for (const wood of FAR_WOODS) {
    for (let column = wood.from; column <= wood.to; column += 1) {
      if (hash(column, 3, 11) > wood.chance) continue
      const x = column * FAR.cellWidth
      const middle = (wood.from + wood.to) / 2
      const taper = 1 - Math.abs(column - middle) / ((wood.to - wood.from) / 2 + 1) * 0.5
      const height = 3 + Math.floor(hash(column, 5, 11) * (wood.tallest - 3) * taper)
      stands.push([column, Math.round(backCrest(x) / FAR.cellHeight) + Math.floor(hash(column, 7, 11) * 2), height])
    }
  }
  return forest(stands, FAR, 3, 17)
}

/** Column of the apex and height in rows of each middle and near pine; the foot row is worked out from the ground. */
const MIDDLE_PINES: ReadonlyArray<readonly [number, number]> = [
  [3, 13], [12, 16], [20, 11],
  [121, 14], [113, 10], [98, 13],
]
const NEAR_PINES: ReadonlyArray<readonly [number, number]> = [
  [1, 25], [9, 19], [-4, 15],
  [87, 21], [82, 14],
]

/** Middle trees: a group on the left, a lighter one on the right, none under the reading column. */
function middleForest(): string {
  const stands = MIDDLE_PINES.map<Stand>(([column, height], index) => {
    const x = column * MIDDLE.cellWidth
    return [column, Math.round((middleCrest(x) + 34) / MIDDLE.cellHeight) + Math.floor(hash(index, 2, 23) * 2), height]
  })
  return forest(stands, MIDDLE, 3, 29)
}

/** Near trees: a low dark wall on the left, a lower one on the right, so the frame is not a mirror; their feet are below the window. */
function nearForest(): string {
  const stands = NEAR_PINES.map<Stand>(([column, height], index) => [column, 47 + Math.floor(hash(index, 9, 31) * 2), height])
  return forest(stands, NEAR, 4, 37)
}

const CREST_GLYPHS = '_-_~_-'
const DRIFT_GLYPHS = '..-,_\''

/** The snow field is made of characters: rows of drift glyphs on the far grid, thick at each hill's crest and thinning below it, sparse under the reading column. */
function hillMarks(crestAt: (x: number) => number, colour: string, opacity: number, rowsDeep: number, seed: number): string {
  const marks: Mark[] = []
  const columns = Math.ceil(WIDTH / FAR.cellWidth)
  for (let column = 0; column < columns; column += 1) {
    const x = (column + 0.5) * FAR.cellWidth
    const crestRow = Math.ceil(crestAt(x) / FAR.cellHeight)
    const outside = feather(x, 300, 520)
    const thin = 0.12 + 0.6 * outside
    for (let below = 0; below < rowsDeep; below += 1) {
      const pick = hash(column, below, seed)
      const limit = (below === 0 ? 0.8 : 0.5 - below * (0.4 / rowsDeep)) * thin
      if (pick > limit || (below > 0 && outside === 0)) continue
      const which = Math.floor(hash(column, below, seed + 1) * 6)
      const glyph = (below === 0 ? CREST_GLYPHS[which] : DRIFT_GLYPHS[which]) ?? '.'
      marks.push({ x: column, y: crestRow + below, glyph })
    }
  }
  return glyphRows(marks, FAR, colour, opacity)
}

/** A hill's body: one long smooth drift. The three drifts are close in value so no seam runs behind the text. */
function hillBody(crestAt: (x: number) => number, fill: string, opacity: number): string {
  let path = `M0 ${HEIGHT}V${crestAt(0).toFixed(1)}`
  for (let x = 20; x <= WIDTH; x += 20) path += `L${x} ${crestAt(x).toFixed(1)}`
  return `<path d="${path}V${HEIGHT}z" fill="${fill}" fill-opacity="${opacity}"/>`
}

function snowField(): string {
  return hillBody(backCrest, 'url(#field)', 1) + hillBody(middleCrest, '#433f76', 0.5) + hillBody(frontCrest, '#3b386e', 0.5) +
    hillMarks(backCrest, '#c6caee', 0.4, 3, 41) +
    hillMarks(middleCrest, '#a9aedc', 0.36, 4, 43) +
    hillMarks(frontCrest, '#8388c0', 0.36, 5, 47)
}

/**
 * One layer of falling snow. The fall is continuous, and each of a layer's few bands of columns falls at its own speed.
 * Every band is ONE text element (its flakes twice over, a screen apart, so the loop has no seam) that carries both motions itself:
 * the fall on `transform`, the sideways sway on `translate`. Each moving element costs the browser a window-sized layer every frame,
 * so there are six of them in all, and the two brighter layers, which only fall near the edges, are split left and right to keep them narrow.
 */
function snowLayer(layer: SnowLayer): string {
  const columns = Math.ceil(WIDTH / layer.cellWidth) + 3
  const bandCount = layer.seconds.length
  const fall = layer.rows * layer.cellHeight
  const bands = layer.seconds.map((): Mark[] => [])
  for (let row = 0; row < layer.rows; row += 1) {
    for (let column = -2; column < columns; column += 1) {
      const x = column * layer.cellWidth
      const density = layer.everywhere ? layer.density : layer.density * feather(x, layer.full, layer.none)
      if (hash(column, row, layer.seed) >= density) continue
      const dotOnly = hash(column, row, layer.seed + 3) >= feather(x, 240, 470)
      const glyph = dotOnly ? '.' : layer.glyphs[Math.floor(hash(column, row, layer.seed + 1) * layer.glyphs.length)] ?? '.'
      const which = layer.everywhere ? Math.floor(hash(column, 0, layer.seed + 2) * bandCount) : x < WIDTH / 2 ? 0 : 1
      const band = bands[which]
      const baseline = row * layer.cellHeight + Math.round(layer.cellHeight * 0.8)
      if (band) band.push({ x: x + layer.cellWidth / 2, y: baseline - fall, glyph }, { x: x + layer.cellWidth / 2, y: baseline, glyph })
    }
  }
  return bands.map((flakes, which) => {
    const seconds = layer.seconds[which] ?? 60
    const xs = flakes.map(flake => flake.x).join(' ')
    const ys = flakes.map(flake => flake.y).join(' ')
    const text = flakes.map(flake => flake.glyph).join('')
    const fallDelay = (seconds * (0.23 + which * 0.31)).toFixed(2)
    return `<text class="${layer.id}" x="${xs}" y="${ys}" style="animation:fall${layer.id} ${seconds}s linear -${fallDelay}s infinite,sway ${layer.swaySeconds}s ease-in-out -${which * 7 + layer.seed % 10}s infinite alternate">${text}</text>`
  }).join('')
}

/** Three layers of snow. Only the faint one falls everywhere; the other two keep to the edges and never cross the reading column. */
const SNOW_LAYER_FAINT: SnowLayer = { id: 'a', seed: 51, cellWidth: 14, cellHeight: 20, rows: 52, seconds: [61], swaySeconds: 19, density: 0.011, everywhere: true, full: 0, none: 0, glyphs: '*.*\'.+', fontSize: 17, colour: '#b4bcec', opacity: 0.34 }
const SNOW_LAYER_MIDDLE: SnowLayer = { id: 'b', seed: 61, cellWidth: 16, cellHeight: 20, rows: 52, seconds: [43, 53], swaySeconds: 14.5, density: 0.06, everywhere: false, full: 0, none: 600, glyphs: '.*.*.+\'*', fontSize: 17, colour: '#c3cbf2', opacity: 0.5 }
const SNOW_LAYER_BRIGHT: SnowLayer = { id: 'c', seed: 71, cellWidth: 22, cellHeight: 26, rows: 40, seconds: [31, 38], swaySeconds: 11.5, density: 0.06, everywhere: false, full: 0, none: 470, glyphs: '*.*+', fontSize: 22, colour: '#d3daf8', opacity: 0.55 }
const SNOW_LAYERS: readonly SnowLayer[] = [SNOW_LAYER_FAINT, SNOW_LAYER_MIDDLE, SNOW_LAYER_BRIGHT]

const CABIN_SHAPE: readonly string[] = [' /^\\ ', '/___\\', '|[] |']

/** The one accent: a small cabin on the middle grid between the right-hand trees: a pitched snowy roof, a dark wall, two amber glyphs for its lit window. */
function cabin(): string {
  const column = 103
  const row = Math.round((middleCrest(column * MIDDLE.cellWidth) + 8) / MIDDLE.cellHeight)
  const roof: Mark[] = []
  const wall: Mark[] = []
  const pane: Mark[] = []
  CABIN_SHAPE.forEach((line, y) => {
    for (let x = 0; x < line.length; x += 1) {
      const glyph = line[x] ?? ' '
      if (glyph === ' ' && y < 2) continue
      const cell = { x: column + x, y: row - 2 + y, glyph }
      if (y < 2) roof.push(cell)
      else if (glyph === '[' || glyph === ']') pane.push(cell)
      else wall.push(cell)
    }
  })
  const left = column * MIDDLE.cellWidth
  const top = row * MIDDLE.cellHeight
  return `<ellipse class="glow" cx="${left + 26}" cy="${top + 20}" rx="44" ry="12" fill="url(#lamp)"/>` +
    tiles(wall.concat(pane), MIDDLE, '#1c1c46', 1) + tiles(roof, MIDDLE, '#5a5c94', 1) +
    glyphRows(roof, MIDDLE, '#d0d4f2', 0.9) + glyphRows(wall.filter(cell => cell.glyph !== ' '), MIDDLE, '#3c3f74', 1) +
    `<g class="glow">${glyphRows(pane, MIDDLE, '#f0a040', 1)}</g>`
}

export function snowPinesSvg(): string {
  const fallFrames = SNOW_LAYERS.map(layer => `@keyframes fall${layer.id}{from{transform:translateY(0)}to{transform:translateY(${layer.rows * layer.cellHeight}px)}}`).join('')
  const layerStyles = SNOW_LAYERS.map(layer => `.${layer.id}{fill:${layer.colour};fill-opacity:${layer.opacity};font-size:${layer.fontSize}px}`).join('')
  const style = `
text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;text-anchor:middle}
${layerStyles}
.glow{animation:glow 7s ease-in-out infinite alternate}
.settle{animation:settle 160s linear infinite}
.dusk{animation:dusk 170s ease-in-out infinite alternate}
${fallFrames}
@keyframes sway{from{translate:-28px 0}to{translate:14px 0}}
@keyframes glow{from{fill-opacity:.7}to{fill-opacity:1}}
@keyframes settle{0%{fill-opacity:.1}12%{fill-opacity:.4}56%{fill-opacity:1}86%{fill-opacity:1}100%{fill-opacity:.1}}
@keyframes dusk{from{transform:translateX(-420px);fill-opacity:.5}to{transform:translateX(300px);fill-opacity:1}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  const defs = `
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#181a46"/><stop offset="0.22" stop-color="#1c1d4d"/><stop offset="0.4" stop-color="#242253"/><stop offset="0.52" stop-color="#30295b"/><stop offset="0.6" stop-color="#3c3162"/><stop offset="0.67" stop-color="#483967"/><stop offset="0.74" stop-color="#52406b"/></linearGradient>
<linearGradient id="field" x1="0" y1="0" x2="0" y2="1"><stop offset="0.66" stop-color="#4b4679"/><stop offset="0.82" stop-color="#403c72"/><stop offset="1" stop-color="#37346a"/></linearGradient>
<radialGradient id="rose" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#a8607a" stop-opacity="0.32"/><stop offset="0.2" stop-color="#a45e7a" stop-opacity="0.27"/><stop offset="0.4" stop-color="#9e5c7a" stop-opacity="0.2"/><stop offset="0.6" stop-color="#985a7a" stop-opacity="0.12"/><stop offset="0.8" stop-color="#92587a" stop-opacity="0.05"/><stop offset="1" stop-color="#8c567a" stop-opacity="0"/></radialGradient>
<radialGradient id="lamp" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffb65c" stop-opacity="0.16"/><stop offset="1" stop-color="#ffb65c" stop-opacity="0"/></radialGradient>
<radialGradient id="hush" cx="0.5" cy="0.5" r="0.5"><stop offset="0.55" stop-color="#1b1c4b" stop-opacity="0.85"/><stop offset="1" stop-color="#1b1c4b" stop-opacity="0"/></radialGradient>`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
<rect width="${WIDTH}" height="${HEIGHT}" fill="url(#sky)"/>
<g class="dusk"><ellipse cx="1040" cy="760" rx="760" ry="240" fill="url(#rose)"/></g>
${farForest()}
${snowField()}
${cabin()}
${snowLayer(SNOW_LAYER_FAINT)}
${middleForest()}
${snowLayer(SNOW_LAYER_MIDDLE)}
${nearForest()}
${snowLayer(SNOW_LAYER_BRIGHT)}
<ellipse cx="1370" cy="150" rx="260" ry="170" fill="url(#hush)"/>
</svg>`
}
