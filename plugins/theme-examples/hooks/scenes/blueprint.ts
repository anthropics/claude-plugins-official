// Blueprint: a cyanotype sheet with one drawing on it that is alive.
// One subject, lower right: a comet's orbit plotted about a sun, inside an open graduated arc. The comet goes round it,
// quick near the sun and slow at the far end (Kepler's timing), its tail pointing away from the sun, a short trail of ink behind it on the orbit,
// a faint radius joining the two and an index tick riding the arc where that radius points.
// The reading column keeps only a ghost of the grid. A dark-window scene.

const SUN_X = 1440
const SUN_Y = 830
const CHALK = '#cfe0f5'
const GOLD = '#f2c14e'
const NEAREST = 66
const FARTHEST = 300
const COMET_PERIOD_SECONDS = 180
const TRAIL_LONGEST = 0.18

/** Pools of deeper wash, kept to the four corners: centre x, centre y, radius x, radius y. */
const DEEP_POOLS: readonly (readonly [number, number, number, number])[] = [
  [-40, -40, 720, 520],
  [1660, -60, 640, 460],
  [1700, 1080, 600, 480],
  [-80, 1080, 560, 420],
]

function round(value: number): number {
  return Math.round(value * 10) / 10
}

/** Deterministic stand-in for a random number, so every build is the same. */
function hash(seed: number): number {
  const value = Math.sin(seed * 127.1 + 311.7) * 43758.5453
  return value - Math.floor(value)
}

/** Degrees grow clockwise on screen, the same way CSS rotate() turns. */
function pointAt(centerX: number, centerY: number, radius: number, degrees: number): [number, number] {
  const angle = (degrees * Math.PI) / 180
  return [round(centerX + radius * Math.cos(angle)), round(centerY + radius * Math.sin(angle))]
}

function point(centerX: number, centerY: number, radius: number, degrees: number): string {
  return pointAt(centerX, centerY, radius, degrees).join(' ')
}

function arc(centerX: number, centerY: number, radius: number, from: number, to: number): string {
  const sweep = to > from ? 1 : 0
  return `M${point(centerX, centerY, radius, from)}A${radius} ${radius} 0 0 ${sweep} ${point(centerX, centerY, radius, to)}`
}

function circle(centerX: number, centerY: number, radius: number): string {
  return `M${centerX - radius} ${centerY}a${radius} ${radius} 0 1 0 ${radius * 2} 0a${radius} ${radius} 0 1 0 ${-radius * 2} 0`
}

/** Radial tick marks over a span of the circle; every `longEvery`-th tick starts further in. */
function radialTicks(
  centerX: number,
  centerY: number,
  inner: number,
  longInner: number,
  outer: number,
  step: number,
  longEvery: number,
  from: number,
  to: number,
): string {
  let path = ''
  for (let degrees = from; degrees <= to; degrees += step) {
    const start = (degrees / step) % longEvery === 0 ? longInner : inner
    path += `M${point(centerX, centerY, start, degrees)}L${point(centerX, centerY, outer, degrees)}`
  }
  return path
}

/**
 * A point of the comet's ellipse, unrounded. The sun is one focus; the far end points up and to the left, into the sheet.
 * `turn` is degrees round the ellipse's own centre from the far end, clockwise on screen; `stretch` scales about that centre (1 is the orbit itself).
 * All of the ellipse lies inside a 1200x800 window's crop.
 */
function cometPoint(turn: number, stretch: number): [number, number] {
  const semiMajor = (NEAREST + FARTHEST) / 2
  const focusOffset = semiMajor - NEAREST
  const semiMinor = Math.sqrt(semiMajor * semiMajor - focusOffset * focusOffset)
  const alongX = Math.cos((225 * Math.PI) / 180)
  const alongY = Math.sin((225 * Math.PI) / 180)
  const acrossX = Math.cos((315 * Math.PI) / 180)
  const acrossY = Math.sin((315 * Math.PI) / 180)
  const angle = (turn * Math.PI) / 180
  const alongDistance = focusOffset + semiMajor * Math.cos(angle) * stretch
  const acrossDistance = semiMinor * Math.sin(angle) * stretch
  return [SUN_X + alongDistance * alongX + acrossDistance * acrossX, SUN_Y + alongDistance * alongY + acrossDistance * acrossY]
}

