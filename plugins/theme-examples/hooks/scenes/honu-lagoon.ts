// Honu Lagoon: a lagoon seen from above on a cell grid: every tile is a
// square with a glyph in it. A turtle (honu) swims in its own clear water on the right, a smaller coral animal drifts by the
// sidebar's edge, a sand island with trails of sand tiles fills the top right corner, a shoal lies along the bottom.
// It is a LIGHT-window scene. Pure string building, the same every time: animals and land are drawn from geometry,
// rasterised onto the grid.
const CELL = 15
const COLUMNS = Math.ceil(1600 / CELL)
const ROWS = Math.ceil(1000 / CELL)
const GLYPHS = '$%tSX:;t$%S'

type Cell = { x: number; y: number; kind: string; body?: boolean }
type Paint = { tile: string; glyph: string; opacity: number }
type Heading = readonly [number, number]

/** Tile kinds: what each letter paints. Glyphs are tone on tone; sand fades toward the tips by colour AND a little by opacity. */
const KINDS: Record<string, Paint> = {
  q: { tile: '#ef7f8e', glyph: '#fbc4cb', opacity: 1 },
  p: { tile: '#e2486c', glyph: '#f6a0b2', opacity: 1 },
  r: { tile: '#d93a63', glyph: '#f28a9f', opacity: 1 },
  R: { tile: '#c22a52', glyph: '#ee7790', opacity: 1 },
  o: { tile: '#e8873a', glyph: '#fbd3a4', opacity: 1 },
  k: { tile: '#9c1f3d', glyph: '#de6c86', opacity: 1 },
  a: { tile: '#f2cf3a', glyph: '#b58f1c', opacity: 1 },
  b: { tile: '#f2d54e', glyph: '#bb9a2c', opacity: 1 },
  c: { tile: '#f3df7a', glyph: '#c2a646', opacity: 0.95 },
  d: { tile: '#f3e6a0', glyph: '#c8b878', opacity: 0.9 },
  g: { tile: '#8f9a52', glyph: '#c3cc8c', opacity: 1 },
  w: { tile: '#b8a85a', glyph: '#8a7c3c', opacity: 1 },
  l: { tile: '#e9d28a', glyph: '#b79d52', opacity: 1 },
  m: { tile: '#d9bd6a', glyph: '#a58a3c', opacity: 1 },
  n: { tile: '#a8923c', glyph: '#75642a', opacity: 1 },
  v: { tile: '#a8964c', glyph: '#75682e', opacity: 1 },
  f: { tile: '#f5efcf', glyph: '#c9c09a', opacity: 0.6 },
  u: { tile: '#e9d9a0', glyph: '#a98f4a', opacity: 0.75 },
}

function hash(x: number, y: number): number {
  let h = (x * 374761393 + y * 668265263) >>> 0
  h = ((h ^ (h >>> 13)) * 1274126177) >>> 0
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296
}

/** How far a point is from a line segment, and how far along it the nearest point lies. */
function distanceToSegment(px: number, py: number, ax: number, ay: number, bx: number, by: number): { distance: number; along: number } {
  const dx = bx - ax
  const dy = by - ay
  const along = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
  return { distance: Math.hypot(px - ax - along * dx, py - ay - along * dy), along }
}

/**
 * The cells of a turtle seen from above. `heading` is the unit vector it swims along; `size` scales it (1 = the big one);
 * `sweep` is how far the front flippers are swept back, in degrees from straight out (0) to along the body (90).
 * Everything is tested in the turtle's own frame: `a` along the heading, `b` across it.
 */
