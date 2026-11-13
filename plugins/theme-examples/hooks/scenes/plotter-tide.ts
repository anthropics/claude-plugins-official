// Plotter Tide: a pen plotter drawing a chart coast. The land in the two lower corners is hatched in a rust pen;
// the sea is "water-lined" in a slate pen: every tide line is the coast pushed seaward by a gap that is always positive
// and grows with distance, so the lines crowd the shore, calm down further out, and never cross.
// A pen works through each set line by line; the oldest lines wash away and are drawn again, so the sheet is never finished.
// Two stocks: warm paper for a light window, blue-black night paper for a dark one. Pure string building.

const WIDTH = 1600
const HEIGHT = 1000
/** The conversation sits between these; no ink goes between them. */
const COLUMN_LEFT = 432
const COLUMN_RIGHT = 1200

interface Stock {
  paper: string
  land: string
  ink: string
  rust: string
}

const DAY: Stock = { paper: '#f3eee3', land: '#e8d6bd', ink: '#1f2a48', rust: '#c4552d' }
/** The same drawing in pale ink on blue-black paper. */
const NIGHT: Stock = { paper: '#141a27', land: '#1c2333', ink: '#aab6d0', rust: '#e98a5e' }

interface Point {
  x: number
  y: number
}

interface Sample {
  point: Point
  inked: boolean
}

/** One piece of land and the sea around it. An islet is a closed ring; a coast is an arc whose centre lies off the sheet. */
interface Coast {
  seed: number
  isIslet: boolean
  centreX: number
  centreY: number
  landRadius: number
  bayDepth: number
  lineCount: number
  firstGap: number
  gapGrowth: number
  fullUntil: number
  keepToward: number
  angleFrom: number
  angleTo: number
  hatchLean: number
}

/** One pen's work. A zero in drawShare, farFrom or coastWidth means "not used". */
interface Job {
  name: string
  ink: string
  width: number
  opacity: number
  opacityFade: number
  cycleSeconds: number
  cycleStart: number
  absentShare: number
  drawShare: number
  farFrom: number
  coastWidth: number
  hidePen: boolean
}

interface JobMarkup {
  shapes: string
  keyframes: string
  strokes: string
  farStrokes: string
}

// The big coast: bottom right, where no panel sits over it.
const EAST_COAST: Coast = {
  seed: 1, isIslet: false, centreX: 1650, centreY: 1050, landRadius: 300, bayDepth: 62, lineCount: 14, firstGap: 11, gapGrowth: 1.062,
  fullUntil: 0.5, keepToward: 0.7, angleFrom: Math.PI * 0.95, angleTo: Math.PI * 1.55, hatchLean: 1,
}
// The spit: bottom left, under the quiet lower half of the sidebar.
const WEST_SPIT: Coast = {
  seed: 2, isIslet: false, centreX: -50, centreY: 1070, landRadius: 300, bayDepth: 56, lineCount: 17, firstGap: 11, gapGrowth: 1.058,
  fullUntil: 0.5, keepToward: 0.3, angleFrom: -Math.PI * 0.58, angleTo: Math.PI * 0.05, hatchLean: 1,
}
// The islet: small, right of the conversation and below the cards, so the top half of the sheet is not bare.
const ISLET: Coast = {
  seed: 5, isIslet: true, centreX: 1436, centreY: 334, landRadius: 26, bayDepth: 7, lineCount: 5, firstGap: 7.5, gapGrowth: 1.2,
  fullUntil: 1, keepToward: 0.5, angleFrom: 0, angleTo: Math.PI * 2, hatchLean: 1,
}

/** A fixed pseudo-random number in 0..1 for a whole number, so every build is the same. */
function hash(number: number): number {
  const value = Math.sin(number * 127.1 + 311.7) * 43758.5453
  return value - Math.floor(value)
}

function round(value: number): number {
  return Math.round(value * 10) / 10
}

