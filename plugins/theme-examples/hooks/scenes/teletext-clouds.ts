// Block Clouds (id teletext-clouds): a night weather page with the text taken out.
// Cloud banks built from blocks on teletext's grid drift in from the sides. Pure string building.

// One grid for everything: 80 blocks across (teletext's 40 characters, 2 blocks each).
// Teletext's separated graphics leave a gap around every block; here it is kept to a hairline.
const BLOCK_WIDTH = 20
const BLOCK_HEIGHT = 16
const GAP = 0.5
const COLUMNS = 80
const ROWS = 63

/** Teletext's blue, cyan, magenta and yellow at reduced value, so nothing shouts behind text. */
const INK = {
  belly: '#1a2788',
  body: '#2636b4',
  bodyLight: '#2c3fc6',
  bodyHigh: '#3346dc',
  top: '#4cc4d8',
  topLit: '#9af0f8',
  rose: '#a84e80',
  deck: '#182568',
  land: '#111a4c',
  landTop: '#27367e',
  sun: '#f0cf52',
  sunShade: '#d2b040',
  star: '#cfd8ff',
}

type InkName = keyof typeof INK

type Block = { column: number; row: number }

type Hump = { x: number; y: number; rx: number; ry: number }

type Layer = readonly [InkName, Block[]]

type DriftingBank = { keyframes: string; svg: string }

/** The one bank shape, measured back from its inner tip; every bank is this shape scaled and placed. */
const HUMPS: readonly Hump[] = [
  { x: -430, y: -22, rx: 430, ry: 40 },
  { x: -350, y: -68, rx: 96, ry: 60 },
  { x: -236, y: -42, rx: 60, ry: 36 },
  { x: -150, y: -54, rx: 72, ry: 50 },
  { x: -86, y: -36, rx: 40, ry: 34 },
  { x: -24, y: -10, rx: 30, ry: 12 },
]

const STAR_PERIODS: readonly number[] = [7, 11, 13, 17, 19]

/** A deterministic stand-in for a random number in 0..1, so every build is the same. */
function hash(x: number, y: number, seed: number): number {
  let value = (x * 374761393 + y * 668265263 + seed * 2147483647) | 0
  value = Math.imul(value ^ (value >>> 13), 1274126177)
  value = value ^ (value >>> 16)
  return (value >>> 0) / 4294967296
}

function keyOf(column: number, row: number): string {
  return `${column},${row}`
}

function blockOfKey(key: string): Block {
  const parts = key.split(',')
  return { column: Number(parts[0] ?? 0), row: Number(parts[1] ?? 0) }
}

function listOf(blocks: ReadonlySet<string>): Block[] {
  return [...blocks].map(blockOfKey)
}

function blockPath(list: readonly Block[]): string {
  const width = BLOCK_WIDTH - GAP
  const height = BLOCK_HEIGHT - GAP
  return list.map(block => `M${block.column * BLOCK_WIDTH + 1} ${block.row * BLOCK_HEIGHT + 1}h${width}v${height}h-${width}z`).join('')
}

/** One path per ink, in the order given, so later inks paint over earlier ones. */
function paths(layers: readonly Layer[]): string {
  let out = ''
  for (const [ink, list] of layers) {
    if (list.length > 0) out += `<path d="${blockPath(list)}" fill="${INK[ink]}"/>`
  }
  return out
}

function insideSomeHump(x: number, y: number, tipX: number, baseY: number, scale: number, direction: number): boolean {
  for (const hump of HUMPS) {
    const dx = (x - (tipX + hump.x * scale * direction)) / (hump.rx * scale)
    const dy = (y - (baseY + hump.y * scale)) / (hump.ry * scale)
    if (dx * dx + dy * dy <= 1) return true
  }
  return false
}

/**
 * A cloud bank: a union of ellipses (humps) sampled at block centres and cut at its base row.
 * The underside is lumpy (some characters lose their lowest row) and rounded at its ends
 * (the last row is drawn in two blocks from every end of the row above it, the row before by one).
 */
