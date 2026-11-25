// Night Reef: the Honu Lagoon after dark. The tile mosaics are ANIMALS seen from above (a big turtle and a manta ray)
// that glide along the edges of the window, each over its own halo of light.
// The one idea is bioluminescence: the turtle's shell rim and the ray's edge glow teal, the shell's heart smoulders violet,
// and the plankton they disturb trails behind them in a glowing wake. The water carries a faint grid, and two drifting bands of moonlight at its sides; a low band of reef runs along the bottom right.
// Pure string building: no DOM, nothing brought in from outside, the same output on every call.

type Cell = { x: number; y: number; kind: string }
type Paint = { tile: string; glyph: string; opacity?: number }
type Heading = 'up' | 'down' | 'left' | 'right'

const CELL = 20
const GLYPHS = '$%tSX:;t$%S'
const TEAL = '#4fe6cf'
const TEAL_INK = '#35c4ae'
const VIOLET = '#7a6cff'
const VIOLET_INK = '#9488ff'
// The one warm note, six tiles in all. To take it out, paint kind 'a' like 'q' and drop the tips in reefBand.
const WARM = '#e0a060'
const WARM_INK = '#c98a4c'

/** Tile kinds: what a map letter paints. Glyphs sit one shade off their tile: texture, never text. */
const KINDS: Record<string, Paint> = {
  h: { tile: '#1d7f80', glyph: '#2a9a98' },
  H: { tile: '#27958f', glyph: '#38b0a6' },
  f: { tile: '#176a70', glyph: '#22838a' },
  s: { tile: '#124a56', glyph: '#1b6270' },
  p: { tile: '#4338b0', glyph: '#5247c4' },
  q: { tile: '#5a4de0', glyph: '#6b5ff0' },
  a: { tile: '#a87645', glyph: '#bd8852' },
  r: { tile: '#3a3099', glyph: '#483eae' },
  k: { tile: '#2c2580', glyph: '#3a3296' },
  t: { tile: '#176a70', glyph: '#22838a' },
  m: { tile: '#1d6672', glyph: '#247482' },
  M: { tile: '#258291', glyph: '#2f96a4' },
  u: { tile: '#176a70', glyph: '#22838a', opacity: 0.7 },
  v: { tile: '#176a70', glyph: '#22838a', opacity: 0.45 },
  w: { tile: '#176a70', glyph: '#22838a', opacity: 0.25 },
  x: { tile: '#16305c', glyph: '#1e3c6c' },
  y: { tile: '#1c4468', glyph: '#255478' },
}

/** The big turtle, heading up: a 3 by 3 head on a neck, an octagonal shell nine cells wide with symmetric scutes and two staggered amber spots. No tail: people saw a stem in it. Flippers are separate so they can change pose. */
const TURTLE_BODY = `
........hHh........
........HHH........
........hHh........
.........h.........
........sss........
.......sspss.......
......sspppss......
.....sspqpapss.....
.....spprkrpps.....
.....spqkqkqps.....
.....spprkrpps.....
.....sspapqpss.....
......sspppss......
.......sspss.......
........sss........
`
/** Three poses of the LEFT flippers, all a wide sweep back (about 25, 35 and 45 degrees), never level and never upright. A comma is an empty row. */
const TURTLE_FLIPPERS = [
  `
,
,
,
,
,
,
...fff
fffff
ff
,
,
,
.....f
.....ff
`,
  `
,
,
,
,
,
,
....ff
..fff
ffff
ff
,
,
.....f
.....ff
`,
  `
,
,
,
,
,
,
.....f
...ff
..ff
.ff
ff
f
.....f
.....ff
`,
]

/** The manta ray, heading up: a pointed nose, wings whose tips trail two cells behind the leading edge, a long thin tail that kinks and fades out (t u v w); two poses. */
const MANTA = [
  `
......m......
.....mmm.....
...mmmMmmm...
.mmmmMMMmmmm.
mmmmmMMMmmmmm
mmm.mmMmm.mmm
m....mmm....m
......m......
......t......
......t......
.....u.......
.....u.......
....v........
....w........
`,
  `
......m......
.....mmm.....
..mmmmMmmmm..
mmmmmMMMmmmmm
mmmmmMMMmmmmm
.mm.mmMmm.mm.
.....mmm.....
......m......
......t......
.....t.......
.....u.......
....u........
....v........
...w.........
`,
]