function turtleCells(heading: Heading, size: number, sweep: number, surge: number): Cell[] {
  const [ux, uy] = heading
  const vx = uy
  const vy = -ux
  const reach = Math.ceil(19 * size)
  const cells: Cell[] = []
  const angle = ((90 - sweep) * Math.PI) / 180
  for (let y = -reach; y <= reach; y += 1) {
    for (let x = -reach; x <= reach; x += 1) {
      const a = (x * ux + y * uy) / size - surge
      const b = (x * vx + y * vy) / size
      const shell = (a / 5.6) ** 2 + (b / 4.4) ** 2
      if (shell <= 1) {
        const pick = hash(x + 91, y + 17)
        // A spine of dark scutes down the middle gives the shell an axis; the rim is ragged where a pale tile drops out.
        const spine = Math.abs(b) <= 1.3 && Math.abs(a) <= 4.2
        if (shell > 0.82 && pick < 0.1) continue
        const kind = spine ? (Math.round(a) % 2 === 0 ? 'k' : 'R') : shell < 0.5 ? (pick < 0.14 ? 'o' : pick < 0.6 ? 'r' : 'R') : shell < 0.85 ? (pick < 0.7 ? 'r' : 'p') : pick < 0.3 ? 'q' : 'p'
        cells.push({ x, y, kind, body: true })
        continue
      }
      // The head and its neck: solid sand, in line with the body, so the leading end is plain to see.
      if (a > 5.2 && a <= 7.6 && Math.abs(b) <= 1.1) {
        cells.push({ x, y, kind: 'a', body: true })
        continue
      }
      if (Math.hypot(a + 6.2, b) <= 0.7) {
        cells.push({ x, y, kind: 'c' })
        continue
      }
      let limb: number | undefined
      for (const side of [1, -1]) {
        const front = distanceToSegment(a, b, 3.3, side * 4.3, 3.3 - 4.5 * Math.cos(angle), side * (4.3 + 4.5 * Math.sin(angle)))
        if (front.distance <= 1.05) limb = front.along
        const back = distanceToSegment(a, b, -4.3, side * 3.3, -4.3 - 1.6 * Math.cos(0.8), side * (3.3 + 1.6 * Math.sin(0.8)))
        if (back.distance <= 0.75) limb = 0.3 + back.along * 0.5
      }
      if (limb !== undefined) cells.push({ x, y, kind: limb < 0.55 ? 'a' : limb < 0.85 ? 'b' : 'c' })
    }
  }
  return cells
}

/** The second animal, like the clip's: mid-size, coral only, a rounded body with a blunt snout and two stubby fins. */
function coralCells(): Cell[] {
  const cells: Cell[] = []
  for (let y = -5; y <= 5; y += 1) {
    for (let x = -5; x <= 6; x += 1) {
      const body = (x / 3.1) ** 2 + ((y - 0.3) / 2.6) ** 2
      const head = x >= 3 && x <= 4 && Math.abs(y) <= 1
      const fin = (x === -1 || x === 0) && (y === -3 || y === 3 || y === 4)
      if (body > 1 && !head && !fin) continue
      const pick = hash(x + 33, y + 71)
      const kind = head ? 'p' : body < 0.2 ? 'R' : body < 0.6 ? (pick < 0.5 ? 'r' : 'p') : pick < 0.55 ? 'p' : 'q'
      cells.push({ x, y, kind, body: true })
    }
  }
  return cells
}

/** Where each sand trail starts (column, row), how many rows it runs, and the row at which it kinks. */
const TRAILS: readonly (readonly [number, number, number, number])[] = [
  [COLUMNS - 30, 4, 7, 3],
  [COLUMNS - 13, 5, 19, 9],
  [COLUMNS - 4, 5, 11, 5],
]

/** One cell of the island, unless something already stands there or it is off the grid. */
function putCell(cells: Cell[], taken: Set<string>, x: number, y: number, kind: string): void {
  if (x < 0 || y < 0 || x >= COLUMNS || taken.has(`${x},${y}`)) return
  taken.add(`${x},${y}`)
  cells.push({ x, y, kind })
}

/**
 * The island in the top right corner: an uneven blob whose top rows are olive and khaki and whose shore is pale sand, with
 * foam on its left tip, and three diagonal trails of fading sand tiles running down and left toward the turtle's water.
 */
function islandCells(): Cell[] {
  const cells: Cell[] = []
  const taken = new Set<string>()
  const middle = COLUMNS - 15
  for (let y = 0; y < 7; y += 1) {
    for (let x = COLUMNS - 36; x < COLUMNS; x += 1) {
      const depth = 4.4 + Math.sin(x / 2.7) * 1.2 + (hash(x, 400) - 0.5) * 1.6 - Math.max(0, COLUMNS - 30 - x) * 0.5
      if (y > depth) continue
      const pick = hash(x + 5, y + 900)
      const heart = Math.hypot((x - middle) / 7, (y - 1.5) / 2.2)
      const kind = heart < 1 && pick < 0.22 ? (pick < 0.08 ? 'g' : pick < 0.15 ? 'w' : 'v') : y >= depth - 0.9 ? (x < COLUMNS - 29 ? 'f' : 'd') : y === 0 ? (pick < 0.5 ? 'n' : 'm') : pick < 0.45 ? 'a' : pick < 0.8 ? 'l' : 'm'
      putCell(cells, taken, x, y, kind)
    }
  }
  // Three trails of sand running down and left in staggered clumps two to four cells wide, each with one kink; the longest
  // passes within a cell of the turtle's home, so the animal seems to trail sand behind it.
  for (const [startX, startY, length, kinkAt] of TRAILS) {
    let x = startX
    for (let step = 0; step < length; step += 1) {
      const share = step / length
      const kind = share < 0.4 ? 'a' : share < 0.75 ? 'b' : 'c'
      const width = 3 + Math.floor(hash(startX + step, 31) * 2)
      const shift = hash(startX, step + 9) < 0.4 ? 1 : 0
      for (let across = 0; across < Math.max(1, width); across += 1) putCell(cells, taken, x + across - shift, startY + step, kind)
      x -= step === kinkAt ? 2 : step % 3 === 2 ? 0 : 1
    }
  }
  return cells
}