function bankBlocks(tipX: number, baseRow: number, scale: number, direction: number): Set<string> {
  const baseY = baseRow * BLOCK_HEIGHT
  const blocks = new Set<string>()
  for (let row = 0; row < baseRow; row += 1) {
    for (let column = -34; column < COLUMNS + 34; column += 1) {
      if (row === baseRow - 1 && hash(Math.floor(column / 2), 1, baseRow) < 0.35) continue
      const x = column * BLOCK_WIDTH + BLOCK_WIDTH / 2
      const y = row * BLOCK_HEIGHT + BLOCK_HEIGHT / 2
      if (insideSomeHump(x, y, tipX, baseY, scale, direction)) blocks.add(keyOf(column, row))
    }
  }
  for (const block of listOf(blocks)) {
    const inset = block.row === baseRow - 1 ? 2 : block.row === baseRow - 2 ? 1 : 0
    if (inset === 0) continue
    if (!blocks.has(keyOf(block.column - inset, block.row - inset)) || !blocks.has(keyOf(block.column + inset, block.row - inset))) blocks.delete(keyOf(block.column, block.row))
  }
  return blocks
}

/**
 * Shades a cloud into a form: a lit top edge one block deep along the whole top, three body tones, and a darker belly row.
 * Slow things keep it alive without moving it: a brighter light travels along the top edge, and a few blocks
 * on the top edge come and go so the outline reshapes. The big right bank's belly row is rose, lit from below by the dusk.
 */
function cloud(blocks: ReadonlySet<string>, seed: number, warm: boolean): string {
  const belly: Block[] = []
  const rose: Block[] = []
  const body: Block[] = []
  const bodyLight: Block[] = []
  const bodyHigh: Block[] = []
  const top: Block[] = []
  const travelling: Block[][] = [[], [], [], [], []]
  let puffs = ''
  for (const block of listOf(blocks)) {
    const isTop = !blocks.has(keyOf(block.column, block.row - 1))
    const isBelly = !blocks.has(keyOf(block.column, block.row + 1))
    const chance = hash(Math.floor(block.column / 2), Math.floor(block.row / 3), seed)
    if (isTop) {
      top.push(block)
      travelling[Math.floor(block.column / 3 + 400) % 5]?.push(block)
      if (hash(block.column, block.row, seed + 1) < 0.08) {
        const above = [{ column: block.column, row: block.row - 1 }]
        puffs += `<g class="puff" style="animation-duration:${16 + (block.column % 5) * 3}s;animation-delay:-${(block.column * 7) % 23}s"><path d="${blockPath([block])}" fill="${INK.body}"/><path d="${blockPath(above)}" fill="${INK.top}"/></g>`
      }
    } else if (isBelly) (warm ? rose : belly).push(block)
    else if (!blocks.has(keyOf(block.column, block.row - 2))) bodyHigh.push(block)
    else if (!blocks.has(keyOf(block.column, block.row - 4)) || chance < 0.15) bodyLight.push(block)
    else body.push(block)
  }
  const light = travelling
    .map((list, group) => (list.length === 0 ? '' : `<path class="travel" style="animation-delay:-${(group * 1.4 + (seed % 5)).toFixed(1)}s" d="${blockPath(list)}" fill="${INK.topLit}"/>`))
    .join('')
  return paths([['belly', belly], ['rose', rose], ['body', body], ['bodyLight', bodyLight], ['bodyHigh', bodyHigh], ['top', top]]) + puffs + light
}

/** A bank slides a whole block at a time between two ends and back; at rest it sits midway. */
function drifting(name: string, blocksEachWay: number, secondsPerBlock: number, delay: number, inner: string): DriftingBank {
  const reach = blocksEachWay * BLOCK_WIDTH
  const steps = blocksEachWay * 2
  return {
    keyframes: `@keyframes ${name}{from{transform:translateX(-${reach}px)}to{transform:translateX(${reach}px)}}`,
    svg: `<g style="animation:${name} ${steps * secondsPerBlock}s steps(${steps}) -${delay}s infinite alternate">${inner}</g>`,
  }
}

/**
 * Stars are quarter blocks on the grid in the outer quarters of the upper sky; a few are yellow, and those under the sidebar are dim.
 * Each twinkles on its own prime period and phase, dimming to about half and back.
 */
function stars(): string {
  let out = ''
  for (let index = 0; index < 26; index += 1) {
    const column = Math.floor(hash(index, 2, 71) * 17) + (index % 2 === 0 ? 1 : 62)
    const row = Math.floor(hash(index, 3, 71) * 26)
    const x = column * BLOCK_WIDTH
    const y = row * BLOCK_HEIGHT
    const shape = `M${x + 5} ${y + 4}h10v8h-10z`
    const fill = index % 5 === 2 ? INK.sun : INK.star
    out += `<path class="star" style="animation-duration:${STAR_PERIODS[index % 5] ?? 7}s;animation-delay:-${(hash(index, 5, 71) * 19).toFixed(1)}s" d="${shape}" fill="${fill}" opacity="${(index % 2 === 0 ? 0.3 : 0.5 + hash(index, 4, 71) * 0.4).toFixed(2)}"/>`
  }
  return out
}

