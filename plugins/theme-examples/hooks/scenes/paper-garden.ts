// Paper Garden: cut-paper leaves laid in from the corners of a warm white sheet, and the same scene on dark kraft.
// Pure string building. Every piece of paper is a faceted (scissor-cut) outline in <defs>,
// drawn four times: far shadow, near shadow, a light lip up and left, then the paper itself.

type Point = [number, number]

/** 0 paints the cream sheet, 1 the dark kraft sheet. */
type Stock = 0 | 1

/** Paint names are CSS classes, so the two stocks differ only in one block of fill rules. [cream, kraft] */
const PAINTS: Record<string, [string, string]> = {
  ground: ['#efe8d8', '#24211d'],
  page: ['#f8f3e9', '#2e2b26'],
  fleck: ['#8f7c50', '#b8ad8c'],
  shadow: ['#5c4a26', '#000000'],
  lip: ['#ffffff', '#f3ecd9'],
  pale: ['#d3dbc1', '#39432f'],
  sage: ['#b4c29f', '#4b5f45'],
  mid: ['#8ba274', '#5d7455'],
  fern: ['#7f9b6c', '#62795a'],
  olive: ['#6f8a5c', '#6f8566'],
  coral: ['#dc6549', '#c9604a'],
  coralLight: ['#e58267', '#e4846a'],
  coralDark: ['#c65a42', '#b5503a'],
  seed: ['#8a3a2c', '#6e2c21'],
}

/** Shadow and lip strengths per stock: dark paper needs heavier shadows and a fainter lip. */
const TONES: [string, string] = [
  '.far{opacity:.05}.near{opacity:.11}.edge{opacity:.38}',
  '.far{opacity:.2}.near{opacity:.35}.edge{opacity:.14}',
]

/** How a piece moves. An empty name means it has no motion of its own; zero seconds means the class's own pace. */
interface Motion {
  name: string
  lifting: boolean
  seconds: number
  delay: number
  noLip: boolean
}

const STILL: Motion = { name: '', lifting: false, seconds: 0, delay: 0, noLip: false }

interface SingleLayer {
  kind: 'single'
  shape: string
  x: number
  y: number
  turn: number
  fill: string
  lift: number
  seconds: number
  sway: string
  lifting: boolean
}

interface SprigLayer {
  kind: 'sprig'
  id: string
  leaflet: string
  length: number
  bend: number
  thick: number
  pairs: number
  bare: number
  spread: number
  segments: number
  seed: number
  x: number
  y: number
  turn: number
  fill: string
  lift: number
  seconds: number
  sway: string
}

interface BloomLayer {
  kind: 'bloom'
}

type Layer = SingleLayer | SprigLayer | BloomLayer

/** What one layer adds to the scene: its markup, and the outlines it needs in <defs>. */
interface Built {
  markup: string
  shapes: Array<[string, string]>
}

/** A repeatable number in 0..1 from two integers, so every build is the same. */
function hash(a: number, b: number): number {
  let h = (Math.round(a) * 374761393 + Math.round(b) * 668265263) >>> 0
  h = ((h ^ (h >>> 13)) * 1274126177) >>> 0
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296
}

function jitter(seed: number, index: number, spread: number): number {
  return 1 + (hash(seed, index) - 0.5) * 2 * spread
}

/** Leans a point sideways by the square of its height, which bends a straight leaf into an arc. */
function bendPoint(point: Point, length: number, amount: number): Point {
  const height = Math.max(0, -point[1] / length)
  return [point[0] + amount * length * height * height, point[1] + Math.abs(amount) * length * height * height * 0.18]
}

function bendAll(points: Point[], length: number, amount: number): Point[] {
  return points.map(point => bendPoint(point, length, amount))
}

function cubicAt(p0: Point, p1: Point, p2: Point, p3: Point, t: number): Point {
  const u = 1 - t
  return [
    u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
  ]
}

function pointAt(points: Point[], index: number): Point {
  return points[index] ?? [0, 0]
}

/** A closed outline of straight snips through the given corners, in whole pixels. */
function polygonPath(corners: Point[]): string {
  return 'M' + corners.map(point => `${Math.round(point[0])} ${Math.round(point[1])}`).join('L') + 'Z'
}

