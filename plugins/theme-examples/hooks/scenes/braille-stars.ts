// Braille Stars: a night sky rendered the way a terminal renders a picture in braille.
// The frame is a grid of cells of 2 by 4 dots; each cell gets a brightness, and that many of its dots are raised.
// Pure string building: no DOM, nothing brought in from outside this file.

type Dot = { x: number; y: number }
type PaintName = 'dust' | 'haze' | 'cloud' | 'star' | 'warm' | 'orchid' | 'amber' | 'figure' | 'ridgeCrest'
type Paint = { colour: string; opacity: number; width: number }
type Layer = Map<PaintName, Dot[]>
type SpineSample = { x: number; y: number; t: number; tangentX: number; tangentY: number }
type BandReading = { brightness: number; along: number; across: number; underCards: number }
type ShimmerGroup = { first: Layer; second: Layer }
type TwinkleGroup = { small: Layer; medium: Layer; large: Layer }
type Figure = { stars: readonly (readonly [number, number, number])[]; joins: readonly (readonly [number, number])[] }
type StarCentre = { x: number; y: number; reach: number }

const DOT_PITCH = 7
const CELL_WIDTH = 19
const CELL_HEIGHT = 33
const CELL_INSET = 3
// The sky sways by three degrees either way about the pole, so it is drawn a little past every edge.
const SKY_LEFT = -110
const SKY_RIGHT = 1730
const SKY_TOP = -100
const SKY_BOTTOM = 1000
const POLE_X = -120
const POLE_Y = -140
const SHIMMER_GROUPS = 8
const SHIMMER_SECONDS = 40

/** A repeatable number in [0, 1) from two grid coordinates and a salt: every build draws the same sky. */
function hashUnit(x: number, y: number, salt: number): number {
  let h = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(salt | 0, 2147483647)) | 0
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b)
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35)
  h = h ^ (h >>> 16)
  return (h >>> 0) / 4294967296
}

function smoothStep(low: number, high: number, value: number): number {
  const t = Math.min(1, Math.max(0, (value - low) / (high - low)))
  return t * t * (3 - 2 * t)
}

/** Smooth noise in [0, 1): clumps the Milky Way so it does not read like an even spray. */
function valueNoise(x: number, y: number, scale: number, salt: number): number {
  const gx = Math.floor(x / scale)
  const gy = Math.floor(y / scale)
  const fx = smoothStep(0, 1, x / scale - gx)
  const fy = smoothStep(0, 1, y / scale - gy)
  const top = hashUnit(gx, gy, salt) * (1 - fx) + hashUnit(gx + 1, gy, salt) * fx
  const bottom = hashUnit(gx, gy + 1, salt) * (1 - fx) + hashUnit(gx + 1, gy + 1, salt) * fx
  return top * (1 - fy) + bottom * fy
}

function dotX(cellColumn: number, dotColumn: number): number {
  return cellColumn * CELL_WIDTH + CELL_INSET + dotColumn * DOT_PITCH
}

function dotY(cellRow: number, dotRow: number): number {
  return cellRow * CELL_HEIGHT + CELL_INSET + dotRow * DOT_PITCH
}

// The order in which a cell's eight dots are raised while it brightens (dot = row * 2 + column). Spread out, so a half-lit cell looks like a letter, not a bar.
const RAISE_ORDER: readonly number[] = [2, 5, 0, 7, 3, 4, 1, 6]

/** The dots of a cell at a brightness of 0 to 8, mirrored by the cell's own hash so neighbours are not copies of each other. A second variant gives the same cell another letter. */
function raisedDots(cellColumn: number, cellRow: number, count: number, variant: number): Dot[] {
  const mirror = hashUnit(cellColumn, cellRow, 40 + variant * 2) < 0.5
  const flip = hashUnit(cellColumn, cellRow, 41 + variant * 2) < 0.5
  const dots: Dot[] = []
  for (let rank = 0; rank < count; rank += 1) {
    const dot = RAISE_ORDER[rank] ?? 0
    const dotColumn = mirror ? 1 - (dot % 2) : dot % 2
    const dotRow = flip ? 3 - (dot >> 1) : dot >> 1
    dots.push({ x: dotX(cellColumn, dotColumn), y: dotY(cellRow, dotRow) })
  }
  return dots
}