/** The coast's shape in -1..1 at a place `along` the shore (pixels). `calm` 0..1 smooths the small bays out, the way the sea does further from land. */
function bays(along: number, coast: Coast, calm: number): number {
  // An islet closes on itself, so its bays must fit a whole number of times into one turn.
  const turn = along / coast.landRadius
  const wide = coast.isIslet ? Math.sin(turn * 2 + coast.seed) : Math.sin(along / 97 + coast.seed * 1.7)
  const middle = (coast.isIslet ? Math.sin(turn * 3 + coast.seed * 2) : Math.sin(along / 41 + coast.seed * 3.1)) * (1 - calm)
  const small = (coast.isIslet ? Math.sin(turn * 5 + coast.seed * 3) : Math.sin(along / 17 + coast.seed * 5.3)) * (1 - calm) * (1 - calm)
  return (wide + 0.55 * middle + 0.25 * small) / 1.8
}

/** Distance from the coast's centre to tide line `line` at `angle`; line 0 is the coast itself. */
function radiusAt(angle: number, line: number, coast: Coast): number {
  const along = angle * coast.landRadius
  let radius = coast.landRadius + coast.bayDepth * bays(along, coast, 0)
  let gap = coast.firstGap
  for (let step = 1; step <= line; step += 1) {
    const calm = Math.min(1, step / (coast.lineCount * 0.8))
    // Wider gaps in the bays, narrower off the headlands: that is what flattens the lines seaward. Never below 0.64 of the gap, about 7 px at the shore.
    radius += gap * (1 - 0.36 * bays(along, coast, calm))
    gap *= coast.gapGrowth
  }
  return radius
}

function pointAt(angle: number, line: number, coast: Coast): Point {
  const radius = radiusAt(angle, line, coast)
  return { x: coast.centreX + radius * Math.cos(angle), y: coast.centreY + radius * Math.sin(angle) }
}

function isOnSheet(point: Point): boolean {
  return point.x > -30 && point.x < WIDTH + 30 && point.y > -30 && point.y < HEIGHT + 30
}

/** Outside the reading column; each line stops a different distance short of it, so the ends do not make a wall. */
function isOutsideColumn(point: Point, line: number, coast: Coast): boolean {
  const shy = 80 * hash(line * 17 + coast.seed * 7)
  return point.x < COLUMN_LEFT - shy || point.x > COLUMN_RIGHT + shy
}

function isOnLand(point: Point, coast: Coast): boolean {
  const dx = point.x - coast.centreX
  const dy = point.y - coast.centreY
  // atan2 answers in -pi..pi; the coast's own angles may lie a whole turn above that.
  let angle = Math.atan2(dy, dx)
  if (!coast.isIslet && angle < coast.angleFrom - 0.5) angle += Math.PI * 2
  return Math.hypot(dx, dy) < radiusAt(angle, 0, coast) - 5
}

function midway(first: Point, second: Point): string {
  return `${round((first.x + second.x) / 2)} ${round((first.y + second.y) / 2)}`
}

/** A smooth open path through the midpoints of the samples: one point per segment, so the string stays short. */
function smoothPath(points: Point[]): string {
  const first = points[0]
  const second = points[1]
  const third = points[2]
  const last = points[points.length - 1]
  if (points.length < 4 || !first || !second || !third || !last) return ''
  let path = `M${round(first.x)} ${round(first.y)}Q${round(second.x)} ${round(second.y)} ${midway(second, third)}`
  for (let index = 2; index < points.length - 1; index += 1) {
    const here = points[index]
    const next = points[index + 1]
    if (here && next) path += `T${midway(here, next)}`
  }
  return `${path}T${round(last.x)} ${round(last.y)}`
}