function cometEllipse(): string {
  let path = ''
  for (let turn = 0; turn < 360; turn += 4) {
    const [x, y] = cometPoint(turn, 1)
    path += `${path === '' ? 'M' : 'L'}${round(x)} ${round(y)}`
  }
  return `${path}z`
}

/** Where the comet is after a share (0..1) of its period, counted from its closest pass: Kepler's equation, solved by Newton's steps. Returns the turn in degrees. */
function turnAtTime(share: number): number {
  const semiMajor = (NEAREST + FARTHEST) / 2
  const eccentricity = (semiMajor - NEAREST) / semiMajor
  const meanAnomaly = 2 * Math.PI * share
  let eccentricAnomaly = meanAnomaly
  for (let step = 0; step < 10; step += 1) {
    eccentricAnomaly -= (eccentricAnomaly - eccentricity * Math.sin(eccentricAnomaly) - meanAnomaly) / (1 - eccentricity * Math.cos(eccentricAnomaly))
  }
  return (eccentricAnomaly * 180) / Math.PI + 180
}

/** Equal-time marks along the plotted orbit: they bunch up at the far end, where the comet is slow. */
function equalTimeMarks(count: number): string {
  let path = ''
  for (let index = 0; index < count; index += 1) {
    const turn = turnAtTime(index / count)
    const [innerX, innerY] = cometPoint(turn, 0.965)
    const [outerX, outerY] = cometPoint(turn, 1.035)
    path += `M${round(innerX)} ${round(innerY)}L${round(outerX)} ${round(outerY)}`
  }
  return path
}

/** How far round the orbit each whole degree of turn is, given in shares (0..1) of its length, counted from the closest pass in the comet's direction. */
function ellipseSharesFromNearest(): number[] {
  const lengths: number[] = [0]
  let [lastX, lastY] = cometPoint(180, 1)
  for (let step = 1; step <= 360; step += 1) {
    const [x, y] = cometPoint(180 + step, 1)
    lengths.push((lengths[step - 1] ?? 0) + Math.hypot(x - lastX, y - lastY))
    lastX = x
    lastY = y
  }
  const whole = lengths[360] ?? 1
  return lengths.map(length => length / whole)
}

function shareAtTurn(shares: readonly number[], turn: number): number {
  const steps = turn - 180
  const whole = Math.min(359, Math.floor(steps))
  const before = shares[whole] ?? 0
  const after = shares[whole + 1] ?? 1
  return before + (after - before) * (steps - whole)
}

/** Two laps of the orbit from the closest pass, in the comet's direction, for the trail to slide along. */
function twoLapOrbit(): string {
  let path = ''
  for (let turn = 180; turn <= 900; turn += 4) {
    const [x, y] = cometPoint(turn, 1)
    path += `${path === '' ? 'M' : 'L'}${round(x)} ${round(y)}`
  }
  return path
}

/**
 * The comet's motion, written out in keyframes at equal steps of time. Each pose turns a frame about the sun to face the comet;
 * `cometRun` then slides out to the comet's distance (and grows the head and tail a little near the sun), `radiusRun` stretches a unit line out to it,
 * `bearingRun` only turns, `trailRun` slides the trail's dash. Enough poses that straight-line blending between them stays on the ellipse.
 */