/** A band of reef along the bottom right, three to six cells tall, uneven. */
const CORAL = `
....................yy......
.....yy............yyyy..y..
....yyyy....y.....yyxyyyyyy.
.y.yyxyy...yyy..yyyxxyyxxyy.
yyyyxxyyy.yyxyy.yxyxxyxxxyyy
yxyxxxxyyyyxxxyyyxxxxxxxxxyx
xxxxxxxxxxxxxxxxxxxxxxxxxxxx
`

function hash(a: number, b: number): number {
  let h = (Math.imul(a | 0, 374761393) + Math.imul(b | 0, 668265263)) >>> 0
  h = Math.imul(h ^ (h >>> 13), 1274126177) >>> 0
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296
}

function cellsOf(map: string): Cell[] {
  const cells: Cell[] = []
  const lines = map.split('\n').filter(line => line.length > 0).map(line => (line === ',' ? '' : line))
  lines.forEach((line, y) => {
    for (let x = 0; x < line.length; x += 1) {
      const kind = line[x] ?? '.'
      if (kind !== '.') cells.push({ x, y, kind })
    }
  })
  return cells
}

/** Maps are drawn heading up; this turns the CELLS, so the glyphs stay upright whichever way the animal swims. */
function facing(cells: Cell[], heading: Heading, height: number): Cell[] {
  return cells.map(c => {
    if (heading === 'down') return { x: c.x, y: height - 1 - c.y, kind: c.kind }
    if (heading === 'left') return { x: c.y, y: c.x, kind: c.kind }
    if (heading === 'right') return { x: height - 1 - c.y, y: c.x, kind: c.kind }
    return c
  })
}

function glyphAt(x: number, y: number): string {
  return GLYPHS[(x * 7 + y * 13 + ((x * y) % 3) + 22) % GLYPHS.length] ?? ''
}

function tilePath(list: Cell[]): string {
  return list.map(c => `M${c.x * CELL + 1} ${c.y * CELL + 1}h18v18h-18z`).join('')
}

function glyphRows(list: Cell[], fill: string): string {
  const rows = new Map<number, Cell[]>()
  for (const c of list) {
    const row = rows.get(c.y) ?? []
    row.push(c)
    rows.set(c.y, row)
  }
  let out = ''
  for (const [y, row] of rows) {
    const xs = row.map(c => c.x * CELL + 10).join(' ')
    const text = row.map(c => glyphAt(c.x, y)).join('')
    out += `<text x="${xs}" y="${y * CELL + 15}" fill="${fill}">${text}</text>`
  }
  return out
}

/** Tiles of one kind in a single path; glyphs in one text per row with a per-glyph x list. */
function mosaic(cells: Cell[]): string {
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
    const faded = paint.opacity === undefined ? '' : ` opacity="${paint.opacity}"`
    out += `<g${faded}><path d="${tilePath(list)}" fill="${paint.tile}" stroke="#aab8ff" stroke-opacity="0.06"/>${glyphRows(list, paint.glyph)}</g>`
  }
  return out
}

/** Cells on the outside of a shape: where an animal's glow lives. */
function edgeCells(cells: Cell[]): Cell[] {
  const filled = new Set(cells.map(c => `${c.x},${c.y}`))
  return cells.filter(c => !filled.has(`${c.x + 1},${c.y}`) || !filled.has(`${c.x - 1},${c.y}`) || !filled.has(`${c.x},${c.y + 1}`) || !filled.has(`${c.x},${c.y - 1}`))
}

/** A set of tiles that glow together: tile, a glyph one shade off it, one slow eased clock. */
function litGroup(list: Cell[], className: string, colour: string, ink: string, seconds: number, delay: number): string {
  if (list.length === 0) return ''
  return `<g class="${className}" style="animation-duration:${seconds}s;animation-delay:-${delay.toFixed(1)}s"><path d="${tilePath(list)}" fill="${colour}"/>${glyphRows(list, ink)}</g>`
}