/** A low bank of sand tiles along the bottom right, clear of the prompt box. */
function shoalCells(): Cell[] {
  const cells: Cell[] = []
  for (let y = ROWS - 7; y < ROWS; y += 1) {
    for (let x = COLUMNS - 45; x < COLUMNS - 1; x += 1) {
      const height = 3.6 + Math.sin(x / 3.1) * 1.4 + (hash(x, 77) - 0.5) * 2 - Math.max(0, COLUMNS - 38 - x) * 0.35
      if (ROWS - y <= height) cells.push({ x, y: y - 2, kind: 'u' })
    }
  }
  return cells
}

function glyphAt(x: number, y: number): string {
  return GLYPHS[Math.floor(hash(x + 7, y + 3) * GLYPHS.length)] ?? '$'
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
    const path = list.map(c => `M${c.x * CELL + 1} ${c.y * CELL + 1}h${CELL - 2}v${CELL - 2}h-${CELL - 2}z`).join('')
    let group = `<path d="${path}" fill="${paint.tile}" stroke="#fff" stroke-opacity="0.24"/>`
    const rows = new Map<number, Cell[]>()
    for (const c of list) {
      const row = rows.get(c.y) ?? []
      row.push(c)
      rows.set(c.y, row)
    }
    for (const [y, row] of rows) {
      group += `<text x="${row.map(c => c.x * CELL + CELL / 2).join(' ')}" y="${y * CELL + 11}" fill="${paint.glyph}">${row.map(c => glyphAt(c.x, y)).join('')}</text>`
    }
    out += paint.opacity === 1 ? group : `<g opacity="${paint.opacity}">${group}</g>`
  }
  return out
}

/** One flat silhouette of the cells, grown by `grow` cells when a shadow should be broad. */
function silhouette(cells: Cell[], grow: number, fill: string, opacity: number): string {
  const seen = new Set<string>()
  for (const c of cells) {
    for (let dy = -grow; dy <= grow; dy += 1) {
      for (let dx = -grow; dx <= grow; dx += 1) {
        if (Math.abs(dx) + Math.abs(dy) <= grow) seen.add(`${(c.x + dx) * CELL} ${(c.y + dy) * CELL}`)
      }
    }
  }
  const d = [...seen].map(key => `M${key}h${CELL}v${CELL}h-${CELL}z`).join('')
  return `<path d="${d}" fill="${fill}" opacity="${opacity}"/>`
}

/** What lies under an animal: its shadow, `offset` cells right and down, and a dark underside for the body. */
function under(cells: Cell[], shadowOpacity: number, offset: number): string {
  const body = cells.filter(c => c.body === true)
  return `<g transform="translate(${CELL * offset} ${CELL * offset})">${silhouette(cells, 0, '#0a6aa6', shadowOpacity)}</g><g transform="translate(0 2)">${silhouette(body, 0, '#7a1230', 0.5)}</g>`
}

/** The stroke: how far the front flippers are swept back in each pose, and whether the shell has surged a cell forward. */
const STROKE: readonly (readonly [number, number])[] = [
  [-45, 0],
  [20, 1],
  [85, 1],
  [20, 0],
]

/** The turtle: four stroke poses taking turns, the tips moving two cells at most from one to the next. */
function turtle(across: string, along: string, heading: Heading, size: number, beat: number): string {
  const poses = STROKE.map(
    ([sweep, surge], index) => `<g class="pose" style="animation-duration:${beat}s;animation-delay:-${(beat * (4 - index)) / 4}s">${under(turtleCells(heading, size, sweep, surge), 0.38, 3)}${mosaic(turtleCells(heading, size, sweep, surge))}</g>`,
  )
  return `<g class="${across}"><g class="${along}">${poses.join('')}</g></g>`
}