/** The same for a closed ring. */
function smoothRing(points: Point[]): string {
  const count = points.length
  const closing = points[count - 1]
  let path = ''
  for (let index = 0; index < count; index += 1) {
    const here = points[index]
    const next = points[(index + 1) % count]
    if (!here || !next || !closing) continue
    if (index === 0) path = `M${midway(closing, here)}Q${round(here.x)} ${round(here.y)} ${midway(here, next)}`
    else path += `T${midway(here, next)}`
  }
  return `${path}Z`
}

/** The longest unbroken run of samples that may be inked. */
function longestRun(samples: Sample[]): Point[] {
  let best: Point[] = []
  let run: Point[] = []
  for (const sample of samples) {
    if (sample.inked) run.push(sample.point)
    else {
      if (run.length > best.length) best = run
      run = []
    }
  }
  return run.length > best.length ? run : best
}

/** The coast and its tide lines, path strings, shore first. The outer lines are shorter pieces. */
function tideLines(coast: Coast): string[] {
  const paths: string[] = []
  for (let line = 0; line <= coast.lineCount; line += 1) {
    const stepAngle = 16 / radiusAt((coast.angleFrom + coast.angleTo) / 2, line, coast)
    const samples: Sample[] = []
    for (let angle = coast.angleFrom; angle <= coast.angleTo; angle += stepAngle) {
      const point = pointAt(angle, line, coast)
      samples.push({ point, inked: isOnSheet(point) && isOutsideColumn(point, line, coast) })
    }
    const points = longestRun(samples)
    const share = line / coast.lineCount
    const fade = Math.max(0, (share - coast.fullUntil) / (1 - coast.fullUntil))
    const keep = Math.max(4, Math.floor(points.length * (1 - fade * (0.35 + 0.3 * hash(line + coast.seed * 31)))))
    const slack = Math.max(points.length - keep, 0)
    const start = Math.min(Math.max(Math.floor(slack * (coast.keepToward + (hash(line * 11 + coast.seed) - 0.5) * 0.4)), 0), slack)
    const kept = points.slice(start, start + keep)
    // The pen goes out along one line and comes back along the next, the way a plotter does.
    if (line % 2 === 1) kept.reverse()
    const path = smoothPath(kept)
    if (path) paths.push(path)
  }
  return paths
}

/** An islet's shore and tide lines: closed rings, shore first. */
function isletRings(coast: Coast): string[] {
  const paths: string[] = []
  for (let line = 0; line <= coast.lineCount; line += 1) {
    const count = Math.max(12, Math.round((radiusAt(0, line, coast) * 6.3) / 14))
    const points: Point[] = []
    for (let index = 0; index < count; index += 1) points.push(pointAt((index / count) * Math.PI * 2 + line * 0.9, line, coast))
    paths.push(smoothRing(points))
  }
  return paths
}

/** The land, one filled shape under the hatching: the coast, closed through its centre, which lies off the sheet. */
function landShape(coast: Coast, colour: string): string {
  let path = ''
  for (let angle = coast.angleFrom; angle <= coast.angleTo; angle += 0.04) {
    const point = pointAt(angle, 0, coast)
    path += `${path ? 'L' : 'M'}${round(point.x)} ${round(point.y)}`
  }
  if (!coast.isIslet) path += `L${coast.centreX} ${coast.centreY}`
  return `<path d="${path}Z" style="fill:${colour}" fill-opacity="0.6"/>`
}

/** Straight hatch strokes across the land, path strings in the order a pen would take them. */
function landHatch(coast: Coast): string[] {
  const paths: string[] = []
  const spacing = 15
  let stroke = 0
  for (let offset = -HEIGHT; offset < WIDTH + HEIGHT; offset += spacing) {
    // One hatch line runs down-left from (offset, 0); walk it and keep the piece that lies on the land.
    let first: Point | null = null
    let last: Point | null = null
    for (let step = 0; step < HEIGHT + 60; step += 4) {
      const point = { x: offset - step * coast.hatchLean, y: step }
      if (isOnSheet(point) && isOnLand(point, coast)) {
        if (!first) first = point
        last = point
      } else if (first) break
    }
    if (!first || !last || Math.hypot(last.x - first.x, last.y - first.y) < 14) continue
    const from = stroke % 2 === 0 ? first : last
    const to = stroke % 2 === 0 ? last : first
    paths.push(`M${round(from.x)} ${round(from.y)}L${round(to.x)} ${round(to.y)}`)
    stroke += 1
  }
  return paths
}