/** Teal along an edge: groups whose clocks are spread evenly round one cycle, so part is always lit and nothing pops. */
function tealEdge(cells: Cell[], share: number, seconds: number, seed: number, groupCount: number): string {
  const groups: Cell[][] = []
  for (let i = 0; i < groupCount; i += 1) groups.push([])
  for (const c of cells) {
    // Neighbours in a 2 by 2 block mostly share a group, so the glow comes in short runs along the edge.
    const pick = hash(Math.floor(c.x / 2) + seed, Math.floor(c.y / 2) * 3) * 0.7 + hash(c.x + seed, c.y) * 0.3
    if (pick < share) groups[Math.floor((pick / share) * groupCount)]?.push(c)
  }
  return groups.map((list, i) => litGroup(list, 'rim', TEAL, TEAL_INK, seconds, (i * seconds) / groupCount)).join('')
}

/** Violet in the shell's heart: the bright scutes smoulder, centre and ring on two clocks, never out. */
function violetHeart(cells: Cell[], centreX: number, centreY: number): string {
  const scutes = cells.filter(c => c.kind === 'q')
  const inner = scutes.filter(c => Math.abs(c.x - centreX) + Math.abs(c.y - centreY) <= 1)
  const outer = scutes.filter(c => Math.abs(c.x - centreX) + Math.abs(c.y - centreY) > 1)
  const spine = cells.filter(c => c.kind === 'a')
  return litGroup(inner, 'ember', VIOLET, VIOLET_INK, 17, 0) + litGroup(outer, 'ember', VIOLET, VIOLET_INK, 23, 9) + litGroup(spine, 'ember', WARM, WARM_INK, 19, 3)
}

/** The glowing wake: plankton stirred up behind an animal. Drawn for an animal heading up (wake below it), then turned like the cells.
 *  Three bands, each dimmer and wider than the last, so it fades without a gradient. */
function wake(widthCells: number, heightCells: number, lengthCells: number, heading: Heading, seed: number): string {
  const bands = ['', '', '']
  const centre = (widthCells * CELL) / 2
  const count = lengthCells * 6
  for (let i = 0; i < count; i += 1) {
    const along = Math.pow(hash(seed, i), 1.4)
    const spread = (0.2 + along * 0.4) * widthCells * CELL
    const px = Math.round(centre + (hash(seed + 1, i) - 0.5) * spread)
    const py = Math.round(heightCells * CELL - 30 + along * lengthCells * CELL)
    const size = hash(seed + 2, i) < 0.3 ? 3 : 2
    const x = heading === 'left' ? py : px
    const y = heading === 'down' ? heightCells * CELL - py : heading === 'left' ? px : py
    const band = Math.min(2, Math.floor(along * 3))
    bands[band] = (bands[band] ?? '') + `M${x} ${y}h${size}v${size}h-${size}z`
  }
  const strength = [0.85, 0.55, 0.3]
  return bands.map((d, i) => `<path class="speck" style="animation-duration:${7 + i * 2}s;animation-delay:-${i * 2.7}s" d="${d}" fill="${TEAL}" fill-opacity="${strength[i] ?? 0}"/>`).join('')
}

/** Poses shown one at a time. With three poses the order is 0 1 2 1, so limbs sweep back and forth. */
function posed(poses: string[], seconds: number): string {
  const className = poses.length === 3 ? ['pose3a', 'pose3b', 'pose3c'] : ['pose2a', 'pose2b']
  return poses.map((body, i) => `<g class="${className[i] ?? ''}" style="animation-duration:${seconds}s">${body}</g>`).join('')
}

/** One stroke phase: the left flippers in one pose, the right in another, so the animal is never a mirror image of itself. */
function strokePhase(left: number, right: number): Cell[] {
  const leftCells = cellsOf(TURTLE_FLIPPERS[left] ?? '')
  const rightCells = cellsOf(TURTLE_FLIPPERS[right] ?? '').map(c => ({ x: 18 - c.x, y: c.y, kind: c.kind }))
  return leftCells.concat(rightCells)
}