/** Cuts a smooth outline [start, c1, c2, end, c1, c2, end, ...] into straight snips about `snip` long, the way scissors would. */
function facet(points: Point[], snip: number, seed: number): string {
  const corners: Point[] = [pointAt(points, 0)]
  for (let i = 1; i + 2 < points.length; i += 3) {
    const p0 = pointAt(points, i - 1)
    const p1 = pointAt(points, i)
    const p2 = pointAt(points, i + 1)
    const p3 = pointAt(points, i + 2)
    const span = Math.hypot(p3[0] - p0[0], p3[1] - p0[1]) + Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * 0.5
    const cuts = Math.max(1, Math.round(span / snip))
    for (let k = 1; k <= cuts; k += 1) {
      const point = cubicAt(p0, p1, p2, p3, k / cuts)
      const wobble = k < cuts ? (hash(seed + i, k) - 0.5) * snip * 0.07 : 0
      corners.push([point[0] + wobble, point[1] - wobble])
    }
  }
  return polygonPath(corners)
}

/** A broad pointed leaf with slits cut along its veins, so whatever lies underneath shows through. */
function broadLeafPath(length: number, width: number, bend: number, seed: number, veins: number): string {
  const fat = jitter(seed, 1, 0.1)
  const outline: Point[] = [
    [-4, 0], [-4, 0], [-4, -length * 0.1], [-3, -length * 0.16],
    [-width * 1.02 * fat, -length * 0.24], [-width * 0.74, -length * 0.8], [0, -length],
    [width * 0.7, -length * 0.78], [width * 1.06 / fat, -length * 0.3], [3, -length * 0.16],
    [4, -length * 0.1], [4, 0], [4, 0],
  ]
  let d = facet(bendAll(outline, length, bend), length / 9, seed)
  for (let i = 0; i < veins; i += 1) {
    for (const side of [-1, 1]) {
      const from = -length * (0.3 + (0.5 * (i + (side > 0 ? 0.5 : 0))) / veins)
      const span = width * (0.56 - 0.24 * (i / veins)) * jitter(seed, i * 2 + side + 5, 0.1)
      const rise = length * 0.12
      const gap = 5 + width * 0.03
      const cut: Point[] = [
        [side * 9, from],
        [side * (9 + span * 0.4), from - rise * 0.2 - gap], [side * (9 + span * 0.8), from - rise * 0.7 - gap], [side * (9 + span), from - rise],
        [side * (9 + span * 0.85), from - rise * 0.6 + gap], [side * (9 + span * 0.4), from - rise * 0.1 + gap], [side * 9, from],
      ]
      d += facet(bendAll(cut, length, bend), span / 2.5, seed + i)
    }
  }
  return d
}

/** A long narrow blade of grass. */
function bladePath(length: number, width: number, bend: number, seed: number): string {
  const outline: Point[] = [
    [-width * 0.25, 0], [-width * 0.7, -length * 0.2], [-width * 0.6, -length * 0.7], [0, -length],
    [width * 0.5, -length * 0.66], [width * 0.75, -length * 0.22], [width * 0.25, 0],
    [width * 0.25, 0], [-width * 0.25, 0], [-width * 0.25, 0],
  ]
  return facet(bendAll(outline, length, bend), length / 7, seed)
}

/** A paddle leaflet lying along +x from a narrow neck at the origin: the Matisse lobe. */
function paddlePath(reach: number, thickness: number, seed: number): string {
  const outline: Point[] = [
    [0, thickness * 0.3],
    [reach * 0.3, thickness * 0.35], [reach * 0.96, thickness * 1.5], [reach, 0],
    [reach * 1.02, -thickness * 1.35], [reach * 0.34, -thickness * 0.45], [0, -thickness * 0.3],
    [0, -thickness * 0.3], [0, thickness * 0.3], [0, thickness * 0.3],
  ]
  return facet(outline, reach / 8, seed)
}

/** A coin leaf on a short stalk, lying along +x: the eucalyptus leaf, cut a little out of round. */
function coinPath(radius: number, seed: number): string {
  const sides = 22
  const corners: Point[] = [[0, 2], [radius * 0.35, 2]]
  for (let i = 1; i < sides; i += 1) {
    const angle = Math.PI - (i / sides) * Math.PI * 2
    const reach = radius * jitter(seed, i, 0.035)
    corners.push([radius * 1.3 + Math.cos(angle) * reach, -Math.sin(angle) * reach * 0.92])
  }
  corners.push([radius * 0.35, -2], [0, -2])
  return polygonPath(corners)
}