/** Dots are collected by paint, then each paint is written out in one path: a zero-length stroke with round caps is a dot. */
function addDot(layer: Layer, paint: PaintName, x: number, y: number): void {
  const dots = layer.get(paint)
  if (dots === undefined) layer.set(paint, [{ x, y }])
  else dots.push({ x, y })
}

function sameDot(dots: readonly Dot[], dot: Dot): boolean {
  return dots.some(other => other.x === dot.x && other.y === dot.y)
}

// Flat tones only, each blended into the sky once when the scene is built: the browser never has to composite a see-through group. Sky: four blues, two warm whites and an orchid. Land: one dark blue.
const PAINTS: Record<PaintName, Paint> = {
  dust: { colour: '#4c62b4', opacity: 0.7, width: 2.8 },
  haze: { colour: '#8ea6ff', opacity: 0.8, width: 3.5 },
  cloud: { colour: '#b4c2ff', opacity: 0.95, width: 4.1 },
  star: { colour: '#dde4ff', opacity: 0.95, width: 4.7 },
  warm: { colour: '#ffdcae', opacity: 0.95, width: 4.6 },
  orchid: { colour: '#c890d6', opacity: 0.85, width: 4 },
  amber: { colour: '#e9d3ad', opacity: 1, width: 4.4 },
  figure: { colour: '#fff1d0', opacity: 0.88, width: 4.4 },
  ridgeCrest: { colour: '#4a5ca6', opacity: 0.7, width: 4 },
}

const SKY_BASE = '#0d1536'
const LAND_BASE = '#070b1f'

/** A tone laid over the sky at a given strength, worked out once: an opaque colour needs no blending when the frame is painted. */
function blend(colour: string, opacity: number, base: string): string {
  let out = '#'
  for (let channel = 0; channel < 3; channel += 1) {
    const top = parseInt(colour.slice(1 + channel * 2, 3 + channel * 2), 16)
    const under = parseInt(base.slice(1 + channel * 2, 3 + channel * 2), 16)
    out += Math.round(top * opacity + under * (1 - opacity)).toString(16).padStart(2, '0')
  }
  return out
}

/** Row by row, with relative moves along a row: a third fewer characters than absolute moves. */
function writeLayer(layer: Layer): string {
  let out = ''
  for (const [paint, dots] of layer) {
    const look = PAINTS[paint]
    dots.sort((first, second) => first.y - second.y || first.x - second.x)
    let d = ''
    let last: Dot | null = null
    for (const dot of dots) {
      d += last !== null && last.y === dot.y ? `m${dot.x - last.x} 0h0` : `M${dot.x} ${dot.y}h0`
      last = dot
    }
    out += `<path d="${d}" stroke="${blend(look.colour, look.opacity, paint === 'ridgeCrest' ? LAND_BASE : SKY_BASE)}" stroke-width="${look.width}"/>`
  }
  return out
}

/** The Milky Way's spine: a diagonal from the top right corner down to the hills, about thirty degrees off upright, its core low. */
function milkyWaySpine(): SpineSample[] {
  const points: { x: number; y: number; t: number }[] = []
  for (let step = 0; step <= 60; step += 1) {
    const t = step / 60
    const x = (1 - t) * (1 - t) * 1830 + 2 * (1 - t) * t * 1430 + t * t * 1010
    const y = (1 - t) * (1 - t) * -60 + 2 * (1 - t) * t * 470 + t * t * 1040
    points.push({ x, y, t })
  }
  return points.map((point, index) => {
    const before = points[Math.max(0, index - 1)] ?? point
    const after = points[Math.min(points.length - 1, index + 1)] ?? point
    const length = Math.hypot(after.x - before.x, after.y - before.y)
    return { x: point.x, y: point.y, t: point.t, tangentX: (after.x - before.x) / length, tangentY: (after.y - before.y) / length }
  })
}