/** A few dash-ripples close around an animal: the water it has just disturbed. */
function nearRipples(width: number, height: number, count: number, seed: number): string {
  let d = ''
  for (let i = 0; i < count; i += 1) {
    const x = Math.round((-90 + hash(seed, i) * (width + 180)) / 20) * 20 + 6
    const y = Math.round((-70 + hash(seed + 1, i) * (height + 140)) / 20) * 20 + 9
    d += `M${x} ${y}h8v2h-8z`
  }
  return `<path class="speck" style="animation-duration:11s" d="${d}" fill="#5fd0c8" fill-opacity="0.4"/>`
}

/** The turtle facing one way. The two long legs of its lap get everything; the short turns get one pose and no glow, to save characters. */
function bigTurtle(heading: Heading, full: boolean): string {
  const height = 15
  const body = facing(cellsOf(TURTLE_BODY), heading, height)
  const strokes = [strokePhase(0, 2), strokePhase(1, 1), strokePhase(2, 0)].map(cells => facing(cells, heading, height))
  if (!full) return `<g transform="translate(40 -40)">${mosaic(strokes[1] ?? [])}${mosaic(body)}</g>`
  const shellRim = body.filter(c => c.kind === 's')
  return `${wake(19, height, 11, heading, 500)}${posed(strokes.map(mosaic), 7)}${mosaic(body)}${violetHeart(body, 9, 9)}${tealEdge(shellRim, 0.7, 12, 0, 6)}`
}

/** The turtle's lap: down the right gutter, a short turn, back up, a short turn. Each heading is shown only on its own leg. */
function turtleLap(): string {
  const glow = `<ellipse class="halo" cx="190" cy="160" rx="300" ry="300" fill="url(#tealglow)"/><ellipse class="halo" style="animation-delay:-4s" cx="190" cy="150" rx="170" ry="180" fill="url(#violetglow)"/>`
  return `${glow}${nearRipples(380, 300, 16, 801)}<g class="legdown">${bigTurtle('down', true)}</g><g class="legleft">${bigTurtle('left', false)}</g><g class="legup">${bigTurtle('up', true)}</g><g class="legright">${bigTurtle('right', false)}</g>`
}

/** The ray's body cells, without its tail: only these glow. */
function isRayBody(cell: Cell): boolean {
  return 'mM'.includes(cell.kind)
}

/** The ray facing one way; like the turtle, the short turns get one pose and no glow. */
function manta(heading: Heading, full: boolean): string {
  const height = 14
  const poses = MANTA.map(map => facing(cellsOf(map), heading, height))
  if (!full) return `<g transform="translate(-10 10)">${mosaic(poses[0] ?? [])}</g>`
  // Under the sidebar's blur only mass and outline survive, so nearly the whole edge glows, on two clocks.
  const tiles = poses.map(cells => mosaic(cells) + tealEdge(edgeCells(cells).filter(isRayBody), 0.9, 14, 70, 2))
  return `${wake(13, height, 6, heading, 600)}${posed(tiles, 9)}`
}

/** The ray's lap, low on the far left: up, a short turn, down two cells further in, a short turn. It never leaves, so the frame is never one animal and empty water. */
function rayLap(): string {
  const glow = `<ellipse class="halo" style="animation-delay:-5s" cx="130" cy="110" rx="280" ry="240" fill="url(#tealglow)"/>`
  return `${glow}${nearRipples(260, 180, 12, 811)}<g class="legdown">${manta('up', true)}</g><g class="legleft">${manta('right', false)}</g><g class="legup">${manta('down', true)}</g><g class="legright">${manta('left', false)}</g>`
}

/** The reef band: dark tiles, a few teal anemones pulsing low down, and four single amber tips, never two side by side. */
function reefBand(column: number, row: number): string {
  const cells = cellsOf(CORAL).map(c => ({ x: c.x + column, y: c.y + row, kind: c.kind }))
  const filled = new Set(cells.map(c => `${c.x},${c.y}`))
  const anemones = cells.filter(c => c.y > row + 2 && hash(c.x * 3 + 9, c.y * 11) < 0.08)
  const tips = cells.filter(c => !filled.has(`${c.x},${c.y - 1}`) && c.x % 6 === 2).slice(0, 4)
  return mosaic(cells) + litGroup(anemones, 'rim', TEAL, TEAL_INK, 12, 2) + litGroup(tips, 'ember', WARM, WARM_INK, 19, 5)
}