/** The big sheet the conversation lies on: straight top and bottom off the frame, long sides cut by hand with a slight wander. */
function pagePath(left: number, right: number, seed: number): string {
  const corners: Point[] = []
  const steps = 30
  for (let i = 0; i <= steps; i += 1) {
    const wander = (hash(seed, i) - 0.5) * 7 + Math.sin(i * 0.45 + seed) * 6
    corners.push([left + wander, -40 + (1080 * i) / steps])
  }
  for (let i = steps; i >= 0; i -= 1) {
    const wander = (hash(seed + 5, i) - 0.5) * 6 + Math.sin(i * 0.4 + seed) * 5
    corners.push([right + wander, -40 + (1080 * i) / steps])
  }
  return polygonPath(corners)
}

/** A scalloped disc cut by hand: one layer of the bloom. */
function discPath(radius: number, scallops: number, seed: number): string {
  const sides = scallops * 4
  const corners: Point[] = []
  for (let i = 0; i < sides; i += 1) {
    const angle = (i / sides) * Math.PI * 2
    const reach = radius * (1 + 0.09 * Math.cos(angle * scallops + seed)) * jitter(seed, i, 0.035)
    corners.push([Math.cos(angle) * reach, Math.sin(angle) * reach])
  }
  return polygonPath(corners)
}

function fixed(value: number): number {
  return Number(value.toFixed(1))
}

/** An offset on the page, expressed in a frame turned by `degrees`, to one decimal. */
function turnedOffset(x: number, y: number, degrees: number): Point {
  const angle = (degrees * Math.PI) / 180
  return [fixed(x * Math.cos(angle) - y * Math.sin(angle)), fixed(x * Math.sin(angle) + y * Math.cos(angle))]
}

function useMarkup(shape: string, offset: Point, paint: string, tone: string): string {
  return `<use href="#${shape}" transform="translate(${offset[0]} ${offset[1]})" class="${paint}${tone ? ` ${tone}` : ''}"/>`
}

/**
 * One piece of paper in the frame given by `place`. `facing` is how far that frame is turned from the page,
 * so the shadow can always fall down and to the right of the page whatever way the piece lies.
 */
function paper(shape: string, place: string, facing: number, fill: string, lift: number, motion: Motion): string {
  const far = turnedOffset(lift * 1.9, lift * 2.4, -facing)
  const near = turnedOffset(lift * 0.9, lift * 1.15, -facing)
  const lip = turnedOffset(-1.2, -1.2, -facing)
  let shadows = useMarkup(shape, far, 'shadow', 'far') + useMarkup(shape, near, 'shadow', 'near')
  if (motion.lifting) {
    const more = turnedOffset(lift * 1.3, lift * 1.6, -facing)
    const pace = motion.seconds ? `animation-duration:${motion.seconds}s;` : ''
    shadows = `<g class="lift" style="--lx:${more[0]}px;--ly:${more[1]}px;${pace}animation-delay:-${motion.delay}s">${shadows}</g>`
  }
  const body = shadows + (motion.noLip ? '' : useMarkup(shape, lip, 'lip', 'edge')) + useMarkup(shape, [0, 0], fill, '')
  const moving = motion.name ? `<g class="${motion.name}" style="animation-duration:${motion.seconds}s;animation-delay:-${motion.delay}s">${body}</g>` : body
  return `<g transform="${place}">${moving}</g>`
}

/** The stem between two heights, cut out on its own, so the sprig can flex at the joints. */
function stemPiece(item: SprigLayer, from: number, to: number): string {
  const left: Point[] = []
  const right: Point[] = []
  for (let k = 0; k <= 3; k += 1) {
    const along = from + ((to - from) * k) / 3
    const half = item.thick * (1 - 0.8 * along) + 1
    left.push(bendPoint([-half, -along * item.length], item.length, item.bend))
    right.unshift(bendPoint([half, -along * item.length], item.length, item.bend))
  }
  return polygonPath(left.concat(right))
}