/** The Milky Way's brightness (0 to 1) at a point, how far along and across the band the point sits, and whether it lies under the cards. */
function milkyWayAt(x: number, y: number, spine: readonly SpineSample[]): BandReading {
  let nearest: SpineSample | undefined = undefined
  let best = Infinity
  for (const sample of spine) {
    const distance = (sample.x - x) * (sample.x - x) + (sample.y - y) * (sample.y - y)
    if (distance < best) {
      best = distance
      nearest = sample
    }
  }
  if (nearest === undefined) return { brightness: 0, along: 0, across: 0, underCards: 1 }
  const across = (x - nearest.x) * nearest.tangentY - (y - nearest.y) * nearest.tangentX
  const halfWidth = (66 + 80 * smoothStep(0.15, 0.85, nearest.t)) * (0.7 + 0.6 * valueNoise(nearest.t * 900, 0, 130, 19))
  const band = Math.exp(-(across * across) / (halfWidth * halfWidth))
  const along = (0.62 + 0.38 * smoothStep(0.1, 0.7, nearest.t)) * (1 - smoothStep(0.86, 0.98, nearest.t))
  const laneCentre = 4 + 38 * Math.sin(nearest.t * 8) + 16 * Math.sin(nearest.t * 19 + 1)
  const laneWidth = 22 + 12 * nearest.t
  const lane = 1 - 0.93 * Math.exp(-((across - laneCentre) * (across - laneCentre)) / (laneWidth * laneWidth))
  const clump = 0.3 + 2 * valueNoise(x, y, 105, 11) * valueNoise(x, y, 41, 12)
  // Under the cards (top right of the window) the band is held to its dimmest tones so it does not crawl through their text.
  const underCards = 1 - smoothStep(1150, 1230, x) * (1 - smoothStep(230, 310, y))
  const brightness = Math.min(1, (0.3 * Math.pow(band, 0.8) + 0.86 * Math.pow(band, 1.2) * clump) * along * lane) * (0.25 + 0.75 * underCards)
  return { brightness, along: nearest.t, across, underCards }
}

/** 1 at the edges, low over the conversation column: the middle stays the sparsest and darkest part. */
function calmFactor(x: number, y: number): number {
  const insideX = smoothStep(330, 470, x) * (1 - smoothStep(1070, 1260, x))
  const insideY = smoothStep(30, 110, y) * (1 - smoothStep(860, 940, y))
  return 1 - 0.8 * insideX * insideY
}

const TONES: readonly PaintName[] = ['dust', 'haze', 'cloud', 'star']

/** The paint of one dot of a band cell. Within a cell the first dots raised are the brightest and the last the dimmest: soft-edged letters, not stencils. */
function bandPaint(tone: number, warm: boolean, orchid: boolean, rank: number, count: number): PaintName {
  if (warm && rank < 3) return 'warm'
  if (orchid && rank < 2) return 'orchid'
  const step = (rank === 0 && count >= 3 ? 1 : 0) - (rank >= count - 1 && count >= 2 ? 1 : 0) - (rank >= count - 2 && count >= 4 ? 1 : 0)
  return TONES[Math.min(3, Math.max(0, tone + step))] ?? 'dust'
}