function cometKeyframes(count: number): string {
  let run = ''
  let radius = ''
  let bearing = ''
  let trail = ''
  let previous = 0
  const lapShares = ellipseSharesFromNearest()
  for (let index = 0; index <= count; index += 1) {
    const [x, y] = cometPoint(turnAtTime(index / count), 1)
    const distance = Math.hypot(x - SUN_X, y - SUN_Y)
    let degrees = (Math.atan2(y - SUN_Y, x - SUN_X) * 180) / Math.PI
    while (degrees < previous - 180) degrees += 360
    while (degrees > previous + 180) degrees -= 360
    previous = degrees
    const percent = round((index / count) * 100)
    const size = (0.72 + 58 / distance).toFixed(2)
    run += `${percent}%{transform:rotate(${round(degrees)}deg) translateX(${round(distance)}px) scale(${size})}`
    radius += `${percent}%{transform:rotate(${round(degrees)}deg) scaleX(${round(distance)})}`
    bearing += `${percent}%{transform:rotate(${round(degrees)}deg)}`
    // The trail is a dash on a two-lap copy of the orbit: its leading end sits `1 + share` laps along, so it never meets the path's start or end.
    const share = index === count ? 1 : shareAtTurn(lapShares, turnAtTime(index / count))
    trail += `${percent}%{stroke-dashoffset:${(TRAIL_LONGEST - 1 - share).toFixed(4)}}`
  }
  return `@keyframes cometRun{${run}}@keyframes radiusRun{${radius}}@keyframes bearingRun{${bearing}}@keyframes trailRun{${trail}}`
}

/** A body on a circular orbit about the sun: a solid disc going round anticlockwise, once per `period` seconds, from `startDegrees`. */
function orbitingBody(orbitRadius: number, bodyRadius: number, period: number, startDegrees: number): string {
  const delay = round(-((360 - startDegrees) / 360) * period)
  return `<g class="orbit" style="animation-duration:${period}s;animation-delay:${delay}s"><circle cx="${SUN_X + orbitRadius}" cy="${SUN_Y}" r="${bodyRadius}" fill="#dce8f7"/></g>`
}

/** The coating: one even Prussian blue where the text sits; the pools of deeper wash keep to the four corners. A little paper tooth. */
function paper(): string {
  const wash = DEEP_POOLS.map(pool => `<ellipse cx="${pool[0]}" cy="${pool[1]}" rx="${pool[2]}" ry="${pool[3]}" fill="url(#washDeep)"/>`).join('')
  const grid = `<rect width="1600" height="1000" fill="url(#minorGrid)" mask="url(#notInColumn)"/><rect width="1600" height="1000" fill="url(#oddMajorGrid)" mask="url(#notInColumn)"/><rect width="1600" height="1000" fill="url(#evenMajorGrid)" mask="url(#fainterInColumn)"/>`
  return `<rect width="1600" height="1000" fill="#22508e"/>${wash}<rect width="1600" height="1000" fill="url(#tooth)"/>${grid}`
}

/** Specks of paper tooth for one 160-unit tile: they also keep the washes from banding under the app's blur. */
function toothSpecks(): string {
  let specks = ''
  for (let index = 0; index < 46; index += 1) {
    const x = round(hash(index + 3) * 160)
    const y = round(hash(index + 71) * 160)
    const light = hash(index + 131) > 0.45
    specks += `<rect x="${x}" y="${y}" width="${light ? 1.2 : 1.6}" height="1.2" fill="${light ? '#dce8f7' : '#0b2347'}" opacity="${light ? 0.07 : 0.1}"/>`
  }
  return specks
}

/** The fixed drawing: an open graduated arc whose ends fade out, one inner orbit with one planet, short axes, the comet's orbit plotted in pale chalk with its equal-time marks. */
function plottedDrawing(): string {
  const x = SUN_X
  const y = SUN_Y
  const scale = `${arc(x, y, 318, 160, 290)}${arc(x, y, 330, 160, 290)}${radialTicks(x, y, 322, 313, 330, 5, 3, 160, 290)}`
  const axes = `M${x - 346} ${y}H${x + 96}M${x} ${y - 346}V${y + 96}`
  const sun = `<circle cx="${x}" cy="${y}" r="11" fill="none" stroke="${CHALK}" stroke-width="1.5" opacity=".7"/><circle cx="${x}" cy="${y}" r="4" fill="#dce8f7" opacity=".9"/>`
  const planet = `<g opacity=".85">${orbitingBody(66, 4.5, 120, 250)}</g>`
  const orbit = `<path fill="none" stroke="${CHALK}" stroke-width="1.4" opacity=".5" d="${cometEllipse()}"/><path class="fine" d="${equalTimeMarks(12)}"/>`
  return `<path class="fine chain" d="${axes}"/><path class="medium" d="${circle(x, y, 66)}"/><path fill="none" stroke="url(#scaleFade)" stroke-width="1.4" opacity=".46" d="${scale}"/>${orbit}${sun}${planet}`
}

