// Halftone Dawn and Halftone Dusk: one two-ink risograph sunrise printed on two stocks. Every mark is a round dot on one tilted screen; dot size is the only drawing tool.
// Pure string building: no DOM, no imports. Two exports: halftoneDawnSvg (cream stock, light windows) and halftoneDuskSvg (night-blue stock, dark windows).

interface Wave {
  seconds: number
  length: number
  rest: number
  peak: number
  sharp: number
  name: string
}

interface Stock {
  paperTop: string
  paperFoot: string
  coral: string
  coralOpacity: number
  blue: string
  blueOpacity: number
  blend: string
}

interface DotGroup {
  band: number
  width: number
  d: string
}

const WIDTH = 1600
const HEIGHT = 1000
const PITCH = 11
const SCREEN_DEGREES = 15
const SUN = { x: 1408, y: 786, radius: 220 }
// Each wave is a pulse, not a sine: dots rest at `rest` and swell (or thin) to `peak` while a narrow crest passes, so each ring stays a ring.
const SUN_WAVE: Wave = { seconds: 24, length: 132, rest: 0.8, peak: 1.32, sharp: 1.4, name: 'breathe' }
const HILL_WAVE: Wave = { seconds: 40, length: 560, rest: 1.03, peak: 0.7, sharp: 1.5, name: 'mist' }
const BAND = 12
// Inks multiply on cream like real overprint; on the dark stock multiply would vanish, so they sit on top.
const DAWN_STOCK: Stock = { paperTop: '#f6ecdc', paperFoot: '#f2dcc6', coral: '#d45c3d', coralOpacity: 1, blue: '#6283b6', blueOpacity: 1, blend: 'multiply' }
const DUSK_STOCK: Stock = { paperTop: '#1b1f30', paperFoot: '#272a3f', coral: '#d9603a', coralOpacity: 0.86, blue: '#7f90ba', blueOpacity: 0.7, blend: 'normal' }

function smooth(from: number, to: number, value: number): number {
  const t = Math.min(1, Math.max(0, (value - from) / (to - from)))
  return t * t * (3 - 2 * t)
}

/** A single rounded hill: a bell of the given height and half-width. */
function bell(x: number, peakX: number, halfWidth: number, height: number): number {
  const t = (x - peakX) / halfWidth
  return height * Math.exp(-t * t)
}

/** 0 under the reading column, 1 at the side panels. */
function awayFromColumn(x: number): number {
  return Math.max(1 - smooth(300, 520, x), smooth(1080, 1260, x))
}

/** Far crest: ONE range across the whole sheet. Tall under the sidebar, a low quiet line below the prompt box, rising again in front of the sun. */
function farCrest(x: number): number {
  return 968 - 34 * awayFromColumn(x) - bell(x, 150, 250, 205) - bell(x, 1600, 330, 135) - 13 * Math.sin(x / 150 + 1) - 5 * Math.sin(x / 53)
}

/** Near crest: darker foothills at the two sides only; under the column it is below the sheet. */
function nearCrest(x: number): number {
  return 1014 - bell(x, -50, 270, 190) - bell(x, 1340, 250, 100) - 7 * Math.sin(x / 90 + 2)
}

/** Blue tone: a pale far range and darker foothills, lighter towards their feet like hills in mist. Each crest is dithered: dots grow from nothing over 36 px. */
function hillTone(x: number, y: number): number {
  const near = 0.42 * smooth(0, 36, y - nearCrest(x)) - 0.12 * smooth(36, 150, y - nearCrest(x))
  const far = 0.21 * smooth(0, 36, y - farCrest(x)) - 0.06 * smooth(36, 160, y - farCrest(x))
  // The floor is loud only at its two ends: under the column the dots carry a third of the weight.
  return Math.max(near, far, 0) * (0.3 + 0.7 * awayFromColumn(x))
}

/**
 * Coral tone: one centre, one continuous falloff. A level body, a soft rim, then a short halo of small clean dots that ends
 * about 80 px beyond the rim. The hills hide it: it fades out over the same band in which their dots grow.
 */
function sunTone(x: number, y: number): number {
  const d = Math.hypot(x - SUN.x, y - SUN.y)
  const behindHills = 1 - smooth(2, 38, y - Math.min(farCrest(x), nearCrest(x)))
  const body = d < SUN.radius ? 0.37 * (1 - Math.pow(d / SUN.radius, 4)) : 0
  const glow = 0.06 * Math.pow(1 - smooth(0, 150, d - SUN.radius * 0.9), 1.3)
  return Math.max(body, glow) * behindHills
}