/** The Milky Way, cell by cell. Every cell has two letters (the same brightness give or take a dot, mirrored differently); groups of cells trade one for the other in turn, so the band's texture slowly rewrites itself from one end to the other. */
function milkyWayCells(spine: readonly SpineSample[]): string {
  const steady: Layer = new Map()
  const groups: ShimmerGroup[] = []
  for (let group = 0; group < SHIMMER_GROUPS; group += 1) groups.push({ first: new Map(), second: new Map() })
  const pulses: Layer[] = [new Map(), new Map(), new Map(), new Map()]
  for (let cellRow = Math.floor(SKY_TOP / CELL_HEIGHT); cellRow * CELL_HEIGHT < SKY_BOTTOM; cellRow += 1) {
    for (let cellColumn = Math.floor(900 / CELL_WIDTH); cellColumn * CELL_WIDTH < SKY_RIGHT; cellColumn += 1) {
      const centreX = cellColumn * CELL_WIDTH + CELL_WIDTH / 2
      const centreY = cellRow * CELL_HEIGHT + CELL_HEIGHT / 2
      const here = milkyWayAt(centreX, centreY, spine)
      // The band is feathered toward the column: full strength at the edge of the window, a ghost of itself inside the column.
      const brightness = here.brightness * Math.pow(calmFactor(centreX, centreY), 1.6)
      const firstCount = Math.min(6, Math.floor(brightness * 7 + hashUnit(cellColumn, cellRow, 1) * 1.3 - 0.25))
      if (firstCount <= 0) continue
      const secondCount = Math.min(7, Math.max(1, firstCount + (hashUnit(cellColumn, cellRow, 2) < 0.5 ? -1 : 1)))
      // The core is warm, the middle has a little orchid, the rest is blue. Coloured cells sit on a checkerboard so two never share an edge and spell something.
      const apart = (cellColumn + cellRow) % 2 === 0
      const warm = apart && brightness > 0.5 && hashUnit(cellColumn, cellRow, 4) < 0.5
      const orchid = !warm && apart && brightness > 0.22 && brightness < 0.6 && hashUnit(cellColumn, cellRow, 21) < 0.2
      const tone = brightness < 0.25 || here.underCards < 0.5 ? 0 : brightness < 0.45 ? 1 : brightness < 0.72 ? 2 : 3
      // About one band cell in nine is a variable star: the whole cell fades down and back on its own slow clock.
      if (brightness > 0.22 && hashUnit(cellColumn, cellRow, 19) < 0.11) {
        const pulse = pulses[Math.min(3, Math.floor(smoothStep(0.12, 0.88, here.along) * 4))]
        if (pulse === undefined) continue
        const pulseDots = raisedDots(cellColumn, cellRow, Math.min(6, firstCount + 1), 0)
        for (const [rank, dot] of pulseDots.entries()) addDot(pulse, rank < 2 ? (warm ? 'warm' : 'star') : 'cloud', dot.x, dot.y)
        continue
      }
      // Cells that change together lie together (one stretch of the band per group), so one change repaints one stretch, not the whole frame.
      const group = groups[Math.floor(here.along * 0.999 * SHIMMER_GROUPS)]
      if (group === undefined) continue
      const first = raisedDots(cellColumn, cellRow, firstCount, 0)
      const second = raisedDots(cellColumn, cellRow, secondCount, 1)
      for (const [rank, dot] of first.entries()) {
        addDot(sameDot(second, dot) ? steady : group.first, bandPaint(tone, warm, orchid, rank, firstCount), dot.x, dot.y)
      }
      for (const [rank, dot] of second.entries()) {
        if (!sameDot(first, dot)) addDot(group.second, bandPaint(tone, warm, orchid, rank, secondCount), dot.x, dot.y)
      }
    }
  }
  let out = writeLayer(steady)
  for (const [index, group] of groups.entries()) {
    const delay = ((index * SHIMMER_SECONDS) / SHIMMER_GROUPS).toFixed(1)
    out += `<g class="first" style="animation-delay:-${delay}s">${writeLayer(group.first)}</g><g class="second" style="animation-delay:-${delay}s">${writeLayer(group.second)}</g>`
  }
  for (const [index, pulse] of pulses.entries()) {
    out += `<g class="pulse p${index}">${writeLayer(pulse)}</g>`
  }
  return out
}