/**
 * A stem with leaflets up both sides. The stem is cut into segments that each flex about their lower joint,
 * so the sway compounds towards the tip like a real stalk; each leaflet also stirs about its own neck.
 */
function sprig(item: SprigLayer, index: number): Built {
  const count = item.pairs * 2
  const pieces: string[] = []
  for (let k = 0; k < item.segments; k += 1) pieces.push('')
  for (let i = 0; i <= count; i += 1) {
    const isTip = i === count
    const side = i % 2 === 0 ? -1 : 1
    const along = isTip ? 0.985 : item.bare + (1 - item.bare) * ((i + 0.6) / (count + 1.4))
    const root = bendPoint([0, -along * item.length], item.length, item.bend)
    const lean = Math.atan(2 * item.bend * along) * (180 / Math.PI)
    const spread = (item.spread - 14 * along) * jitter(item.seed, i, 0.1)
    const angle = isTip ? lean - 90 : lean - 90 + side * spread
    const envelope = isTip ? 0.8 : 0.62 + 0.38 * Math.sin(Math.PI * (0.12 + 0.7 * (i / count)))
    const scale = fixed(envelope * jitter(item.seed, i + 30, item.leaflet === 'coin' ? 0.22 : 0.08))
    const place = `translate(${Math.round(root[0])} ${Math.round(root[1])}) rotate(${fixed(angle)}) scale(${scale})`
    const motion: Motion = {
      name: 'stir',
      lifting: true,
      seconds: 7 + 2 * Math.round(hash(item.seed, i + 50) * 3),
      delay: fixed(i * 1.3 + hash(item.seed, i + 70) * 3),
      noLip: false,
    }
    const segment = Math.min(item.segments - 1, Math.floor(along * item.segments))
    pieces[segment] = (pieces[segment] ?? '') + paper(item.leaflet, place, item.turn + angle, item.fill, item.lift / scale, motion)
  }
  const shapes: Array<[string, string]> = []
  let body = ''
  for (let k = item.segments - 1; k >= 0; k -= 1) {
    const from = k / item.segments
    const to = (k + 1) / item.segments
    const id = `${item.id}Stem${k}`
    shapes.unshift([id, stemPiece(item, from, Math.min(1, to + 0.01))])
    const joint = bendPoint([0, -from * item.length], item.length, item.bend)
    const inner = paper(id, '', item.turn, item.fill, item.lift * 0.6, STILL) + (pieces[k] ?? '') + body
    body = k === 0 ? inner : `<g class="flex" style="transform-origin:${Math.round(joint[0])}px ${Math.round(joint[1])}px;animation-duration:${11 + k * 6}s;animation-delay:-${fixed(hash(item.seed, k) * 20)}s">${inner}</g>`
  }
  const markup =
    `<g class="${item.sway}" style="transform-origin:${item.x}px ${item.y}px;animation-duration:${item.seconds}s;animation-delay:-${fixed(hash(index, 7) * item.seconds)}s">` +
    `<g transform="translate(${item.x} ${item.y}) rotate(${item.turn})">${body}</g></g>`
  return { markup, shapes }
}

/** A single big piece (leaf, blade, sheet) that sways about its stem end; zero seconds means it lies still. */
function single(item: SingleLayer, index: number): string {
  const motion: Motion = { name: '', lifting: item.lifting, seconds: 0, delay: fixed(hash(index, 3) * 14), noLip: item.fill === 'pale' }
  const inner = paper(item.shape, `translate(${item.x} ${item.y}) rotate(${item.turn})`, item.turn, item.fill, item.lift, motion)
  if (!item.seconds) return inner
  return `<g class="${item.sway}" style="transform-origin:${item.x}px ${item.y}px;animation-duration:${item.seconds}s;animation-delay:-${fixed(hash(index, 7) * item.seconds)}s">${inner}</g>`
}