/** One pen's job: the paths drawn strictly one after another on a shared cycle, each washed away again before its next turn.
 * Returns the shapes for <defs>, the job's own keyframes, and the strokes (the far tide lines apart, so they can ride the tide further). */
function penJob(paths: string[], job: Job): JobMarkup {
  let shapes = ''
  let strokes = ''
  let farStrokes = ''
  let heads = ''
  let farHeads = ''
  const stepSeconds = job.cycleSeconds / paths.length
  // Normally a stroke takes exactly its turn; a job may ask for a shorter stroke, so its lines are rarely caught half made.
  const drawnAt = job.drawShare > 0 ? job.drawShare : round(100 / paths.length)
  const restUntil = 100 - job.absentShare - drawnAt
  for (let line = 0; line < paths.length; line += 1) {
    const id = `${job.name}${line}`
    // Line k starts one step after line k - 1, so it is one step less far into its cycle.
    const phase = (((job.cycleStart - line * stepSeconds) % job.cycleSeconds) + job.cycleSeconds) % job.cycleSeconds
    const timing = `style="animation-delay:${round(-phase)}s"`
    const opacity = round((job.opacity - job.opacityFade * (line / paths.length)) * 100) / 100
    shapes += `<path id="${id}" pathLength="1" d="${paths[line] ?? ''}"/>`
    // The first path of a land job is the coast itself: a firmer line than the hatching.
    const firm = line === 0 && job.coastWidth > 0 ? ` stroke-width="${job.coastWidth}" stroke-opacity="0.9"` : ` stroke-opacity="${opacity}"`
    const isFar = job.farFrom > 0 && line >= job.farFrom
    if (isFar) farStrokes += `<use href="#${id}" class="ink"${firm} ${timing}/>`
    else strokes += `<use href="#${id}" class="ink"${firm} ${timing}/>`
    if (!job.hidePen && isFar) farHeads += `<use href="#${id}" class="pen" ${timing}/>`
    else if (!job.hidePen) heads += `<use href="#${id}" class="pen" ${timing}/>`
  }
  const keyframes = `
.${job.name} .ink{animation:ink-${job.name} ${job.cycleSeconds}s linear infinite}.${job.name} .pen{animation:pen-${job.name} ${job.cycleSeconds}s linear infinite}
@keyframes ink-${job.name}{0%{stroke-dashoffset:1.01;opacity:1}${drawnAt}%{stroke-dashoffset:0;opacity:1}${round(drawnAt * 2.5)}%{stroke-dashoffset:0;opacity:.74}${restUntil}%{stroke-dashoffset:0;opacity:.74}${restUntil + drawnAt}%{stroke-dashoffset:-1.01}100%{stroke-dashoffset:-1.01;opacity:.74}}
@keyframes pen-${job.name}{0%{stroke-dashoffset:0;opacity:1}${drawnAt}%{stroke-dashoffset:-1;opacity:1}${drawnAt + 0.01}%{stroke-dashoffset:-1;opacity:0}100%{stroke-dashoffset:-1;opacity:0}}`
  const near = `<g class="${job.name}" stroke="${job.ink}" stroke-width="${job.width}">${strokes}${heads}</g>`
  const far = `<g class="${job.name}" stroke="${job.ink}" stroke-width="${job.width}">${farStrokes}${farHeads}</g>`
  return { shapes, keyframes, strokes: near, farStrokes: far }
}