/** Which of six patches of sky a point lies in. Stars that twinkle together share a patch, so one change repaints one patch, not the whole frame. */
function skyRegion(x: number, y: number): number {
  if (x < 450) return y < 330 ? 0 : y < 640 ? 1 : 2
  if (x > 1150) return y < 480 ? 3 : 4
  return y < 500 ? 5 : x < 800 ? 2 : 4
}

/** Sparse field stars, one braille cell each. Some step between three dot patterns: that is the twinkle. */
function fieldStars(spine: readonly SpineSample[]): string {
  const steady: Layer = new Map()
  const twinkleGroups: TwinkleGroup[] = []
  for (let group = 0; group < 6; group += 1) twinkleGroups.push({ small: new Map(), medium: new Map(), large: new Map() })
  for (let cellRow = Math.floor(SKY_TOP / CELL_HEIGHT); cellRow * CELL_HEIGHT < SKY_BOTTOM; cellRow += 1) {
    for (let cellColumn = Math.floor(SKY_LEFT / CELL_WIDTH); cellColumn * CELL_WIDTH < SKY_RIGHT; cellColumn += 1) {
      const centreX = cellColumn * CELL_WIDTH + CELL_WIDTH / 2
      const centreY = cellRow * CELL_HEIGHT + CELL_HEIGHT / 2
      const chance = 0.085 * calmFactor(centreX, centreY) * (0.5 + valueNoise(centreX, centreY, 240, 21))
      if (hashUnit(cellColumn, cellRow, 5) >= chance) continue
      if (milkyWayAt(centreX, centreY, spine).brightness > 0.2) continue
      const dotColumn = hashUnit(cellColumn, cellRow, 6) < 0.5 ? 0 : 1
      const dotRow = 1 + Math.floor(hashUnit(cellColumn, cellRow, 7) * 2)
      const x = dotX(cellColumn, dotColumn)
      const y = dotY(cellRow, dotRow)
      const otherX = dotX(cellColumn, 1 - dotColumn)
      const rank = hashUnit(cellColumn, cellRow, 8)
      const calm = calmFactor(centreX, centreY) < 0.6
      const bright: PaintName = rank < 0.86 ? 'star' : rank < 0.96 ? 'warm' : 'amber'
      if (calm || hashUnit(cellColumn, cellRow, 9) >= 0.36) {
        addDot(steady, calm ? 'dust' : rank < 0.5 ? 'haze' : rank < 0.85 ? 'cloud' : bright, x, y)
        if (!calm && rank > 0.8) addDot(steady, 'haze', otherX, y)
        continue
      }
      const group = twinkleGroups[skyRegion(centreX, centreY)]
      if (group === undefined) continue
      addDot(group.small, 'cloud', x, y)
      addDot(group.medium, bright, x, y)
      addDot(group.medium, 'haze', otherX, y)
      addDot(group.large, bright, x, y)
      addDot(group.large, 'cloud', otherX, y)
      addDot(group.large, 'cloud', x, y - DOT_PITCH)
      addDot(group.large, 'haze', x, y + DOT_PITCH)
    }
  }
  let out = writeLayer(steady)
  for (const [index, group] of twinkleGroups.entries()) {
    out += `<g class="tw t${index}"><g class="small">${writeLayer(group.small)}</g><g class="medium">${writeLayer(group.medium)}</g><g class="large">${writeLayer(group.large)}</g></g>`
  }
  return out
}

