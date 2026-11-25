// Departure Board: one big LED dot-matrix panel. A lattice of unlit dots runs edge to edge, and a slow diagonal swell of
// brightness passes through it on the left. Down the right-hand side, a tall board of an invented script is lit amber and
// runs off the frame's right and bottom edges. Every sixteen seconds one row re-letters, letter by letter from the left;
// a freshly lettered row glows a little brighter and settles over twenty seconds. Nothing else moves.
//
// Cheap to paint on purpose (it must hold 55 frames a second with no GPU): no mask and no group opacity anywhere.
// Fades that a mask used to make are painted over in the ground colour; rows carry their level in `fill-opacity`;
// the slow fades (the swell, a fresh row settling) move in small steps about once a second, so most frames paint nothing.

const PITCH = 10
const ROW_PITCH = 10
const FIRST_ROW = 12
const ROWS = 10
const FIRST_SHOWN_ROW = 2
const LAST_SHOWN_ROW = 8
const GROUND = '#1f1710'
const LETTERS_PER_ROW = 7
const LETTER_ADVANCE = 7
const BOARD_COLUMN = 118
const FLIP_SECONDS = 320
const SWELL_SECONDS = 120
const SWELL_STRIPES = 16
const ALPHABET_SIZE = 28
const AMBER = 'url(#dotAmber)'
const TEAL = 'url(#dotTeal)'

/** One dot of the lattice, by column and row. */
type Cell = { column: number; row: number }

/** A negative delay starts an animation that many seconds into its cycle. */
function delayOf(base: number, period: number): string {
  const phase = ((base % period) + period) % period
  return `-${phase.toFixed(2)}s`
}

/** A small deterministic hash: the same build every time, with no random call and no clock. */
function hashOf(seed: number): number {
  let value = (seed * 2654435761) % 4294967296
  value = (value ^ (value >>> 13)) >>> 0
  value = (value * 1274126177) % 4294967296
  return ((value ^ (value >>> 16)) >>> 0) / 4294967296
}

/** One run of neighbouring cells in a row: a pitch-high rectangle that a dot pattern fills. */
function runPath(start: number, end: number, row: number): string {
  const width = (end - start + 1) * PITCH
  return `M${start * PITCH} ${row * PITCH}h${width}v${PITCH}h-${width}z`
}

/** Cells joined into one path of row runs. */
function cellPath(cells: Cell[]): string {
  const rows = new Map<number, number[]>()
  for (const cell of cells) {
    const columns = rows.get(cell.row) ?? []
    columns.push(cell.column)
    rows.set(cell.row, columns)
  }
  let path = ''
  for (const [row, columns] of rows) {
    const sorted = [...columns].sort((a, b) => a - b)
    let open = false
    let start = 0
    let previous = 0
    for (const column of sorted) {
      if (open && column === previous + 1) {
        previous = column
        continue
      }
      if (open) path += runPath(start, previous, row)
      open = true
      start = column
      previous = column
    }
    if (open) path += runPath(start, previous, row)
  }
  return path
}

/**
 * The invented alphabet, from one kit of BROKEN strokes: a stem with a gap in it, one three-dot diagonal leaving
 * the stem, one two-dot tick that floats free on the other side, and one loose dot. One grammar, so it looks like a script.
 * No bar ever joins the stem, so it has no bracket, no E, F, H, 7 or T in it, whatever the alphabet; the gap keeps a stem
 * from looking like a 1 or an I.
 */