/** Plankton: a swarm of small square specks that drifts in one body; three sub-groups twinkle on their own clocks; a few bright ones carry a halo. */
function swarm(centreX: number, centreY: number, radiusX: number, radiusY: number, count: number, seed: number, driftSeconds: number, driftX: number, driftY: number): string {
  const parts = ['', '', '']
  let violet = ''
  let halos = ''
  let bright = ''
  for (let i = 0; i < count; i += 1) {
    const angle = hash(seed, i * 2) * Math.PI * 2
    const reach = Math.pow(hash(seed, i * 2 + 1), 0.8)
    const x = Math.round(centreX + Math.cos(angle) * radiusX * reach)
    const y = Math.round(centreY + Math.sin(angle) * radiusY * reach)
    const roll = hash(seed + 7, i)
    if (roll < 0.1) {
      halos += `<circle cx="${x + 2}" cy="${y + 2}" r="11" fill="url(#speckhalo)"/>`
      bright += `M${x} ${y}h4v4h-4z`
    } else if (roll < 0.36) {
      violet += `M${x} ${y}h3v3h-3z`
    } else {
      const size = roll < 0.6 ? 3 : roll < 0.85 ? 2 : 1.5
      parts[i % 3] = (parts[i % 3] ?? '') + `M${x} ${y}h${size}v${size}h-${size}z`
    }
  }
  const specks = parts.map((d, i) => `<path class="speck" style="animation-duration:${7 + i * 2}s;animation-delay:-${(hash(seed, 90 + i) * 9).toFixed(1)}s" d="${d}" fill="${TEAL}"/>`).join('')
  const soft = `<path class="speck" style="animation-duration:10s;animation-delay:-${(hash(seed, 95) * 9).toFixed(1)}s" d="${violet}" fill="#8b7bff"/>`
  const stars = `<g class="speck" style="animation-duration:11s;animation-delay:-${(hash(seed, 99) * 11).toFixed(1)}s">${halos}<path d="${bright}" fill="#b8fff0"/></g>`
  return `<g class="drift" style="animation-duration:${driftSeconds}s;animation-delay:-${(hash(seed, 77) * driftSeconds).toFixed(0)}s;--dx:${driftX}px;--dy:${driftY}px">${specks}${soft}${stars}</g>`
}

/** A thin scatter of the faintest specks through the reading column, so the middle is water and not a hole. */
function middleScatter(): string {
  let d = ''
  for (let i = 0; i < 18; i += 1) d += `M${Math.round(470 + hash(51, i) * 700)} ${Math.round(60 + hash(52, i) * 860)}h1.5v1.5h-1.5z`
  return `<path class="speck" style="animation-duration:13s" d="${d}" fill="${TEAL}" fill-opacity="0.3"/>`
}

/** Grain: a tile of barely visible light and dark pixels that dithers the dark gradient so it cannot band. */
function grainPattern(): string {
  let light = ''
  let dark = ''
  for (let i = 0; i < 150; i += 1) {
    const x = Math.floor(hash(11, i) * 48) * 2
    const y = Math.floor(hash(12, i) * 48) * 2
    if (i % 2 === 0) light += `M${x} ${y}h2v2h-2z`
    else dark += `M${x} ${y}h2v2h-2z`
  }
  return `<pattern id="grain" width="96" height="96" patternUnits="userSpaceOnUse"><path d="${light}" fill="#9db4ff" fill-opacity="0.022"/><path d="${dark}" fill="#000" fill-opacity="0.09"/></pattern>`
}