// One figure. Its joins are dotted at the grid's own pitch, so even the lines are drawn in dots. Each star is a cell; a brighter star raises more dots (1, 2, 4 or 6). Its stars wink, a few at a time.
const FIGURES: readonly Figure[] = [
  // The Scorpion's head and body, beside the band; its tail is left to the cloud.
  {
    stars: [[1192, 276, 2], [1213, 305, 3], [1198, 335, 2], [1246, 324, 2], [1278, 348, 4], [1304, 382, 2], [1312, 417, 3], [1336, 439, 2]],
    joins: [[0, 1], [1, 2], [1, 3], [3, 4], [4, 5], [5, 6], [6, 7]],
  },
]

function figures(): string {
  const winks: Layer[] = [new Map(), new Map(), new Map(), new Map()]
  let lines = ''
  for (const figure of FIGURES) {
    const centres: StarCentre[] = []
    for (const [index, star] of figure.stars.entries()) {
      const cellColumn = Math.floor(star[0] / CELL_WIDTH)
      const cellRow = Math.floor(star[1] / CELL_HEIGHT)
      const rows = star[2] >= 4 ? 3 : star[2] >= 3 ? 2 : 1
      const columns = star[2] >= 2 ? 2 : 1
      const wink = winks[index % 4]
      if (wink === undefined) continue
      for (let dotRow = 0; dotRow < rows; dotRow += 1) {
        for (let dotColumn = 0; dotColumn < columns; dotColumn += 1) addDot(wink, 'figure', dotX(cellColumn, dotColumn), dotY(cellRow, 1 + dotRow))
      }
      centres.push({ x: dotX(cellColumn, 0) + ((columns - 1) * DOT_PITCH) / 2, y: dotY(cellRow, 1) + ((rows - 1) * DOT_PITCH) / 2, reach: 8 + rows * 4 })
    }
    for (const join of figure.joins) {
      const from = centres[join[0]]
      const to = centres[join[1]]
      if (from === undefined || to === undefined) continue
      const length = Math.hypot(to.x - from.x, to.y - from.y)
      const unitX = (to.x - from.x) / length
      const unitY = (to.y - from.y) / length
      lines += `M${(from.x + unitX * from.reach).toFixed(1)} ${(from.y + unitY * from.reach).toFixed(1)}L${(to.x - unitX * to.reach).toFixed(1)} ${(to.y - unitY * to.reach).toFixed(1)}`
    }
  }
  return `<path d="${lines}" stroke="${blend('#8ea6ff', 0.24, SKY_BASE)}" stroke-width="2.2" stroke-dasharray="0 8"/>` + winks.map((layer, index) => `<g class="wink p${index}">${writeLayer(layer)}</g>`).join('')
}

/** The near hills: two flanks with a deep valley between them, because the prompt box sits over the middle. */
function frontRidge(x: number): number {
  return 990 - 140 * smoothStep(1000, 1640, x) - 180 * (1 - smoothStep(-60, 500, x)) - 10 * Math.sin(x / 173 + 0.6) - 6 * Math.sin(x / 61 + 2.1)
}

function backRidge(x: number): number {
  return 968 - 110 * smoothStep(1120, 1520, x) + 50 * smoothStep(1500, 1720, x) - 110 * (1 - smoothStep(60, 640, x)) - 12 * Math.sin(x / 227 + 2.4) - 6 * Math.sin(x / 83 + 0.3)
}

/** A hill's outline. Filled flat behind the hill's dots, so the sky's dots stop at the hill. */
function ridgeOutline(ridge: (x: number) => number): string {
  let d = 'M-30 1010'
  for (let x = -30; x <= 1630; x += 10) d += `L${x} ${ridge(x).toFixed(1)}`
  return `${d}L1630 1010z`
}

/** The near hill's rim: one row of dots just under its crest, in a dark tone that never competes with the sky. */
function ridgeDots(): string {
  const layer: Layer = new Map()
  for (let cellColumn = -1; cellColumn * CELL_WIDTH < 1610; cellColumn += 1) {
    for (let cellRow = Math.floor(720 / CELL_HEIGHT); cellRow * CELL_HEIGHT < 1010; cellRow += 1) {
      for (let dot = 0; dot < 8; dot += 1) {
        const x = dotX(cellColumn, dot % 2)
        const y = dotY(cellRow, dot >> 1)
        const depth = y - frontRidge(x) - 4
        if (depth >= 0 && depth < 8 && hashUnit(x, y, 13) < 0.94) addDot(layer, 'ridgeCrest', x, y)
      }
    }
  }
  return writeLayer(layer)
}