/** The whole sheet on one stock. */
function plotterTideSheet(stock: Stock): string {
  const eastSea = penJob(tideLines(EAST_COAST).slice(1), { name: 'e', ink: stock.ink, width: 1.15, opacity: 1, opacityFade: 0.4, cycleSeconds: 136, cycleStart: 30, absentShare: 20, drawShare: 0, farFrom: 7, coastWidth: 0, hidePen: false })
  const westSea = penJob(tideLines(WEST_SPIT).slice(1), { name: 'w', ink: stock.ink, width: 1.15, opacity: 1, opacityFade: 0.4, cycleSeconds: 126, cycleStart: 75, absentShare: 20, drawShare: 0, farFrom: 8, coastWidth: 0, hidePen: false })
  const isletSea = penJob(isletRings(ISLET).slice(1), { name: 'i', ink: stock.ink, width: 1.1, opacity: 0.8, opacityFade: 0.3, cycleSeconds: 150, cycleStart: 40, absentShare: 14, drawShare: 5, farFrom: 0, coastWidth: 0, hidePen: true })
  const eastLand = penJob(tideLines(EAST_COAST).slice(0, 1).concat(landHatch(EAST_COAST)), { name: 'f', ink: stock.rust, width: 1, opacity: 0.8, opacityFade: 0, cycleSeconds: 118, cycleStart: 60, absentShare: 4, drawShare: 0, farFrom: 0, coastWidth: 1.3, hidePen: false })
  const westLand = penJob(tideLines(WEST_SPIT).slice(0, 1).concat(landHatch(WEST_SPIT)), { name: 'g', ink: stock.rust, width: 1, opacity: 0.8, opacityFade: 0, cycleSeconds: 104, cycleStart: 20, absentShare: 4, drawShare: 0, farFrom: 0, coastWidth: 1.3, hidePen: false })
  const isletLand = penJob(isletRings(ISLET).slice(0, 1), { name: 'j', ink: stock.rust, width: 1, opacity: 0.8, opacityFade: 0, cycleSeconds: 140, cycleStart: 9, absentShare: 6, drawShare: 6, farFrom: 0, coastWidth: 1.3, hidePen: true })
  const jobs = [eastSea, westSea, isletSea, eastLand, westLand, isletLand]

  const style = `
path{fill:none;stroke-linecap:round;stroke-linejoin:round}
.ink{stroke-dasharray:1 2}
.pen{stroke-dasharray:.0001 3;stroke-width:8;opacity:0}
.tide{animation:tide 70s ease-in-out infinite alternate}${jobs.map(job => job.keyframes).join('')}
@keyframes tide{from{transform:translate(0,0)}to{transform:var(--move)}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${jobs.map(job => job.shapes).join('')}</defs>
<rect width="${WIDTH}" height="${HEIGHT}" fill="${stock.paper}"/>
${landShape(EAST_COAST, stock.land)}${landShape(WEST_SPIT, stock.land)}${landShape(ISLET, stock.land)}
<g class="tide" style="--move:translate(-5px,-5px)">${eastSea.strokes}</g><g class="tide" style="--move:translate(-17px,-15px)">${eastSea.farStrokes}</g>
<g class="tide" style="--move:translate(5px,-5px);animation-delay:-35s">${westSea.strokes}</g><g class="tide" style="--move:translate(16px,-16px);animation-delay:-35s">${westSea.farStrokes}</g>
<g class="tide" style="--move:translate(-3px,3px);animation-delay:-36s">${isletSea.strokes}</g>
${eastLand.strokes}${westLand.strokes}${isletLand.strokes}
</svg>`
}

/** Plotter Tide on warm paper, for a light window (scene.svg). */
export function plotterTideSvg(): string {
  return plotterTideSheet(DAY)
}

/** Plotter Tide on blue-black night paper, for a dark window (scene-night.svg). */
export function plotterTideNightSvg(): string {
  return plotterTideSheet(NIGHT)
}