function alphabet(): Cell[][] {
  const letters: Cell[][] = []
  const seen = new Set<string>()
  let seed = 1
  while (letters.length < ALPHABET_SIZE) {
    seed += 1
    const stem = 1 + Math.floor(hashOf(seed * 3) * 3)
    const gapAt = 1 + Math.floor(hashOf(seed * 5) * 4)
    const side = hashOf(seed * 7) > 0.5 ? 1 : -1
    if ((stem === 1 && side < 0) || (stem === 3 && side > 0)) continue
    const diagonalRow = hashOf(seed * 11) > 0.5 ? 0 : 6
    const tickRow = 2 + Math.floor(hashOf(seed * 13) * 3)
    const cells: Cell[] = []
    for (let row = 0; row < 7; row += 1) {
      if (row !== gapAt + 1) cells.push({ column: stem, row })
    }
    for (let step = 1; step <= 3; step += 1) {
      const column = stem + side * step
      const row = diagonalRow === 0 ? step - 1 : 7 - step
      if (column >= 0 && column <= 4) cells.push({ column, row })
    }
    const tickColumn = side > 0 ? stem - 2 : stem + 2
    if (tickColumn >= 0 && tickColumn + 1 <= 4 && tickColumn - 1 !== stem && tickColumn + 2 !== stem) {
      cells.push({ column: tickColumn, row: tickRow }, { column: tickColumn + 1, row: tickRow })
    } else {
      cells.push({ column: side > 0 ? 0 : 4, row: tickRow })
    }
    cells.push({ column: side > 0 ? 4 : 0, row: diagonalRow === 0 ? 6 : 0 })
    const key = cells.map(cell => `${cell.column},${cell.row}`).sort().join(' ')
    if (seen.has(key)) continue
    seen.add(key)
    letters.push(cells)
  }
  return letters
}

/** One letter cell: what it shows and what it will show; the two cross-fade when the row's turn comes. */
function letter(x: number, y: number, seed: number, flipAt: number): string {
  const first = Math.floor(hashOf(seed) * ALPHABET_SIZE)
  const second = (first + 1 + Math.floor(hashOf(seed + 101) * (ALPHABET_SIZE - 1))) % ALPHABET_SIZE
  const place = `x="${x}" y="${y}" style="animation-delay:${delayOf(FLIP_SECONDS / 2 - flipAt, FLIP_SECONDS)}"`
  return `<use href="#letter${first}" class="was" ${place}/><use href="#letter${second}" class="next" ${place}/>`
}

/** How bright a row rests: its own level, less at the top (just below the cards) and at the bottom (where a wide window crops). */
function restingLevel(index: number): number {
  const edge = index === FIRST_SHOWN_ROW ? 0.6 : index === LAST_SHOWN_ROW ? 0.55 : 1
  return (0.55 + 0.45 * hashOf(700 + index)) * edge
}

/** A fresh row's glow and its settling: keyframes of `fill-opacity` that already hold the row's own level. */
function freshKeyframes(index: number, fade: number, settle: number): string {
  const rest = (restingLevel(index) * 0.74).toFixed(3)
  const peak = (restingLevel(index) * 0.98).toFixed(3)
  const gentle = 'animation-timing-function:steps(24)'
  return `@keyframes fresh${index}{0%{fill-opacity:${peak};${gentle}}${settle.toFixed(2)}%{fill-opacity:${rest}}${(50 - 2 * fade).toFixed(2)}%{fill-opacity:${rest}}50%{fill-opacity:${peak};${gentle}}${(50 + settle).toFixed(2)}%{fill-opacity:${rest}}${(100 - 2 * fade).toFixed(2)}%{fill-opacity:${rest}}100%{fill-opacity:${peak}}}`
}

/**
 * The board: rows down the right side, from just below the cards to the bottom edge. Its last letters lie beyond the
 * frame, so the crop cuts it. Rows keep the numbering of the full ten-row board, so their letters and turns stay put.
 */