export function nightReefSvg(): string {
  // The animals GLIDE: their laps are plain linear keyframes, no stepping and no held frames (a cell per step read like a stalled screen in the real app).
  // The four upright drawings of a lap, and the limb poses, cross-fade over about 0.4 s instead of snapping.
  // Delays are chosen so that time zero is a good composition. The still a reduced-motion user sees is set apart from it:
  // the resting place of each animal and its one visible pose stand in the PLAIN style: the app can stop a scene by taking every
  // animation away, and what only keyframes place would fall to the top of the window. The keyframes name every moment of the run.
  const style = `
text{font:700 13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;text-anchor:middle}
.rim{opacity:.5;animation:rim 12s ease-in-out infinite}
.ember{opacity:.7;animation:ember 17s ease-in-out infinite}
.halo{animation:halo 9s ease-in-out infinite}
.speck{opacity:.6;animation:speck 9s ease-in-out infinite}
.drift{animation:drift 55s ease-in-out infinite alternate}
.caustic{animation:caustic 110s ease-in-out infinite alternate}
.turtleway{animation:turtleway 128s linear infinite;animation-delay:-78s}
.legdown{animation:legdown 128s linear infinite;animation-delay:-78s}.legleft{animation:legleft 128s linear infinite;animation-delay:-78s}.legup{animation:legup 128s linear infinite;animation-delay:-78s}.legright{animation:legright 128s linear infinite;animation-delay:-78s}
.rayway{animation:rayway 128s linear infinite;animation-delay:-30s}.raylegs g{animation-delay:-30s}
.pose3a{animation:pose3a 8s linear infinite}.pose3b{animation:pose3b 8s linear infinite}.pose3c{animation:pose3c 8s linear infinite}
.pose2a{animation:pose2a 6s linear infinite}.pose2b{animation:pose2b 6s linear infinite}
@keyframes pose3a{0%{opacity:1}20%{opacity:1}25%{opacity:0}95%{opacity:0}100%{opacity:1}}
@keyframes pose3b{0%{opacity:0}20%{opacity:0}25%{opacity:1}45%{opacity:1}50%{opacity:0}70%{opacity:0}75%{opacity:1}95%{opacity:1}100%{opacity:0}}
@keyframes pose3c{0%{opacity:0}45%{opacity:0}50%{opacity:1}70%{opacity:1}75%{opacity:0}100%{opacity:0}}
@keyframes pose2a{0%{opacity:1}45%{opacity:1}50%{opacity:0}95%{opacity:0}100%{opacity:1}}
@keyframes pose2b{0%{opacity:0}45%{opacity:0}50%{opacity:1}95%{opacity:1}100%{opacity:0}}
@keyframes rim{0%,100%{opacity:.14}50%{opacity:.95}}
@keyframes ember{0%,100%{opacity:.35}50%{opacity:.9}}
@keyframes halo{0%,100%{opacity:.5}50%{opacity:1}}
@keyframes speck{0%,100%{opacity:.28}50%{opacity:1}}
@keyframes drift{from{transform:translate(0,0)}to{transform:translate(var(--dx),var(--dy))}}
@keyframes caustic{from{transform:translate(-90px,0)}to{transform:translate(90px,0)}}
@keyframes turtleway{0%{transform:translate(0,290px)}43.75%{transform:translate(0,570px)}50%{transform:translate(-40px,570px)}93.75%{transform:translate(-40px,290px)}100%{transform:translate(0,290px)}}
@keyframes rayway{0%{transform:translate(0,700px)}43.75%{transform:translate(0,420px)}50%{transform:translate(40px,420px)}93.75%{transform:translate(40px,700px)}100%{transform:translate(0,700px)}}
@keyframes legdown{0%{opacity:1}43.59%{opacity:1}43.91%{opacity:0}99.7%{opacity:0}100%{opacity:1}}
@keyframes legleft{0%{opacity:0}43.59%{opacity:0}43.91%{opacity:1}49.84%{opacity:1}50.16%{opacity:0}100%{opacity:0}}
@keyframes legup{0%{opacity:0}49.84%{opacity:0}50.16%{opacity:1}93.59%{opacity:1}93.91%{opacity:0}100%{opacity:0}}
@keyframes legright{0%{opacity:0}93.59%{opacity:0}93.91%{opacity:1}99.7%{opacity:1}100%{opacity:0}}
.pose3a,.pose3c,.pose2b,.legleft,.legdown,.legright{opacity:0}.turtleway{transform:translate(-40px,440px)}.rayway{transform:translate(40px,520px)}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  const defs = `
<radialGradient id="water" gradientUnits="userSpaceOnUse" cx="720" cy="420" r="1050"><stop offset="0" stop-color="#1b2d5a"/><stop offset="0.3" stop-color="#13224a"/><stop offset="0.6" stop-color="#0a1430"/><stop offset="0.85" stop-color="#060c1f"/><stop offset="1" stop-color="#040816"/></radialGradient>
<linearGradient id="caustic" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6f8fd6" stop-opacity="0"/><stop offset="0.5" stop-color="#6f8fd6" stop-opacity="0.085"/><stop offset="1" stop-color="#6f8fd6" stop-opacity="0"/></linearGradient>
<radialGradient id="deep" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#0d3a56" stop-opacity="0.6"/><stop offset="0.35" stop-color="#0d3a56" stop-opacity="0.34"/><stop offset="0.7" stop-color="#0d3a56" stop-opacity="0.1"/><stop offset="1" stop-color="#0d3a56" stop-opacity="0"/></radialGradient>
<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M0 0.5h20M0.5 0v20" stroke="#9db4ff" stroke-opacity="0.045" fill="none"/></pattern>
<linearGradient id="edgeward" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0.9"/><stop offset="0.24" stop-color="#fff" stop-opacity="0"/><stop offset="0.74" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient>
<mask id="edges" maskUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1000"><rect width="1600" height="1000" fill="url(#edgeward)"/></mask>

<radialGradient id="tealglow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="${TEAL}" stop-opacity="0.24"/><stop offset="0.25" stop-color="${TEAL}" stop-opacity="0.15"/><stop offset="0.5" stop-color="${TEAL}" stop-opacity="0.07"/><stop offset="0.75" stop-color="${TEAL}" stop-opacity="0.02"/><stop offset="1" stop-color="${TEAL}" stop-opacity="0"/></radialGradient>
<radialGradient id="violetglow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="${VIOLET}" stop-opacity="0.2"/><stop offset="0.3" stop-color="${VIOLET}" stop-opacity="0.11"/><stop offset="0.6" stop-color="${VIOLET}" stop-opacity="0.04"/><stop offset="1" stop-color="${VIOLET}" stop-opacity="0"/></radialGradient>
<radialGradient id="speckhalo" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="${TEAL}" stop-opacity="0.5"/><stop offset="0.4" stop-color="${TEAL}" stop-opacity="0.14"/><stop offset="1" stop-color="${TEAL}" stop-opacity="0"/></radialGradient>
${grainPattern()}`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
<rect width="1600" height="1000" fill="url(#water)"/>
<g transform="skewX(-28)"><rect class="caustic" x="170" y="-20" width="280" height="1040" fill="url(#caustic)"/><rect class="caustic" style="animation-duration:95s;animation-delay:-20s;animation-direction:alternate-reverse" x="1420" y="-20" width="320" height="1040" fill="url(#caustic)"/></g>
<ellipse cx="1640" cy="1040" rx="900" ry="640" fill="url(#deep)"/>
<rect width="1600" height="1000" fill="url(#grid)" opacity="0.35"/><rect width="1600" height="1000" fill="url(#grid)" mask="url(#edges)"/>
<rect width="1600" height="1000" fill="url(#grain)"/>
${swarm(1330, 700, 190, 120, 48, 1, 61, -70, 30)}${swarm(1480, 880, 110, 90, 36, 2, 47, 60, -40)}${swarm(1180, 950, 150, 40, 30, 6, 67, 80, -14)}${swarm(210, 880, 210, 90, 46, 5, 53, 76, -30)}${middleScatter()}
${reefBand(64, 44)}
<g class="rayway"><g class="raylegs" transform="translate(${3 * CELL} 0)">${rayLap()}</g></g>
<g class="turtleway"><g transform="translate(${62 * CELL} 0)">${turtleLap()}</g></g>
</svg>`
}