/** Each patch of deeper water: column, row, width and height in cells. All of them lie right of the reading column. */
const PATCHES: readonly (readonly [number, number, number, number])[] = [
  [84, 8, 20, 9],
  [82, 22, 26, 12],
  [86, 44, 22, 14],
  [80, 56, 28, 9],
  [92, 32, 16, 9],
]

/** Large, faint stepped patches of deeper water: the only tile-shaped edges the water has, and none of them hard. */
function patches(): string {
  let d = ''
  for (const [column, row, width, height] of PATCHES) {
    for (let y = 0; y < height; y += 1) {
      const inset = Math.round(Math.abs(y - height / 2) * 0.9 + (hash(column + y, row) - 0.5) * 3)
      const run = Math.max(2, width - inset * 2) * CELL
      d += `M${(column + inset) * CELL} ${(row + y) * CELL}h${run}v${CELL}h-${run}z`
    }
  }
  return `<path d="${d}" fill="#0f7fb8" opacity="0.075"/>`
}

/** A few sand tiles that dim and return, so the land is not frozen: a pale veil over about one tile in eighteen. */
function twinkle(cells: Cell[]): string {
  let out = ''
  for (const c of cells) {
    const pick = hash(c.x + 61, c.y + 13)
    if (pick > 0.055) continue
    out += `<rect class="dim" style="animation-duration:${9 + Math.floor(pick * 90)}s;animation-delay:-${Math.floor(hash(c.x, c.y + 5) * 12)}s" x="${c.x * CELL + 1}" y="${c.y * CELL + 1}" width="${CELL - 2}" height="${CELL - 2}" fill="#8fdbe6"/>`
  }
  return out
}

function sparkle(x: number, y: number, size: number, delay: number, seconds: number): string {
  return `<circle class="star" style="animation-delay:-${delay}s;animation-duration:${seconds}s" cx="${x}" cy="${y}" r="${size}" fill="#fff"/>`
}

function glints(id: string, cx: number, cy: number, rx: number, ry: number, seconds: number, delay: number): string {
  return `<g class="glints" style="animation-duration:${seconds + 9}s;animation-delay:-${delay}s"><ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="url(#dots)" mask="url(#${id})"/></g>`
}