/** Ring number around the sun: the sun's wave travels outward through these. */
function sunBand(x: number, y: number): number {
  return Math.hypot(x - SUN.x, y - SUN.y) / BAND
}

/** The hills' own wave runs along the ground, away from the sun. */
function hillBand(x: number): number {
  return Math.abs(SUN.x - x) / BAND
}

/**
 * Dots of one ink, gathered by band (for the wave's delay) and by diameter (one stroke width per path).
 * Both inks share one tilted lattice; the second ink sits half a cell over, so where they meet the dots interleave instead of colliding.
 * Dots under 2.3 px are not drawn: at that size they look like dust, not print.
 */
function screen(toneAt: (x: number, y: number) => number, bandAt: (x: number, y: number) => number, wave: Wave, halfCell: boolean): string {
  const turn = (SCREEN_DEGREES * Math.PI) / 180
  const cos = Math.cos(turn)
  const sin = Math.sin(turn)
  const reach = Math.ceil(2000 / PITCH)
  const offset = halfCell ? 0.5 : 0
  const groups = new Map<string, DotGroup>()
  for (let i = -reach; i <= reach; i += 1) {
    for (let j = -reach; j <= reach; j += 1) {
      const x = 800 + ((i + offset) * cos - (j + offset) * sin) * PITCH
      const y = 500 + ((i + offset) * sin + (j + offset) * cos) * PITCH
      if (x < -6 || x > WIDTH + 6 || y < -6 || y > HEIGHT + 6) continue
      const diameter = 2 * PITCH * Math.sqrt(toneAt(x, y) / Math.PI)
      if (diameter < 2.3) continue
      const band = Math.floor(bandAt(x, y))
      const width = Math.round(diameter * 2) / 2
      const key = `${band}|${width}`
      const group = groups.get(key) ?? { band, width, d: '' }
      group.d += `M${x.toFixed(1)} ${y.toFixed(1)}h0`
      groups.set(key, group)
    }
  }
  let markup = ''
  for (const group of groups.values()) {
    const lag = (((group.band + 0.5) * BAND) / wave.length) % 1
    const delay = (lag * wave.seconds - wave.seconds).toFixed(2)
    markup += `<path style="--w:${group.width}px;animation-delay:${delay}s" d="${group.d}"/>`
  }
  return markup
}

/** Keyframes that walk the pulse in small steps: stroke width repaints a few times a second, never every frame. */
function waveKeyframes(wave: Wave): string {
  let frames = ''
  for (let step = 0; step <= 12; step += 1) {
    const pulse = Math.pow((1 + Math.cos((step / 12) * 2 * Math.PI)) / 2, wave.sharp)
    const scale = wave.rest + (wave.peak - wave.rest) * pulse
    frames += `${((step * 100) / 12).toFixed(2)}%{stroke-width:calc(var(--w)*${scale.toFixed(3)})}`
  }
  return `@keyframes ${wave.name}{${frames}}`
}

/** One sheet: the same two plates on the given stock. */
function sheetSvg(stock: Stock): string {
  const sun = screen(sunTone, sunBand, SUN_WAVE, false)
  const hills = screen(hillTone, hillBand, HILL_WAVE, true)
  const style = `
.ink{mix-blend-mode:${stock.blend}}
.ink path{fill:none;stroke-linecap:round;stroke-width:var(--w);animation:${SUN_WAVE.name} ${SUN_WAVE.seconds}s steps(4) infinite}
.blue path{animation-name:${HILL_WAVE.name};animation-duration:${HILL_WAVE.seconds}s}
${waveKeyframes(SUN_WAVE)}
${waveKeyframes(HILL_WAVE)}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>
<linearGradient id="paper" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${stock.paperTop}"/><stop offset="1" stop-color="${stock.paperFoot}"/></linearGradient></defs>
<rect width="${WIDTH}" height="${HEIGHT}" fill="url(#paper)"/>
<g class="ink" stroke="${stock.coral}" stroke-opacity="${stock.coralOpacity}">${sun}</g>
<g class="ink blue" stroke="${stock.blue}" stroke-opacity="${stock.blueOpacity}">${hills}</g>
</svg>`
}

/** Halftone Dawn: the cream sheet, for light windows. */
export function halftoneDawnSvg(): string {
  return sheetSvg(DAWN_STOCK)
}

/** Halftone Dusk: the same plates on night-blue stock with an ember sun, for dark windows. */
export function halftoneDuskSvg(): string {
  return sheetSvg(DUSK_STOCK)
}