// Where the soft light under the band lies: spine sample, long radius, short radius, gradient.
const GLOW_SPOTS: readonly (readonly [number, number, number, string])[] = [[14, 300, 110, 'glowBlue'], [32, 330, 150, 'glowCore'], [47, 280, 130, 'glowBlue']]

/** A soft light under the band, so its dots sit in a cloud: three long ellipses laid along the spine, each breathing a little out of step. */
function bandGlow(spine: readonly SpineSample[]): string {
  let out = ''
  for (const [index, spot] of GLOW_SPOTS.entries()) {
    const sample = spine[spot[0]]
    if (sample === undefined) continue
    const angle = (Math.atan2(sample.tangentY, sample.tangentX) * 180) / Math.PI
    out += `<ellipse class="breath b${index}" cx="${sample.x.toFixed(0)}" cy="${sample.y.toFixed(0)}" rx="${spot[1]}" ry="${spot[2]}" fill="url(#${spot[3]})" transform="rotate(${angle.toFixed(1)} ${sample.x.toFixed(0)} ${sample.y.toFixed(0)})"/>`
  }
  return out
}

/** One shooting star: a run of dots that fades behind itself, heading down into the band's fringe. */
function shootingStar(): string {
  let out = ''
  for (let index = 0; index < 20; index += 1) {
    const opacity = Number(Math.pow(0.84, index).toFixed(2))
    out += `<path d="M${(1215 - index * 9.6).toFixed(1)} ${(470 - index * 6).toFixed(1)}h0" stroke="${blend(index < 3 ? '#fff6d0' : '#e6ebff', opacity, SKY_BASE)}" stroke-width="${index === 0 ? 5.4 : index < 4 ? 4.2 : 3.4}"/>`
  }
  return `<g class="shoot">${out}</g>`
}