/** Three hand-cut discs on a tapered stem, folded a little open: the one warm thing on the sheet. The head nods on the stem while the stem leans. */
function bloom(): string {
  const x = 1440
  const y = 832
  const rootX = 1570
  const rootY = 1100
  const stem = `M${rootX - 6} ${rootY}L1530 1000L1484 900L${x - 2} ${y}L${x + 3} ${y}L1492 896L1540 996L${rootX + 6} ${rootY}Z`
  return (
    `<g class="swayWide" style="transform-origin:${rootX}px ${rootY}px;animation-duration:23s;animation-delay:-4s">` +
    `<path d="${stem}" transform="translate(4 5)" class="shadow near"/><path d="${stem}" class="olive"/>` +
    `<g transform="translate(${x} ${y})"><g class="nod"><g transform="scale(0.9)">` +
    paper('discBack', 'translate(-5 4) rotate(8)', 8, 'coralDark', 4, { name: 'openBack', lifting: false, seconds: 19, delay: 3, noLip: false }) +
    paper('discMiddle', 'translate(4 -3) rotate(-14)', -14, 'coral', 4, { name: 'open', lifting: false, seconds: 19, delay: 3, noLip: false }) +
    paper('discFront', 'translate(-2 2) rotate(20)', 20, 'coralLight', 3, { name: 'open', lifting: false, seconds: 19, delay: 1, noLip: false }) +
    '<circle r="13" class="coralDark"/><circle r="6" class="seed"/>' +
    '</g></g></g></g>'
  )
}

function layer(item: Layer, index: number): Built {
  if (item.kind === 'bloom') return { markup: bloom(), shapes: [] }
  if (item.kind === 'sprig') return sprig(item, index)
  return { markup: single(item, index), shapes: [] }
}

/** The outlines every scene needs, whatever the layers add. */
function baseShapes(): Array<[string, string]> {
  return [
    ['leafGreat', broadLeafPath(660, 150, 0.16, 5, 4)],
    ['leafMid', broadLeafPath(440, 108, -0.2, 8, 3)],
    ['bladeLong', bladePath(430, 30, 0.2, 4)],
    ['bladeShort', bladePath(300, 24, -0.26, 6)],
    ['paddle', paddlePath(150, 30, 12)],
    ['coin', coinPath(31, 21)],
    ['page', pagePath(422, 1196, 7)],
    ['discBack', discPath(58, 5, 2)],
    ['discMiddle', discPath(45, 6, 5)],
    ['discFront', discPath(30, 5, 9)],
  ]
}

/** Back to front. turn 0 points up the page; each stem end sits off the sheet. Nothing here reaches x 432..1200. */
const LAYERS: Layer[] = [
  // the page: its long edges fall in the gaps between the app's panels (24-27% and 75-77% of the width); margins are a darker, flecked paper
  { kind: 'single', shape: 'page', x: 0, y: 0, turn: 0, fill: 'page', lift: 3, seconds: 0, sway: 'sway', lifting: false },
  // bottom left lives under the sidebar glass: one corner only, large, simple, low contrast, so it dissolves into a tone
  { kind: 'single', shape: 'leafGreat', x: 20, y: 1190, turn: 14, fill: 'pale', lift: 4, seconds: 61, sway: 'sway', lifting: true },
  { kind: 'sprig', id: 'fern', leaflet: 'paddle', length: 520, bend: 0.1, thick: 6, pairs: 4, bare: 0.26, spread: 56, segments: 3, seed: 11, x: 190, y: 1130, turn: -10, fill: 'sage', lift: 5, seconds: 38, sway: 'sway' },
  // right edge, all below the cards and right of x 1400: a pale leaf, and over it a drooping coin branch in two stacked greens
  { kind: 'single', shape: 'leafMid', x: 1720, y: 330, turn: 244, fill: 'pale', lift: 4, seconds: 23, sway: 'swayBack', lifting: true },
  { kind: 'sprig', id: 'under', leaflet: 'coin', length: 300, bend: 0.14, thick: 4, pairs: 2, bare: 0.34, spread: 60, segments: 2, seed: 53, x: 1680, y: 318, turn: 222, fill: 'sage', lift: 4, seconds: 19, sway: 'swayWide' },
  { kind: 'sprig', id: 'vine', leaflet: 'coin', length: 390, bend: -0.1, thick: 4, pairs: 2, bare: 0.3, spread: 64, segments: 3, seed: 29, x: 1672, y: 282, turn: 203, fill: 'fern', lift: 6, seconds: 14, sway: 'swayWide' },
  // bottom right: grass first, so nothing crosses the face of the bloom
  { kind: 'single', shape: 'leafMid', x: 1600, y: 1150, turn: -12, fill: 'pale', lift: 4, seconds: 29, sway: 'swayBack', lifting: true },
  { kind: 'single', shape: 'bladeShort', x: 1630, y: 1060, turn: -26, fill: 'fern', lift: 7, seconds: 11, sway: 'swayWide', lifting: true },
  { kind: 'single', shape: 'bladeLong', x: 1680, y: 1090, turn: -44, fill: 'mid', lift: 6, seconds: 17, sway: 'swayWide', lifting: true },
  { kind: 'bloom' },
]