export function honuLagoonSvg(): string {
  // Each animal's home and its one visible pose stand in the PLAIN style (the first keyframe's place): the app can stop a scene by
  // taking every animation away, and what only keyframes place would fall to the top left corner, or not show at all.
  const style = `
text{font:800 ${CELL - 4}px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;text-anchor:middle}
.pose{opacity:0;animation:turn 22s linear infinite}
.star{animation:twinkle 9s ease-in-out infinite}
.dim{opacity:0;animation:dim 11s ease-in-out infinite alternate}
.glints{animation:breathe 20s ease-in-out infinite alternate}
.field{animation:drift 52s ease-in-out infinite alternate}
.honuX{animation:honuX 170s infinite}.honuY{animation:honuY 170s infinite}
.coralY{animation:coralY 90s infinite}
@keyframes turn{0%{opacity:0}1.8%{opacity:1}25%{opacity:1}26.8%{opacity:0}100%{opacity:0}}
@keyframes twinkle{0%,100%{opacity:0}50%{opacity:.8}}
@keyframes breathe{from{opacity:.3}to{opacity:1}}
@keyframes dim{from{opacity:0}to{opacity:.3}}
@keyframes drift{from{transform:translate(-40px,-12px)}to{transform:translate(40px,12px)}}
@keyframes honuX{0%{transform:translateX(${91 * CELL}px);animation-timing-function:ease-in-out}45%{transform:translateX(${95 * CELL}px);animation-timing-function:ease-in-out}100%{transform:translateX(${91 * CELL}px)}}
@keyframes honuY{0%{transform:translateY(${32 * CELL}px);animation-timing-function:ease-in-out}45%{transform:translateY(${44 * CELL}px);animation-timing-function:ease-in-out}100%{transform:translateY(${32 * CELL}px)}}
@keyframes coralY{0%{transform:translate(${10 * CELL}px,${30 * CELL}px);animation-timing-function:ease-in-out}50%{transform:translate(${24 * CELL}px,${30 * CELL}px);animation-timing-function:ease-in-out}100%{transform:translate(${10 * CELL}px,${30 * CELL}px)}}
.honuX{transform:translateX(${91 * CELL}px)}.honuY{transform:translateY(${32 * CELL}px)}.coralY{transform:translate(${10 * CELL}px,${30 * CELL}px)}.pose:first-child{opacity:1}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  const defs = `
<linearGradient id="water" x1="0" y1="0" x2="1" y2="0.03"><stop offset="0" stop-color="#5cc7d6"/><stop offset="0.05" stop-color="#6bcedb"/><stop offset="0.1" stop-color="#79d4e0"/><stop offset="0.16" stop-color="#86d9e4"/><stop offset="0.24" stop-color="#93dde8"/><stop offset="0.36" stop-color="#9fe0ea"/><stop offset="0.54" stop-color="#84d6e5"/><stop offset="0.7" stop-color="#4fbbdc"/><stop offset="0.86" stop-color="#22a0cf"/><stop offset="1" stop-color="#1493c9"/></linearGradient>
<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#d2f8fa" stop-opacity="0.28"/><stop offset="0.35" stop-color="#d2f8fa" stop-opacity="0.18"/><stop offset="0.7" stop-color="#d2f8fa" stop-opacity="0.06"/><stop offset="1" stop-color="#d2f8fa" stop-opacity="0"/></radialGradient>
<radialGradient id="sun" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ffe9a0" stop-opacity="0.8"/><stop offset="0.2" stop-color="#ffe9a0" stop-opacity="0.58"/><stop offset="0.4" stop-color="#ffe9a0" stop-opacity="0.36"/><stop offset="0.6" stop-color="#ffe9a0" stop-opacity="0.18"/><stop offset="0.8" stop-color="#ffe9a0" stop-opacity="0.06"/><stop offset="1" stop-color="#ffe9a0" stop-opacity="0"/></radialGradient>
<radialGradient id="soft" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#fff"/><stop offset="0.3" stop-color="#fff" stop-opacity="0.7"/><stop offset="0.65" stop-color="#fff" stop-opacity="0.22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="${CELL}" height="${CELL}" patternUnits="userSpaceOnUse"><rect x="5" y="6.5" width="5" height="2" rx="1" fill="#eaffff" fill-opacity="0.75"/></pattern>
<pattern id="grid" width="${CELL}" height="${CELL}" patternUnits="userSpaceOnUse"><path d="M0 0.5h${CELL}M0.5 0v${CELL}" stroke="#dff7ff" stroke-opacity="0.08" fill="none"/></pattern>
<linearGradient id="east" x1="0" y1="0" x2="1" y2="0"><stop offset="0.64" stop-color="#fff" stop-opacity="0"/><stop offset="0.82" stop-color="#fff" stop-opacity="1"/></linearGradient>
<mask id="eastward" maskUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1000"><rect width="1600" height="1000" fill="url(#east)"/></mask>
${['m1', 'm2', 'm3', 'm4'].map(id => `<mask id="${id}" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#soft)"/></mask>`).join('')}`

  const south: Heading = [Math.sin(0.26), Math.cos(0.26)]

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
<rect width="1600" height="1000" fill="url(#water)"/>
<ellipse cx="576" cy="400" rx="448" ry="420" fill="url(#glow)"/>
${patches()}
<ellipse cx="1600" cy="0" rx="560" ry="460" fill="url(#sun)"/>
<rect width="1600" height="1000" fill="url(#grid)" mask="url(#eastward)"/>
<g class="field">${glints('m1', 1400, 330, 170, 110, 9, 0)}${glints('m2', 180, 150, 170, 80, 11, 3)}${glints('m3', 1330, 800, 200, 130, 10, 5)}${glints('m4', 230, 800, 200, 90, 13, 2)}</g>
${mosaic(islandCells())}${mosaic(shoalCells())}${twinkle(islandCells())}${twinkle(shoalCells())}
<g class="coralY">${under(coralCells(), 0.2, 2)}${mosaic(coralCells())}</g>
${turtle('honuX', 'honuY', south, 1.1, 22)}
${sparkle(1470, 840, 2.4, 2.2, 8)}${sparkle(240, 470, 2, 3.6, 9)}${sparkle(1560, 520, 2, 6.1, 11)}${sparkle(1290, 300, 1.8, 0.7, 7)}${sparkle(1140, 900, 2, 4.9, 10)}${sparkle(110, 150, 1.8, 7.5, 9)}${sparkle(330, 880, 2.2, 1.9, 8)}${sparkle(1330, 960, 1.8, 5.5, 11)}${sparkle(60, 640, 2, 8.3, 7)}
</svg>`
}