function board(): string {
  const x = BOARD_COLUMN * PITCH
  let out = ''
  let rules = ''
  for (let index = FIRST_SHOWN_ROW; index <= LAST_SHOWN_ROW; index += 1) {
    const row = FIRST_ROW + index * ROW_PITCH
    const order = (index * 3 + 1) % ROWS
    const flipAt = 13 + order * (FLIP_SECONDS / 2 / ROWS)
    const freshDelay = delayOf(FLIP_SECONDS / 2 - flipAt - 1, FLIP_SECONDS)
    let letters = ''
    for (let position = 0; position < LETTERS_PER_ROW; position += 1) {
      const gap = position >= 2 ? 1 : 0
      if (hashOf(900 + index * 17 + position) < 0.24) continue
      letters += letter(x + (position * LETTER_ADVANCE + gap) * PITCH, row * PITCH, 500 + index * 13 + position, flipAt + position * 0.4)
    }
    const lampCells = [2, 3, 4].map(lampRow => ({ column: BOARD_COLUMN - 2, row: row + lampRow }))
    const rest = (restingLevel(index) * 0.74).toFixed(3)
    out += `<g style="fill-opacity:${rest};animation:fresh${index} ${FLIP_SECONDS}s linear ${freshDelay} infinite">${letters}</g><path class="lamp" style="animation-delay:${freshDelay}" d="${cellPath(lampCells)}" fill="${TEAL}"/>`
    if (index > FIRST_SHOWN_ROW) rules += `M${x - 30} ${(row - 1) * PITCH}h520v${PITCH}h-520z`
  }
  return `<path d="${rules}" fill="url(#rule)"/><g fill="${AMBER}">${out}</g>`
}

/** A horizontal slice of a slanted stripe, kept inside the left band: the stripe leans half a unit left per unit down. */
function stripeSlice(left: number, width: number, from: number, to: number): string {
  let path = ''
  for (let y = 0; y < 1000; y += 50) {
    const start = Math.max(from, left - y / 2)
    const end = Math.min(to, left + width - y / 2)
    if (end > start) path += `M${start.toFixed(0)} ${y}H${end.toFixed(0)}v50H${start.toFixed(0)}z`
  }
  return path
}

/**
 * The swell: diagonal stripes of brighter lattice dots, each fading up and down in turn, so a soft band of brightness
 * drifts down the left band, under the sidebar's glass. It stays out from behind the lit letters. The stripes never
 * move, so their dots stay on the lattice; each is cut in three along its length, fainter toward the reading column,
 * which is the soft edge a mask used to give.
 */
function swell(): string {
  let out = ''
  const width = 150
  const parts = [{ from: 0, to: 290, level: 1 }, { from: 290, to: 360, level: 0.6 }, { from: 360, to: 420, level: 0.25 }]
  for (let stripe = 0; stripe < SWELL_STRIPES; stripe += 1) {
    const left = stripe * width
    const delay = delayOf(30 - stripe * SWELL_SECONDS / SWELL_STRIPES, SWELL_SECONDS)
    for (const part of parts) {
      const path = stripeSlice(left, width, part.from, part.to)
      if (path !== '') out += `<path class="swell" style="--peak:${part.level};animation-delay:${delay}" d="${path}"/>`
    }
  }
  return `<g fill="url(#swellDot)">${out}</g>`
}

/** A lit dot: a halo that stays inside the dot's own cell (so nothing can band), a core and a glint. */
function dotPattern(id: string, halo: string, core: string, glint: string): string {
  return `<radialGradient id="${id}Halo"><stop offset="0" stop-color="${halo}" stop-opacity="0.5"/><stop offset="0.5" stop-color="${halo}" stop-opacity="0.18"/><stop offset="1" stop-color="${halo}" stop-opacity="0"/></radialGradient>`
    + `<pattern id="${id}" width="${PITCH}" height="${PITCH}" patternUnits="userSpaceOnUse"><rect width="${PITCH}" height="${PITCH}" fill="url(#${id}Halo)"/><circle cx="5" cy="5" r="2.5" fill="${core}"/><circle cx="5" cy="5" r="1.05" fill="${glint}"/></pattern>`
}