/** Short paper fibres for the margins, scattered by hash; the page sheet covers them in the middle. */
function fleckPath(): string {
  let d = ''
  for (let i = 0; i < 26; i += 1) {
    const x = Math.round(hash(i, 1) * 168)
    const y = Math.round(hash(i, 2) * 206)
    const angle = hash(i, 3) * Math.PI
    const reach = 2 + hash(i, 4) * 3
    d += `M${x} ${y}l${fixed(Math.cos(angle) * reach)} ${fixed(Math.sin(angle) * reach)}l1 1z`
  }
  return d
}

function paintRules(stock: Stock): string {
  return Object.entries(PAINTS).map(([name, values]) => `.${name}{fill:${values[stock]}}`).join('')
}

/** The whole scene on one stock of paper. */
function sceneSvg(stock: Stock): string {
  const style =
    paintRules(stock) + TONES[stock] +
    '.sway{animation:sway 40s ease-in-out infinite alternate}' +
    '.swayWide{animation:swayWide 20s ease-in-out infinite alternate}' +
    '.stir{animation:stir 12s ease-in-out infinite alternate}' +
    '.lift{animation:lift 14s ease-in-out infinite alternate}' +
    '.open{animation:open 19s ease-in-out infinite alternate}' +
    '.openBack{animation:openBack 19s ease-in-out infinite alternate}' +
    '.nod{animation:nod 11s ease-in-out infinite alternate}' +
    '.swayBack{animation:swayBack 23s ease-in-out infinite alternate}' +
    '.flex{animation:flex 17s ease-in-out infinite alternate}' +
    '@keyframes sway{from{transform:rotate(-2.4deg)}to{transform:rotate(2.8deg)}}' +
    '@keyframes swayWide{from{transform:rotate(-4deg)}to{transform:rotate(4.5deg)}}' +
    '@keyframes stir{from{transform:rotate(-7deg)}to{transform:rotate(8deg)}}' +
    '@keyframes lift{from{transform:translate(0,0)}to{transform:translate(var(--lx),var(--ly))}}' +
    '@keyframes open{from{transform:scale(0.95) rotate(-4deg)}to{transform:scale(1.05) rotate(5deg)}}' +
    '@keyframes openBack{from{transform:scale(0.98) rotate(3deg)}to{transform:scale(1.03) rotate(-3deg)}}' +
    '@keyframes swayBack{from{transform:translate(-5px,3px) rotate(1.6deg)}to{transform:translate(4px,-4px) rotate(-1.8deg)}}' +
    '@keyframes flex{from{transform:rotate(-3deg)}to{transform:rotate(3.6deg)}}' +
    '@keyframes nod{from{transform:rotate(-9deg)}to{transform:rotate(7deg)}}' +
    '@media (prefers-reduced-motion: reduce){*{animation:none!important}}'
  const built = LAYERS.map(layer)
  const shapes = baseShapes().concat(built.flatMap(part => part.shapes))
  const defs =
    shapes.map(([id, d]) => `<path id="${id}" d="${d}" fill-rule="evenodd"/>`).join('') +
    `<pattern id="flecks" width="173" height="211" patternUnits="userSpaceOnUse"><path class="fleck" opacity="0.09" d="${fleckPath()}"/></pattern>`
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888">' +
    `<style>${style}</style><defs>${defs}</defs>` +
    '<rect width="1600" height="1000" class="ground"/><rect width="1600" height="1000" fill="url(#flecks)"/>' +
    built.map(part => part.markup).join('') +
    '</svg>'
  )
}

/** Paper Garden: cream paper, for light windows. */
export function paperGardenSvg(): string {
  return sceneSvg(0)
}

/** Paper Garden, Kraft: the same cut paper on dark kraft, for dark windows. */
export function paperGardenKraftSvg(): string {
  return sceneSvg(1)
}