/** One layer of the trail: a dash `share` of a lap long whose leading end rides with the comet. Three of them stacked make the trail fade toward its far end. */
function trailLayer(share: number, width: number, opacity: number, timing: string, restShare: number, orbitTwice: string): string {
  return `<path class="trailRun" pathLength="2" style="${timing};stroke-dasharray:0 ${(TRAIL_LONGEST - share).toFixed(2)} ${share} 3;stroke-dashoffset:${(TRAIL_LONGEST - 1 - restShare).toFixed(3)}" d="${orbitTwice}" fill="none" stroke="${GOLD}" stroke-width="${width}" opacity="${opacity}"/>`
}

/** The comet: a small bright head, a tapering tail that always points away from the sun, and a faint radius from the sun to the head. A short trail of ink lies behind it on the orbit and an index tick rides the arc at its bearing. Never a line that fills up. */
function comet(): string {
  // A third of the way round at the first frame, well out on the sheet. Without animation it rests near the far end.
  const timing = `animation-duration:${COMET_PERIOD_SECONDS}s;animation-delay:-${Math.round(COMET_PERIOD_SECONDS * 0.36)}s`
  const [restX, restY] = cometPoint(turnAtTime(0.42), 1)
  const restDistance = round(Math.hypot(restX - SUN_X, restY - SUN_Y))
  const restDegrees = round((Math.atan2(restY - SUN_Y, restX - SUN_X) * 180) / Math.PI)
  const radius = `<path class="radiusRun" style="${timing};transform:rotate(${restDegrees}deg) scaleX(${restDistance})" d="M${SUN_X} ${SUN_Y}h1" fill="none" stroke="${CHALK}" stroke-width="1" opacity=".16"/>`
  const body = `<g class="cometRun" style="${timing};transform:rotate(${restDegrees}deg) translateX(${restDistance}px)"><path d="M${SUN_X + 2} ${SUN_Y - 3.4}L${SUN_X + 58} ${SUN_Y}L${SUN_X + 2} ${SUN_Y + 3.4}z" fill="url(#tailFade)"/><circle cx="${SUN_X}" cy="${SUN_Y}" r="5" fill="#ffe08a"/></g>`
  const orbitTwice = twoLapOrbit()
  const restShare = shareAtTurn(ellipseSharesFromNearest(), turnAtTime(0.42))
  const trail = `${trailLayer(0.18, 1.6, 0.2, timing, restShare, orbitTwice)}${trailLayer(0.11, 2, 0.25, timing, restShare, orbitTwice)}${trailLayer(0.05, 2.6, 0.35, timing, restShare, orbitTwice)}`
  const index = `<path class="bearingRun" style="${timing};transform:rotate(${restDegrees}deg)" d="M${SUN_X + 311} ${SUN_Y}h16" fill="none" stroke="${GOLD}" stroke-width="2" opacity=".75"/>`
  return `${trail}${radius}${index}${body}`
}

/** Stops of a left-to-right ramp that is full at the sheet's margins and `inside` strong behind the reading column, eased over 352 units a side so no seam shows. */
function columnRamp(inside: number): string {
  return `<stop offset="0" stop-color="#fff"/><stop offset=".1" stop-color="#fff"/><stop offset=".32" stop-color="#fff" stop-opacity="${inside}"/><stop offset=".7" stop-color="#fff" stop-opacity="${inside}"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff"/>`
}