export function brailleStarsSvg(): string {
  const spine = milkyWaySpine()

  const style = `
path{fill:none;stroke-linecap:round}
.sky{transform-origin:${POLE_X}px ${POLE_Y}px;animation:turn 280s steps(560) -140s infinite alternate}
.second{stroke-opacity:0}
.first{animation:first ${SHIMMER_SECONDS}s steps(1) infinite}.second{animation:second ${SHIMMER_SECONDS}s steps(1) infinite}
.breath{animation:breath 74s steps(12) infinite alternate}.b1{animation-delay:-25s}.b2{animation-delay:-50s}
.pulse{animation:pulse 9s steps(1) infinite}.wink{animation:wink 9s steps(1) infinite}.p1{animation-duration:11s;animation-delay:-3s}.p2{animation-duration:13s;animation-delay:-8s}.p3{animation-duration:14s;animation-delay:-5s}
.tw .medium,.tw .large{stroke-opacity:0}
.tw .small{animation:small 11s steps(1) infinite}.tw .medium{animation:medium 11s steps(1) infinite}.tw .large{animation:large 11s steps(1) infinite}
.tw.t1 g{animation-duration:13s;animation-delay:-4s}.tw.t2 g{animation-duration:17s;animation-delay:-11s}
.tw.t3 g{animation-duration:9s;animation-delay:-6s}.tw.t4 g{animation-duration:19s;animation-delay:-2s}.tw.t5 g{animation-duration:14s;animation-delay:-8.5s}
.shoot{stroke-opacity:0;animation:shoot 46s linear -37.9s infinite}
@keyframes turn{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}
@keyframes first{0%{stroke-opacity:1}40%{stroke-opacity:.66}43%{stroke-opacity:.33}46%{stroke-opacity:0}90%{stroke-opacity:.33}93%{stroke-opacity:.66}96%{stroke-opacity:1}100%{stroke-opacity:1}}
@keyframes second{0%{stroke-opacity:0}40%{stroke-opacity:.33}43%{stroke-opacity:.66}46%{stroke-opacity:1}90%{stroke-opacity:.66}93%{stroke-opacity:.33}96%{stroke-opacity:0}100%{stroke-opacity:0}}
@keyframes breath{from{fill-opacity:.7}to{fill-opacity:1}}
@keyframes pulse{0%{stroke-opacity:1}30%{stroke-opacity:.8}36%{stroke-opacity:.65}42%{stroke-opacity:.5}48%{stroke-opacity:.35}70%{stroke-opacity:.5}76%{stroke-opacity:.6}82%{stroke-opacity:.8}88%{stroke-opacity:1}100%{stroke-opacity:1}}
@keyframes wink{0%{stroke-opacity:1}40%{stroke-opacity:.8}46%{stroke-opacity:.62}52%{stroke-opacity:.45}70%{stroke-opacity:.62}76%{stroke-opacity:.8}82%{stroke-opacity:1}100%{stroke-opacity:1}}
@keyframes small{0%{stroke-opacity:1}30%{stroke-opacity:.6}36%{stroke-opacity:.25}42%{stroke-opacity:0}92%{stroke-opacity:.3}96%{stroke-opacity:.7}100%{stroke-opacity:1}}
@keyframes medium{0%{stroke-opacity:0}30%{stroke-opacity:.4}36%{stroke-opacity:.75}42%{stroke-opacity:1}58%{stroke-opacity:.6}62%{stroke-opacity:.25}66%{stroke-opacity:0}80%{stroke-opacity:.4}84%{stroke-opacity:1}92%{stroke-opacity:.6}96%{stroke-opacity:.25}100%{stroke-opacity:0}}
@keyframes large{0%{stroke-opacity:0}58%{stroke-opacity:.4}62%{stroke-opacity:.75}66%{stroke-opacity:1}80%{stroke-opacity:.6}84%{stroke-opacity:0}100%{stroke-opacity:0}}
@keyframes shoot{0%,95%{stroke-opacity:0;transform:translate(0,0)}95.5%{stroke-opacity:1}99.2%{stroke-opacity:.9}100%{stroke-opacity:0;transform:translate(260px,162px)}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  const defs = `
<linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#080d26"/><stop offset="0.4" stop-color="#0b1230"/><stop offset="0.75" stop-color="#0f183e"/><stop offset="1" stop-color="#121c48"/></linearGradient>
<radialGradient id="glowBlue"><stop offset="0" stop-color="#2b3676" stop-opacity="0.32"/><stop offset="0.35" stop-color="#2b3676" stop-opacity="0.2"/><stop offset="0.7" stop-color="#2b3676" stop-opacity="0.07"/><stop offset="1" stop-color="#2b3676" stop-opacity="0"/></radialGradient>
<radialGradient id="glowCore"><stop offset="0" stop-color="#3d3a7c" stop-opacity="0.42"/><stop offset="0.4" stop-color="#30367a" stop-opacity="0.22"/><stop offset="0.72" stop-color="#2b3676" stop-opacity="0.07"/><stop offset="1" stop-color="#2b3676" stop-opacity="0"/></radialGradient>`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
<rect width="1600" height="1000" fill="url(#night)"/>
<g class="sky">
${bandGlow(spine)}
${milkyWayCells(spine)}
${fieldStars(spine)}
${figures()}
</g>
${shootingStar()}
<path d="${ridgeOutline(backRidge)}" style="fill:#0a1030"/><path d="${ridgeOutline(frontRidge)}" style="fill:#070b1f"/>
${ridgeDots()}
</svg>`
}