function unlitPattern(id: string, radius: number, colour: string): string {
  return `<pattern id="${id}" width="${PITCH}" height="${PITCH}" patternUnits="userSpaceOnUse"><circle cx="5" cy="5" r="${radius}" fill="${colour}"/></pattern>`
}

function smooth(value: number): number {
  const t = Math.max(0, Math.min(1, value))
  return t * t * (3 - 2 * t)
}

/** How much of the lattice the reading column keeps: full in the side bands, a low even level across the middle, never zero. */
function latticeLevel(x: number): number {
  return 0.55 + 0.45 * smooth((0.34 - Math.min(x, 1 - x)) / 0.2)
}

/** The lattice's fade toward the middle, painted OVER it in the ground colour: what a mask did, at a fraction of the cost. */
function middleVeil(): string {
  let stops = ''
  for (let step = 0; step <= 24; step += 1) {
    stops += `<stop offset="${(step / 24).toFixed(3)}" stop-color="${GROUND}" stop-opacity="${(1 - latticeLevel(step / 24)).toFixed(3)}"/>`
  }
  return `<linearGradient id="middleVeil" x1="0" y1="0" x2="1" y2="0">${stops}</linearGradient>`
}

export function departureBoardSvg(): string {
  const letters = alphabet()
  const fade = (1.2 / FLIP_SECONDS * 100)
  const settle = (20 / FLIP_SECONDS * 100)
  const rowIndexes: number[] = []
  for (let index = FIRST_SHOWN_ROW; index <= LAST_SHOWN_ROW; index += 1) rowIndexes.push(index)

  const style = `
.was{animation:was ${FLIP_SECONDS}s linear infinite}
.next{opacity:0;animation:next ${FLIP_SECONDS}s linear infinite}
@keyframes was{0%{opacity:1}${(50 - fade).toFixed(2)}%{opacity:1}50%{opacity:0}${(100 - fade).toFixed(2)}%{opacity:0}100%{opacity:1}}
@keyframes next{0%{opacity:0}${(50 - fade).toFixed(2)}%{opacity:0}50%{opacity:1}${(100 - fade).toFixed(2)}%{opacity:1}100%{opacity:0}}
${rowIndexes.map(index => freshKeyframes(index, fade, settle)).join('\n')}
@keyframes lamp{0%{fill-opacity:.9;animation-timing-function:steps(24)}${settle.toFixed(2)}%{fill-opacity:0}${(50 - 2 * fade).toFixed(2)}%{fill-opacity:0}50%{fill-opacity:.9;animation-timing-function:steps(24)}${(50 + settle).toFixed(2)}%{fill-opacity:0}${(100 - 2 * fade).toFixed(2)}%{fill-opacity:0}100%{fill-opacity:.9}}
.lamp{fill-opacity:0;animation:lamp ${FLIP_SECONDS}s linear infinite}
.swell{fill-opacity:0;animation:swell ${SWELL_SECONDS}s steps(20) infinite}
@keyframes swell{0%{fill-opacity:0}16%{fill-opacity:var(--peak)}32%{fill-opacity:0}100%{fill-opacity:0}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  const defs = `
${unlitPattern('unlit', 1.5, '#3a2b1d')}
${unlitPattern('rule', 1.6, '#523c1e')}
${unlitPattern('swellDot', 1.9, '#7a5526')}
${dotPattern('dotAmber', '#ee8f1c', '#f2a53a', '#ffe0aa')}
${dotPattern('dotTeal', '#2fb89c', '#5fd0b8', '#d8fff5')}
${middleVeil()}
${letters.map((cells, index) => `<path id="letter${index}" d="${cellPath(cells)}"/>`).join('')}`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
<rect width="1600" height="1000" fill="${GROUND}"/>
<rect width="1600" height="1000" fill="url(#unlit)"/>
${swell()}
<rect width="1600" height="1000" fill="url(#middleVeil)"/>
${board()}
</svg>`
}