export function blueprintSvg(): string {
  const style = `
.medium{fill:none;stroke:${CHALK};stroke-width:1.1;opacity:.26}
.fine{fill:none;stroke:${CHALK};stroke-width:.8;opacity:.2}
.chain{stroke-dasharray:26 5 4 5}
.orbit,.cometRun,.radiusRun,.bearingRun{transform-origin:${SUN_X}px ${SUN_Y}px}
.orbit{animation:orbit 600s linear infinite}
.cometRun{animation:cometRun ${COMET_PERIOD_SECONDS}s linear infinite}
.radiusRun{animation:radiusRun ${COMET_PERIOD_SECONDS}s linear infinite}
.bearingRun{animation:bearingRun ${COMET_PERIOD_SECONDS}s linear infinite}
.trailRun{animation:trailRun ${COMET_PERIOD_SECONDS}s linear infinite}
@keyframes orbit{to{transform:rotate(-360deg)}}
${cometKeyframes(120)}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}`

  const [fadeFromX, fadeFromY] = pointAt(SUN_X, SUN_Y, 324, 160)
  const [fadeToX, fadeToY] = pointAt(SUN_X, SUN_Y, 324, 290)
  const defs = `
<radialGradient id="washDeep"><stop offset="0" stop-color="#0e2c58" stop-opacity=".78"/><stop offset=".4" stop-color="#0e2c58" stop-opacity=".46"/><stop offset=".72" stop-color="#0e2c58" stop-opacity=".15"/><stop offset="1" stop-color="#0e2c58" stop-opacity="0"/></radialGradient>
<linearGradient id="scaleFade" gradientUnits="userSpaceOnUse" x1="${fadeFromX}" y1="${fadeFromY}" x2="${fadeToX}" y2="${fadeToY}"><stop offset="0" stop-color="${CHALK}" stop-opacity="0"/><stop offset=".16" stop-color="${CHALK}"/><stop offset=".84" stop-color="${CHALK}"/><stop offset="1" stop-color="${CHALK}" stop-opacity="0"/></linearGradient>
<linearGradient id="tailFade"><stop offset="0" stop-color="${GOLD}" stop-opacity=".95"/><stop offset=".5" stop-color="${GOLD}" stop-opacity=".45"/><stop offset="1" stop-color="${GOLD}" stop-opacity="0"/></linearGradient>
<pattern id="tooth" width="160" height="160" patternUnits="userSpaceOnUse">${toothSpecks()}</pattern>
<pattern id="minorGrid" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M20.5 0v100M40.5 0v100M60.5 0v100M80.5 0v100M0 20.5h100M0 40.5h100M0 60.5h100M0 80.5h100" stroke="${CHALK}" stroke-opacity=".07" fill="none"/></pattern>
<pattern id="oddMajorGrid" width="200" height="200" patternUnits="userSpaceOnUse"><path d="M100.5 0v200M0 100.5h200" stroke="${CHALK}" stroke-opacity=".14" fill="none"/></pattern>
<pattern id="evenMajorGrid" width="200" height="200" patternUnits="userSpaceOnUse"><path d="M.5 0v200M0 .5h200" stroke="${CHALK}" stroke-opacity=".14" fill="none"/></pattern>
<linearGradient id="notInColumnRamp">${columnRamp(0)}</linearGradient>
<linearGradient id="fainterInColumnRamp">${columnRamp(0.35)}</linearGradient>
<mask id="notInColumn" maskUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1000"><rect width="1600" height="1000" fill="url(#notInColumnRamp)"/></mask>
<mask id="fainterInColumn" maskUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1000"><rect width="1600" height="1000" fill="url(#fainterInColumnRamp)"/></mask>`

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" preserveAspectRatio="xMidYMid slice" font-family="monospace" color="#888"><style>${style}</style><defs>${defs}</defs>
${paper()}
${plottedDrawing()}
${comet()}
</svg>`
}