/** Land in the bottom left corner only, in broad steps; nothing under the conversation or the prompt box. */
function land(heights: readonly number[], firstColumn: number): string {
  const body: Block[] = []
  const top: Block[] = []
  heights.forEach((height, index) => {
    for (let dx = 0; dx < 4; dx += 1) {
      for (let row = ROWS - height; row < ROWS; row += 1) (row === ROWS - height ? top : body).push({ column: firstColumn + index * 4 + dx, row })
    }
  })
  return paths([['land', body], ['landTop', top]])
}

/**
 * The sun band of a weather page, turned into a night light: a small disc of solid yellow blocks beside the cards,
 * with a bite of sky taken out of its upper left so it is a moon.
 */
function disc(): string {
  const bright: Block[] = []
  const shade: Block[] = []
  for (let row = 8; row < 32; row += 1) {
    for (let column = 56; column < COLUMNS; column += 1) {
      const dx = column * BLOCK_WIDTH + BLOCK_WIDTH / 2 - 1350
      const dy = row * BLOCK_HEIGHT + BLOCK_HEIGHT / 2 - 312
      const distance = Math.sqrt(dx * dx + dy * dy)
      const bitten = Math.sqrt((dx + 44) * (dx + 44) + (dy + 34) * (dy + 34)) <= 56
      if (distance <= 60 && !bitten) (dy > 30 ? shade : bright).push({ column, row })
    }
  }
  return paths([['sun', bright], ['sunShade', shade]])
}

export function teletextCloudsSvg(): string {
  // Two banks only: the big one low on the right, and a smaller echo low on the left. They breathe in and out in turn:
  // one block every 8 s, fourteen blocks from end to end, so two minutes apart the picture is plainly different.
  const banks = [
    drifting('driftA', 7, 8, 112, cloud(bankBlocks(300, 44, 1.25, 1), 5, false)),
    drifting('driftB', 7, 8, 112, cloud(bankBlocks(1340, 56, 1.9, -1), 11, true)),
  ]

  // One far deck runs the whole width low in the window, a few percent lighter than the sky, so the middle is a place and not a void.
  const deckBlocks = new Set([...bankBlocks(1500, 47, 1.6, 1), ...bankBlocks(100, 47, 1.6, -1)])
  const deck = `<g style="animation:driftDeck 360s steps(24) -90s infinite alternate"><path d="${blockPath(listOf(deckBlocks))}" fill="${INK.deck}"/></g>`

  const style = `
.travel{opacity:0;animation:travel 7s ease-in-out infinite}
.puff{animation:puff 16s steps(1) infinite}
.star{animation:star 9s steps(2) infinite}
@keyframes travel{0%,30%,100%{opacity:0}12%{opacity:1}}
@keyframes puff{0%,55%{opacity:1}56%,100%{opacity:0}}
@keyframes star{0%,100%{opacity:1}50%{opacity:.5}}
${banks.map(each => each.keyframes).join('\n')}
@keyframes driftDeck{from{transform:translateX(-240px)}to{transform:translateX(240px)}}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  // The banks dissolve while they move in under the conversation: a fixed mask fades them out between the panels and the text.
  const defs = `<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1238"/><stop offset="0.6" stop-color="#14225c"/><stop offset="1" stop-color="#1b2b6e"/></linearGradient>
<linearGradient id="edges" x1="0" y1="0" x2="1" y2="0"><stop offset="0.16" stop-color="#fff"/><stop offset="0.255" stop-color="#fff" stop-opacity="0"/><stop offset="0.76" stop-color="#fff" stop-opacity="0"/><stop offset="0.83" stop-color="#fff"/></linearGradient>
<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1000"><rect width="1600" height="1000" fill="url(#edges)"/></mask>`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
<rect width="1600" height="1000" fill="url(#sky)"/>
${stars()}
${disc()}
${deck}
<g mask="url(#fade)">${banks.map(each => each.svg).join('\n')}</g>
${land([9, 8, 6, 5, 3, 2], -4)}
</svg>`
}
