// Ripple Tank. A two-ink print of a pond's skin: a teal plate for the water and a coral plate for what lives on it.
// The water is a real wave field kept in a small buffer, so every pointer is a dipper and several make true interference.
// Three passes do most of the work. "cast" is a tiny table of where every creature is, worked out once a frame.
// "tank" is the wave field. "water" prints the field as halftone rings; the creatures are small shapes laid over it.
import {
  PI, abs, atan, buffer, clamp, cos, dot, dt, exp, floor, int, length, max, min, mix, normalize, picture, pointerCount,
  pointers, scene, shader, shapes, sin, size, smoothstep, sqrt, step, table, time, unsigned, vec2, vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

// A small integer mixer: two whole numbers in, 32 scrambled bits out
const blend = (a: int, b: int): int => {
  let h = int(a * 1830299339 + b * -1588511639)
  h = int(h ^ (h >>> 15))
  h = int(h * -2018788877)
  h = int(h ^ (h >>> 12))
  h = int(h * 458427541)
  return int(h ^ (h >>> 17))
}
const low = (h: int) => unsigned(int(h & 65535)) / 65536
const high = (h: int) => unsigned(int(h >>> 16)) / 65536

// The cast
// One row each. Striders: home x, home y (shares of the window), seconds between darts, seed.
// Leaves: home x, home y, seed, how fast it turns (radians a second). Rain: middle x, middle y, seconds between
// drops, seed. Whirligig beetles: home x, home y, seed, how fast it circles (radians a second, the sign its way round).
// Minnows: place in the shoal along and across, seed, size. Midges, in the air over the water: home x, home y, seed, size.
// Leaves and beetles have their homes in the gaps between the striders' homes, so they seldom sit on one another.
const STRIDERS = 8
const LEAVES = 3
const DROPS = 2
const BEETLES = 3
const MINNOWS = 9
const MIDGES = 5
const LEAF0 = STRIDERS
const DROP0 = LEAF0 + LEAVES
const BEETLE0 = DROP0 + DROPS
const MINNOW0 = BEETLE0 + BEETLES
const MIDGE0 = MINNOW0 + MINNOWS
const ROLL = table([
  [0.075, 0.83, 3.1, 0.13],
  [0.19, 0.61, 2.6, 0.71],
  [0.07, 0.4, 3.7, 0.37],
  [0.18, 0.16, 2.9, 0.55],
  [0.93, 0.86, 3.4, 0.91],
  [0.815, 0.65, 2.7, 0.29],
  [0.925, 0.4, 3.9, 0.63],
  [0.825, 0.15, 3.2, 0.47],
  [0.062, 0.615, 1.3, 0.03],
  [0.94, 0.63, 4.1, -0.024],
  [0.205, 0.385, 2.6, 0.037],
  [0.13, 0.52, 2.3, 0.2],
  [0.87, 0.5, 3.1, 0.6],
  [0.205, 0.85, 0.3, 2.1],
  [0.775, 0.39, 1.7, -2.4],
  [0.8, 0.87, 2.9, 1.9],
  [0.9, 0, 0.1, 1.1],
  [0.45, 0.7, 0.9, 0.9],
  [0.35, -0.8, 1.7, 1],
  [0, 0.15, 2.3, 1.2],
  [-0.2, -0.6, 3.1, 0.85],
  [-0.5, 0.75, 3.8, 1],
  [-0.7, -0.1, 4.6, 0.95],
  [-1, 0.5, 5.2, 0.8],
  [-1.1, -0.7, 6, 0.9],
  [0.25, 0.27, 0.4, 1.5],
  [0.1, 0.6, 1.9, 1.3],
  [0.74, 0.86, 3.3, 1.65],
  [0.9, 0.26, 4.7, 1.35],
  [0.77, 0.5, 5.9, 1.5],
])
// Sizes that the shapes need where they are placed.
const STRIDER_SIZE = [1.3, 1.1, 1.4, 1.2, 1.2, 1.35, 1.1, 1.3]
const LEAF_LONG = [50, 42, 33]
const LEAF_WIDE = [0.5, 0.58, 0.46]
const LEAF_BITE = [1, 0, 0]

const ROAM = 46
// In a narrow or a short window every creature is drawn a little smaller, so the margins do not crowd.
const zoomOf = () => clamp(min(size.x / 1200, size.y / 760), 0.62, 1)

// One turn of a wave: up, then down, over "span" seconds, then nothing.
const plop = (age: number, span: number) => sin(2 * PI * min(age / span, 1))

// How the water leans at a place. (The tank is declared further down.)
const leanAt = (uv: vec2) => {
  const tx = 1 / tank.size.x
  const ty = 1 / tank.size.y
  return vec2(
    tank.sample(vec2(uv.x + tx, uv.y)).r - tank.sample(vec2(uv.x - tx, uv.y)).r,
    tank.sample(vec2(uv.x, uv.y + ty)).r - tank.sample(vec2(uv.x, uv.y - ty)).r,
  )
}

// A creature gives way to the pointers: the push it would like, never large, and none when a pointer is right on it.
const giveWay = (at: vec2, wide: number, far: number) => {
  let shove = vec2(0, 0)
  for (const finger of pointers) {
    const away = vec2(at - finger.at)
    const hold = clamp(1 - finger.gone, 0, 1)
    shove = vec2(shove + away * (1.1 * exp(-dot(away, away) / (wide * wide)) * hold * hold))
  }
  return vec2(shove / (1 + length(shove) / far))
}

// Three texels a creature. Top row: where it is (x, y) and which way it faces (x, y). The rows under it: what else it
// remembers from frame to frame (how far a pointer has pushed it, how far the water has carried it).
const cast: Buffer = buffer({ size: [MIDGE0 + MIDGES, 3], float: 32, filter: 'nearest' }, (p): vec4 => {
  const who = p.cell.x
  const card = ROLL.at(who)
  const kept = cast.at(vec2(who, 1))
  const carried = cast.at(vec2(who, 2)).xy

  // A strider: rest, dart, glide, on a path that is a function of the clock
  const home = vec2(size.x * card.x, size.y * card.y)
  const g = time / card.z + card.w
  const n = floor(g)
  const f = g - n
  const stop = (k: number) => {
    const h = blend(int(k), int(card.w * 1000))
    const a = k * 1.9 + low(h) * 1.2 + card.w * 6
    const r = ROAM * zoomOf() * (0.45 + 0.55 * high(h))
    return vec2(home.x + cos(a) * r, home.y + sin(a) * r)
  }
  const a = stop(n)
  const b = stop(n + 1)
  const c = stop(n + 2)
  const left = 1 - min(f / 0.36, 1)
  const base = vec2(mix(a, b, 1 - left * left * left))
  const ahead = normalize(vec2(b - a))
  const facing = normalize(vec2(mix(ahead, normalize(vec2(c - b)), smoothstep(0.58, 0.96, f))))
  const stroke = smoothstep(0, 0.06, f) * (1 - smoothstep(0.08, 0.36, f))
  // It gives way to a pointer with a little inertia, and slides with the slope of the water under it.
  const striderShove = vec2(kept.zw + (giveWay(base, 110, 44) - kept.zw) * (1 - exp(-dt * 6)))
  const striderRide = vec2(carried + (clamp(leanAt(vec2(base / size)) * -70, -8, 8) - carried) * (1 - exp(-dt * 4)))
  const striderTop = vec4(base + striderShove + striderRide, facing)
  const striderBottom = vec4(stroke, f * card.z, striderShove)

  // A leaf: a slow drift and a slow turn; a pointer nudges it, the water rocks it
  const leafBase = vec2(home.x + 22 * sin(time * 0.05 + card.z), home.y + 30 * sin(time * 0.037 + card.z * 2))
  const leafShove = vec2(kept.zw + (giveWay(leafBase, 130, 56) - kept.zw) * (1 - exp(-dt * 1.6)))
  const leafLean = leanAt(vec2(leafBase / size))
  const leafRide = vec2(carried + (clamp(leafLean * -80, -9, 9) - carried) * (1 - exp(-dt * 2.5)))
  const leafTurn = card.z * 2 + card.w * time + 0.4 * sin(time * 0.11 + card.z) + clamp((leafRide.x - leafRide.y) * 0.02, -0.2, 0.2)
  const leafTop = vec4(leafBase + leafShove + leafRide, cos(leafTurn), sin(leafTurn))
  const leafBottom = vec4(0, 0, leafShove)

  // A raindrop source: it wanders the margin, one drop every few seconds
  const dg = time / card.z + card.w
  const dk = floor(dg)
  // Rain does not keep time: each drop falls a little late, by its own amount, and now and then one does not fall.
  const dh = blend(int(dk), int(card.w * 77))
  const fallen = high(dh) < 0.18 ? 99 : max((dg - dk) * card.z - low(dh) * 0.5 * card.z, 0)
  const dropTop = vec4(
    size.x * (card.x + 0.08 * sin(dk * 2.4 + card.w * 9)),
    size.y * (card.y + 0.34 * sin(dk * 1.7 + card.w * 5)),
    fallen,
    dk,
  )
  // A drop falls only if no pointer is there when it lands; once it has landed, it finishes.
  const landed = fallen < 0.07 ? (pointerCount > 0 ? 0 : 1) : kept.x

  // A whirligig beetle: round and round, faster when a pointer comes near
  const ring = vec2(home.x + 26 * sin(time * 0.04 + card.z), home.y + 34 * sin(time * 0.031 + card.z * 2))
  let alarm = 0
  for (const finger of pointers) {
    const away = vec2(ring - finger.at)
    alarm = max(alarm, exp(-dot(away, away) / 26000) * clamp(1 - finger.gone, 0, 1))
  }
  const calmer = kept.y + (alarm - kept.y) * (1 - exp(-dt * 3))
  const swing = kept.x + card.w * (1 + 2.5 * calmer) * dt
  const angle = swing - floor(swing / (2 * PI)) * 2 * PI
  const wide = 17 + 6 * sin(time * 0.6 + card.z * 3)
  const spin = card.w < 0 ? -1 : 1
  const beetleTop = vec4(ring.x + wide * cos(angle), ring.y + wide * sin(angle), -sin(angle) * spin, cos(angle) * spin)
  const beetleBottom = vec4(angle, calmer, 0, 0)

  // A minnow: a place in a shoal that cruises the whole tank, under the surface
  const cruise = vec2(time * 0.043 + 1, time * 0.071)
  const shoal = vec2(size.x * (0.5 + 0.41 * sin(cruise.x)), size.y * (0.5 + 0.34 * sin(cruise.y)))
  const heading = normalize(vec2(size.x * 0.41 * 0.043 * cos(cruise.x), size.y * 0.34 * 0.071 * cos(cruise.y) + 0.01))
  const across = vec2(-heading.y, heading.x)
  const place = vec2(
    shoal + heading * (card.x * 62 + 7 * sin(time * 0.7 + card.z)) + across * (card.y * 44 + 6 * sin(time * 0.53 + card.z * 2)),
  )
  const minnowShove = vec2(kept.zw + (giveWay(place, 150, 80) - kept.zw) * (1 - exp(-dt * 4)))
  const nose = normalize(vec2(heading + across * (0.25 * sin(time * 0.53 + card.z * 2)) + minnowShove * 0.02))
  const minnowTop = vec4(place + minnowShove, nose)
  const minnowBottom = vec4(card.z, card.w, minnowShove)

  // A midge: a slow looping glide in the air over one patch of water
  const s = card.z
  const patch = vec2(home.x + 34 * sin(time * 0.05 + s), home.y + 44 * sin(time * 0.037 + s * 2))
  const dance = vec2(14 * sin(time * 1.3 + s * 7) + 5 * sin(time * 2.9 + s * 3), 12 * cos(time * 1.1 + s * 5) + 5 * sin(time * 2.3 + s))
  const going = normalize(vec2(18 * cos(time * 1.3 + s * 7) + 14.5 * cos(time * 2.9 + s * 3) + 0.01, -13 * sin(time * 1.1 + s * 5) + 11.5 * cos(time * 2.3 + s)))
  const midgeShove = vec2(kept.zw + (giveWay(patch, 120, 70) - kept.zw) * (1 - exp(-dt * 8)))
  const midgeTop = vec4(patch + dance + midgeShove, going)
  const midgeBottom = vec4(card.w, 0, midgeShove)

  const top =
    who < LEAF0 ? striderTop : who < DROP0 ? leafTop : who < BEETLE0 ? dropTop : who < MINNOW0 ? beetleTop : who < MIDGE0 ? minnowTop : midgeTop
  const bottom =
    who < LEAF0
      ? striderBottom
      : who < DROP0
        ? leafBottom
        : who < BEETLE0
          ? vec4(landed, 0, 0, 0)
          : who < MINNOW0
            ? beetleBottom
            : who < MIDGE0
              ? minnowBottom
              : midgeBottom
  const third = who < LEAF0 ? striderRide : who < DROP0 ? leafRide : vec2(0, 0)
  return p.cell.y < 0.5 ? top : p.cell.y < 1.5 ? bottom : vec4(third, 0, 0)
})

// The tank: a wave field of one texel to every four points, two time levels
const tank: Buffer = buffer({ scale: 0.25, float: 16, filter: 'linear', repeat: 2 }, (p): vec4 => {
  const c = p.cell
  const me = tank.at(c).rg
  const plus = vec2(
    tank.at(vec2(c.x + 1, c.y)).rg + tank.at(vec2(c.x - 1, c.y)).rg + tank.at(vec2(c.x, c.y + 1)).rg + tank.at(vec2(c.x, c.y - 1)).rg,
  )
  const cross = vec2(
    tank.at(vec2(c.x + 1, c.y + 1)).rg + tank.at(vec2(c.x - 1, c.y + 1)).rg + tank.at(vec2(c.x + 1, c.y - 1)).rg + tank.at(vec2(c.x - 1, c.y - 1)).rg,
  )
  const bend = vec2((plus * 4 + cross - me * 20) / 6)
  // A beach round the rim soaks the waves up.
  const rim = min(min(p.uv.x, 1 - p.uv.x), min(p.uv.y, 1 - p.uv.y))
  const beach = 1 - smoothstep(0, 0.07, rim)
  // Two runs a frame; "pace" keeps the waves' speed the same when frames come slower than thirty a second.
  const pace = clamp(dt * 30, 0.6, 1.5)
  const push = pace * pace
  const drag = 0.0045 * pace + 0.2 * beach * beach
  let next = me.r + (1 - drag) * (me.r - me.g) + 0.15 * push * bend.r + 0.03 * (bend.r - bend.g)

  // Each pointer is a dipper: the water under it is held to a height that swings down and up. Holding to a height, not
  // adding to it, means nothing can pile up however hard a finger scrubs. The dipper is drawn from where the pointer was
  // to where it is, so a fast one leaves a line, not beads, and the faster it goes the lighter it presses.
  for (const finger of pointers) {
    const moved = length(vec2(finger.at - finger.was))
    // With no move to speak of, "aim" is nearly nothing and the stroke below is a single spot, as it should be.
    const aim = vec2((finger.at - finger.was) / max(moved, 0.01))
    const from = vec2(p.point - finger.was)
    const along = dot(from, aim)
    const beyond = max(max(-along, along - moved), 0)
    const away = max(dot(from, from) - along * along, 0) + beyond * beyond
    const light = 1 / (1 + moved * moved / 400)
    const hold = 1 - smoothstep(0, 0.35, finger.gone)
    const press = (0.35 + 0.65 * finger.down) * (1 - 0.6 * finger.over)
    const want = -0.55 * press * cos(2 * PI * 1.2 * finger.age)
    next += (want - next) * 0.5 * exp(-away / 200) * hold * light
  }

  // With nobody there, two raindrops wander the margins.
  for (let j = DROP0; j < BEETLE0; j++) {
    const drop = cast.at(vec2(j, 0))
    const off = vec2(p.point - drop.xy)
    next += cast.at(vec2(j, 1)).x * push * 0.036 * plop(drop.z, 0.62) * exp(-dot(off, off) / 220)
  }
  // Each strider's push-off drops a small ripple.
  for (let j = 0; j < STRIDERS; j++) {
    const off = vec2(p.point - cast.at(vec2(j, 0)).xy)
    next += push * 0.007 * plop(cast.at(vec2(j, 1)).y, 0.4) * exp(-dot(off, off) / 90)
  }
  // Each whirligig trails fine ripples.
  for (let j = BEETLE0; j < MINNOW0; j++) {
    const off = vec2(p.point - cast.at(vec2(j, 0)).xy)
    next += (0.05 * sin(time * 15 + j) - next) * 0.3 * exp(-dot(off, off) / 60)
  }
  return vec4(clamp(next, -2, 2), me.r, 0, 1)
})

// Printing
const LIGHT = {
  ground: vec3(214, 231, 224) / 255,
  ringTeal: vec3(170, 213, 203) / 255,
  ringCoral: vec3(243, 195, 182) / 255,
  teal: vec3(22, 131, 125) / 255,
  coral: vec3(238, 106, 85) / 255,
  over: vec3(91, 58, 68) / 255,
  shade: vec3(186, 215, 206) / 255,
  minnow: vec3(140, 196, 185) / 255,
}
const DARK = {
  ground: vec3(17, 46, 52) / 255,
  ringTeal: vec3(35, 100, 96) / 255,
  ringCoral: vec3(90, 50, 48) / 255,
  teal: vec3(82, 199, 184) / 255,
  coral: vec3(245, 132, 111) / 255,
  over: vec3(59, 36, 51) / 255,
  shade: vec3(9, 28, 33) / 255,
  minnow: vec3(42, 117, 111) / 255,
}
// The Svg under the shader is printed in the window's mode; one corner of it tells day from night.
const dayOf = () => step(0.5, dot(scene.sample(vec2(0.004, 0.004)).rgb, vec3(0.3, 0.6, 0.1)))

// 1 inside a shape whose edge is at "d" = 0, fading to 0 across the edge. "crisp" is one over the edge's full width.
const inside = (d: number, crisp: number) => clamp(0.5 - d * crisp, 0, 1)
// An edge about a pixel and a half wide, never finer than a point.
const crispOf = (px: number) => 1 / max(px * 1.4, 0.9)

// One halftone screen: dots on a turned grid, each as big as the tone under it asks.
const screenDots = (at: vec2, ca: number, sa: number, pitch: number, tone: number, crisp: number) => {
  const r = vec2((at.x * ca + at.y * sa) / pitch, (at.y * ca - at.x * sa) / pitch)
  const cell = floor(r)
  const off = vec2(r - cell - 0.5)
  const wobble = low(blend(int(cell.x), int(cell.y)))
  const radius = pitch * 0.31 * sqrt(tone) * (0.85 + 0.25 * wobble)
  const d = length(off) * pitch
  return inside(d - radius, crisp) * step(0.01, tone)
}

// How far "at" is from the stroke that runs from a to b. Measured in the stroke's own terms: how far along it the
// point lies, how far it overshoots either end, and how far to the side.
const toLine = (at: vec2, a: vec2, b: vec2) => {
  const reach = length(vec2(b - a))
  const aim = vec2((b - a) / reach)
  const from = vec2(at - a)
  const along = dot(from, aim)
  const beyond = max(max(-along, along - reach), 0)
  const aside = max(dot(from, from) - along * along, 0)
  return sqrt(aside + beyond * beyond)
}

// Paper tooth: the solid inks do not quite cover. Two numbers, one for each plate.
const toothAt = (at: vec2) => {
  const t = high(blend(int(at.x / 1.4), int(at.y / 1.4)))
  return vec2(1 - 0.4 * step(0.9, t), 1 - 0.4 * step(t, 0.1))
}

// The two plates, laid down as one premultiplied color.
const printed = (inkT: number, inkC: number, at: vec2) => {
  const day = dayOf()
  const tooth = toothAt(at)
  const t = inkT * tooth.x
  const c = inkC * tooth.y
  return vec4(
    mix(DARK.teal, LIGHT.teal, day) * t * (1 - c) + mix(DARK.coral, LIGHT.coral, day) * c * (1 - t) + mix(DARK.over, LIGHT.over, day) * t * c,
    1 - (1 - t) * (1 - c),
  )
}

const water = picture(p => {
  const crisp = crispOf(p.px)
  const day = dayOf()
  const ground = vec3(mix(DARK.ground, LIGHT.ground, day))
  const ringTeal = vec3(mix(DARK.ringTeal, LIGHT.ringTeal, day))
  const ringCoral = vec3(mix(DARK.ringCoral, LIGHT.ringCoral, day))

  // A ripple tank shows waves by how they bend light: a crest is a lens. So what prints is not the water's height but
  // how sharply it curves: its height here against the water a step away on four sides. Long slow swells curve too
  // gently to print at all; only true crests and troughs do.
  const ux = 12 / size.x
  const uy = 12 / size.y
  const height = tank.sample(p.uv).r
  const east = tank.sample(vec2(p.uv.x + ux, p.uv.y)).r
  const west = tank.sample(vec2(p.uv.x - ux, p.uv.y)).r
  const north = tank.sample(vec2(p.uv.x, p.uv.y + uy)).r
  const south = tank.sample(vec2(p.uv.x, p.uv.y - uy)).r
  const curve = height - (east + west + north + south) / 4
  const sway = vec2(clamp(vec2(east - west, north - south) * 26, -6, 6))
  // Crests print on the teal screen, troughs fainter on the coral screen; the sharper the crest, the bigger its dots.
  const crestDots = screenDots(p.point, 0.966, 0.259, 7.5, smoothstep(0.006, 0.07, curve), crisp)
  const troughDots = screenDots(p.point, 0.259, 0.966, 7.5, smoothstep(0.006, 0.07, -curve) * 0.6, crisp)

  // Pebbles on the bed, seen through the water: a flat tint, bent by the waves over it.
  const bq = vec2((p.point + sway * 2.4) / 118)
  const bcell = floor(bq)
  const bh = blend(int(int(bcell.x) + 31), int(int(bcell.y) + 17))
  const bturn = high(bh) * 6.3
  const brel = vec2((bq - bcell - vec2(0.3 + 0.4 * low(bh), 0.3 + 0.4 * high(bh))) * 118)
  const bsize = 6 + 9 * (low(bh) * 5.7 - floor(low(bh) * 5.7))
  const blong = vec2(brel.x * cos(bturn) + brel.y * sin(bturn), (brel.y * cos(bturn) - brel.x * sin(bturn)) * 1.5)
  const pebble = inside(length(blong) - bsize, 0.4) * step(0.55, high(bh) * 3.1 - floor(high(bh) * 3.1))

  // A film of pollen: fine specks that ride the slope, so a passing ring is seen moving through them.
  const q = vec2(p.point + sway * 2 + vec2(time * 3.2, time * -1.9))
  const dq = vec2(q / 23)
  const dcell = floor(dq)
  const dh = blend(int(int(dcell.x) + 7), int(dcell.y))
  const dust =
    inside(length(vec2(dq - dcell - vec2(0.25 + 0.5 * low(dh), 0.25 + 0.5 * high(dh)))) * 23 - 0.75, crisp) *
    step(0.5, low(dh) * 7.3 - floor(low(dh) * 7.3))

  // Small things afloat, one to a cell: bubbles, seeds, a pair of duckweed fronds. The water moves them but, unlike
  // the pollen, hardly bends them.
  const fq = vec2((p.point + sway * 0.6 + vec2(time * 3.2, time * -1.9)) / 70)
  const fcell = floor(fq)
  const fh = blend(int(fcell.x), int(fcell.y))
  const kind = low(fh) * 13.7 - floor(low(fh) * 13.7)
  const frel = vec2((fq - fcell - vec2(0.22 + 0.56 * low(fh), 0.22 + 0.56 * high(fh))) * 70)
  const fsize = high(fh) * 9.1 - floor(high(fh) * 9.1)
  const bubble = inside(abs(length(frel) - 1.9 - 1.6 * fsize) - 0.55, crisp) * step(0.42, kind) * step(kind, 0.68)
  const lean = vec2(cos(fsize * 6.3), sin(fsize * 6.3))
  const lies = dot(frel, lean)
  const spill = max(abs(lies) - 2.6, 0)
  const seed = inside(sqrt(max(dot(frel, frel) - lies * lies, 0) + spill * spill) - 0.9, crisp) * step(0.68, kind) * step(kind, 0.9)
  const frond = inside(min(length(vec2(frel - lean * 1.5)), length(vec2(frel + lean * 1.6)) + 0.5) - 1.7, crisp) * step(0.9, kind)

  let color = vec3(mix(ground, mix(DARK.shade, LIGHT.shade, day), pebble * 0.4))
  color = vec3(mix(color, ringTeal, crestDots))
  color = vec3(mix(color, ringCoral, troughDots))
  color = vec3(mix(color, ringTeal, dust * 0.8))
  color = vec3(mix(color, mix(ringTeal, mix(DARK.teal, LIGHT.teal, day), 0.5), max(bubble, frond)))
  color = vec3(mix(color, mix(ringCoral, mix(DARK.coral, LIGHT.coral, day), 0.6), seed))
  return vec4(color, 1)
})

// The creatures, each a small square laid where the cast says
// Each pass says how much of a window its squares may cover, and is not drawn if they cover more. The engine counts
// every square with a pixel and a half added on each edge, so the figures below leave room for coarse pixels.

// The corner of a square for one of its six vertices (two triangles).
const cornerOf = (v: number) => vec2(v == 1 || v == 2 || v == 4 ? 1 : -1, v == 2 || v == 4 || v == 5 ? 1 : -1)
const squareAt = (middle: vec2, corner: vec2, half: number) => vec2((middle + corner * half) / size * 2 - 1)
// Light falls from the upper left, so a shadow on the bed lies this far to the lower right, in points.
const SHADOW = vec2(9, -11)
// What the water's slope does to a place seen through it.
const swayAt = (uv: vec2) => vec2(clamp(leanAt(uv) * 40, -6, 6))
// A shadow on the bed: a flat tint, premultiplied.
const shaded = (shadow: number) => vec4(mix(DARK.shade, LIGHT.shade, dayOf()) * shadow * 0.75, shadow * 0.75)

// A strider's body and feet, in its own frame (x ahead, y out to the side, mirrored). "row" is how far into a stroke.
const bodyOf = (at: vec2) => min((length(vec2((at.x + 2) / 12.5, at.y / 2.6)) - 1) * 2.6, length(vec2(at.x - 11.8, at.y)) - 2.1)
const midKneeOf = (row: number) => vec2(6.5 - row, 13)
const midFootOf = (row: number) => vec2(13 - 12 * row, 29)
const hindKnee = vec2(-13, 10)
const hindFootOf = (row: number) => vec2(-27 + 3 * row, 19)
const foreFoot = vec2(15.5, 7)
// A leaf's blade in its own frame, one unit from middle to tip: round at the stalk, pointed at the tip, fine-toothed.
// Below zero is inside, in points.
const bladeOf = (u: vec2, long: number, wide: number) => {
  const x = clamp(u.x, -1, 1)
  const half = wide * sqrt(1 + x) * (1 - x) * (0.918 + 0.03 * sin(x * 26))
  return (abs(u.y) - half + max(abs(u.x) - 1, 0)) * long
}
const BEETLE_BIG = 1.5

// Minnows, under the surface: flat tints, bent by the water over them.
const minnows = shapes(
  { count: 6, instances: MINNOWS, cover: 0.05, draw: 'triangles' },
  (v, i) => {
    const who = MINNOW0 + i
    const top = cast.at(vec2(who, 0))
    const bottom = cast.at(vec2(who, 1))
    const corner = cornerOf(v)
    return { at: squareAt(top.xy, corner, 30), a: vec4(corner * 30, top.zw), b: vec4(bottom.x, bottom.y * zoomOf(), 0, 0) }
  },
  spot => {
    const crisp = crispOf(spot.px)
    const rel = vec2((spot.a.xy + swayAt(spot.uv) * 1.8) / spot.b.y)
    const nose = spot.a.zw
    const x = dot(rel, nose)
    const wag = sin(time * 6 + spot.b.x * 5)
    // The tail swings; the body follows a little.
    const back = clamp((2 - x) / 14, 0, 1)
    const y = nose.x * rel.y - nose.y * rel.x - wag * 4.5 * back * back
    const body = (length(vec2((x - 3) / 9.5, y / 3.1)) - 1) * 3.1
    // A forked tail: a wedge with a notch cut into its end.
    const tail = max(abs(y) - 0.5 - clamp((-6 - x) / 7, 0, 1) * 4.2, max(-13 + (4.2 - abs(y)) * 0.7 - x, x + 5))
    const fins = toLine(vec2(x, abs(y)), vec2(5, 2.6), vec2(1.5, 6)) - 0.8
    const ink = inside(min(min(body, tail), fins), crisp) * 0.9
    return vec4(mix(DARK.minnow, LIGHT.minnow, dayOf()) * ink, ink)
  },
)

// Shadows lie on the bed, under everything that floats, so they are laid down before the creatures on the surface.
const leafShadows = shapes(
  { count: 6, instances: LEAVES, cover: 0.042, draw: 'triangles' },
  (v, i) => {
    const top = cast.at(vec2(LEAF0 + i, 0))
    const corner = cornerOf(v)
    const long = LEAF_LONG[i]! * zoomOf()
    return { at: squareAt(vec2(top.xy + SHADOW * 1.3), corner, long * 1.05 + 14), a: vec4(corner * (long * 1.05 + 14), top.zw), b: vec4(long, LEAF_WIDE[i]!, 0, 0) }
  },
  spot => {
    const from = vec2(spot.a.xy + swayAt(spot.uv) * 1.6)
    const u = vec2((from.x * spot.a.z + from.y * spot.a.w) / spot.b.x, (from.y * spot.a.z - from.x * spot.a.w) / spot.b.x)
    return shaded(inside(bladeOf(u, spot.b.x, spot.b.y), 0.2))
  },
)

const striderShadows = shapes(
  { count: 6, instances: STRIDERS, cover: 0.125, draw: 'triangles' },
  (v, i) => {
    const top = cast.at(vec2(i, 0))
    const corner = cornerOf(v)
    const big = STRIDER_SIZE[i]! * zoomOf()
    return { at: squareAt(vec2(top.xy + SHADOW), corner, 41 * big + 12), a: vec4(corner * (41 * big + 12), top.zw), b: vec4(cast.at(vec2(i, 1)).x, big, 0, 0) }
  },
  spot => {
    const big = spot.b.y
    const row = spot.b.x
    const nose = spot.a.zw
    const rel = vec2((spot.a.xy + swayAt(spot.uv) * 1.6) / big)
    const s = vec2(dot(rel, nose), abs(nose.x * rel.y - nose.y * rel.x))
    // Each dimple throws a round shadow much bigger than the foot, and the body a thin one.
    const edge = big / 4.4
    return shaded(
      max(
        max(inside(length(vec2(s - midFootOf(row))) - 7.5, edge), inside(length(vec2(s - hindFootOf(row))) - 6.5, edge)),
        max(inside(length(vec2(s - foreFoot)) - 3.8, edge), inside(bodyOf(s) - 0.5, edge) * 0.7),
      ),
    )
  },
)

// The beetles' shadows, and the midges', which fall far from them because they are in the air.
const smallShadows = shapes(
  { count: 6, instances: BEETLES + MIDGES, cover: 0.02, draw: 'triangles' },
  (v, i) => {
    const beetle = i < BEETLES
    const top = cast.at(vec2(BEETLE0 + i + (beetle ? 0 : MINNOWS), 0))
    const corner = cornerOf(v)
    const big = (beetle ? BEETLE_BIG : cast.at(vec2(BEETLE0 + i + MINNOWS, 1)).x) * zoomOf()
    const half = beetle ? 24 : 15
    const long = beetle ? 8 * big : 4.2 * big
    return { at: squareAt(vec2(top.xy + SHADOW * (beetle ? 0.7 * big : 1.7)), corner, half), a: vec4(corner * half, top.zw), b: vec4(long, beetle ? 1 : 1.6, 0, 0) }
  },
  spot => {
    const from = vec2(spot.a.xy + swayAt(spot.uv))
    const nose = spot.a.zw
    return shaded(inside(length(vec2(dot(from, nose) / spot.b.y, nose.x * from.y - nose.y * from.x)) - spot.b.x / spot.b.y, 0.3) * 0.9)
  },
)

// A crown of droplets where a raindrop has just landed.
const crowns = shapes(
  { count: 6, instances: DROPS, cover: 0.024, draw: 'triangles' },
  (v, i) => {
    const drop = cast.at(vec2(DROP0 + i, 0))
    const corner = cornerOf(v)
    return { at: squareAt(drop.xy, corner, 46), a: vec4(corner * 46, drop.zw), b: vec4(cast.at(vec2(DROP0 + i, 1)).x, 0, 0, 0) }
  },
  spot => {
    const crisp = crispOf(spot.px)
    const rel = spot.a.xy
    const fly = clamp(spot.a.z / 0.8, 0, 1)
    const spoke = floor(atan(rel.y, rel.x) / 0.898 + 0.5)
    const luck = low(blend(int(spoke), int(spot.a.w)))
    const far = 5 + (16 + 16 * luck) * (1 - (1 - fly) * (1 - fly))
    const bead = length(vec2(rel - vec2(cos(spoke * 0.898), sin(spoke * 0.898)) * far))
    const big = (1.3 + 1.3 * luck) * (1 - fly)
    return printed(spot.b.x * inside(bead - big, crisp) * step(fly, 0.98) * step(0.001, fly), 0, spot.point)
  },
)

const leaves = shapes(
  { count: 6, instances: LEAVES, cover: 0.05, draw: 'triangles' },
  (v, i) => {
    const top = cast.at(vec2(LEAF0 + i, 0))
    const corner = cornerOf(v)
    const long = LEAF_LONG[i]! * zoomOf()
    return { at: squareAt(top.xy, corner, long * 1.38 + 6), a: vec4(corner * (long * 1.38 + 6), top.zw), b: vec4(long, LEAF_WIDE[i]!, LEAF_BITE[i]!, i) }
  },
  spot => {
    const crisp = crispOf(spot.px)
    const long = spot.b.x
    const wide = spot.b.y
    const ca = spot.a.z
    const sa = spot.a.w
    const frame = (from: vec2) => vec2((from.x * ca + from.y * sa) / long, (from.y * ca - from.x * sa) / long)
    const nib = (u: vec2) => spot.b.z * inside((length(vec2(u.x - 0.2, u.y - wide * 0.86)) - 0.2) * long, crisp)
    // The teal plate lies true; the coral plate is a little out of register, more so where the water leans.
    const ut = frame(spot.a.xy)
    const uc = frame(vec2(spot.a.xy + vec2(1.5, -1.1) + swayAt(spot.uv) * 0.35))
    const fill = inside(bladeOf(uc, long, wide), crisp) * (1 - nib(uc))
    const onLeaf = inside(bladeOf(ut, long, wide), crisp) * (1 - nib(ut))
    const within = inside(bladeOf(ut, long, wide) + 2.8, 0.625) * (1 - nib(ut))
    const rib = inside(abs(ut.y) * long - 1, crisp) * step(-1.32, ut.x) * step(ut.x, 0.86)
    const lane = (ut.x - 1.15 * abs(ut.y)) * 3.3
    const vein = inside(abs(lane - floor(lane) - 0.5) * long / 5 - 0.7, crisp) * within * step(-0.8, ut.x)
    const shade = screenDots(spot.point, 0.966, 0.259, 5.5, 0.62, crisp) * onLeaf * step(ut.y, 0)
    // Two beads of water sit on the blade.
    const beadAt = (m: vec2, r: number) => inside(abs(length(vec2(ut - m)) * long - r) - 0.7, crisp) * step(0.25, length(vec2(ut - m - vec2(0.03, 0.03))) * long / r)
    const beads = max(beadAt(vec2(0.3, -wide * 0.4), 3.2), beadAt(vec2(-0.45, wide * 0.45), 2.3)) * onLeaf
    return printed(max(max(rib, vein), max(shade, beads)), fill, spot.point)
  },
)

const beetles = shapes(
  { count: 6, instances: BEETLES, cover: 0.01, draw: 'triangles' },
  (v, i) => {
    const top = cast.at(vec2(BEETLE0 + i, 0))
    const corner = cornerOf(v)
    return { at: squareAt(top.xy, corner, 22), a: vec4(corner * 22, top.zw), b: vec4(BEETLE_BIG * zoomOf(), 0, 0, 0) }
  },
  spot => {
    const big = spot.b.x
    const w = crispOf(spot.px) * big
    const nose = spot.a.zw
    const at = vec2(dot(spot.a.xy, nose) / big, abs(nose.x * spot.a.y - nose.y * spot.a.x) / big)
    const shell = (length(vec2(at.x / 7.4, at.y / 4.8)) - 1) * 4.8
    // A seam down the back, a collar and two pairs of oar legs are the coral plate's share.
    const seam = inside(at.y - 0.6, w) * inside(shell + 1, w) * step(at.x, 3)
    const collar = inside(abs(at.x - 3.4) - 0.55, w) * inside(shell + 1, w)
    const oars = inside(min(toLine(at, vec2(-1.5, 4), vec2(-7, 9.5)), toLine(at, vec2(3, 4), vec2(6.5, 8))) - 0.7, w)
    return printed(inside(shell, w), max(max(seam, collar), oars), spot.point)
  },
)

const striders = shapes(
  { count: 6, instances: STRIDERS, cover: 0.1, draw: 'triangles' },
  (v, i) => {
    const top = cast.at(vec2(i, 0))
    const corner = cornerOf(v)
    const big = STRIDER_SIZE[i]! * zoomOf()
    return { at: squareAt(top.xy, corner, 41 * big + 4), a: vec4(corner * (41 * big + 4), top.zw), b: vec4(cast.at(vec2(i, 1)).x, big, 0, 0) }
  },
  spot => {
    const big = spot.b.y
    const w = crispOf(spot.px) * big
    const row = spot.b.x
    const nose = spot.a.zw
    // Its own frame: x ahead, y out to the side, mirrored. Teal plate true, coral plate out of register.
    const own = (rel: vec2) => vec2(dot(rel, nose), abs(nose.x * rel.y - nose.y * rel.x))
    const t = own(vec2(spot.a.xy / big))
    const c = own(vec2((spot.a.xy + vec2(1.5, -1.1) + swayAt(spot.uv) * 0.35) / big))
    const midKnee = midKneeOf(row)
    const midFoot = midFootOf(row)
    const hindFoot = hindFootOf(row)
    const legs = min(
      min(toLine(c, vec2(2.5, 1.4), midKnee), toLine(c, midKnee, midFoot)),
      min(min(toLine(c, vec2(-3, 1.4), hindKnee), toLine(c, hindKnee, hindFoot)), toLine(c, vec2(7.5, 1.2), foreFoot)),
    )
    const knees = min(length(vec2(c - midKnee)), length(vec2(c - hindKnee))) - 1.35
    const feeler = toLine(c, vec2(13, 0.9), vec2(19, 4.6)) - 0.4
    const coral = max(max(inside(bodyOf(c), w), inside(legs - 0.8, w)), max(inside(knees, w), inside(feeler, w)))
    // A dimple under each foot: a ring, heavier on its outer side.
    const dimple = (foot: vec2, r: number) => inside(abs(length(vec2(t - foot)) - r) - 1, w) * (0.5 + 0.5 * clamp((t.y - foot.y) / r + 0.3, -1, 1))
    // The teal plate also carries a stripe down the back, three bands across the tail, and the eyes.
    const stripe = inside(length(vec2(t.x - clamp(t.x, -1, 7), t.y)) - 0.6, w)
    const bands = inside(abs(t.x + 7.5 - 3 * clamp(floor((t.x + 7.5) / 3 + 0.5), -1, 1)) - 0.45, w) * inside(t.y - 2.2, w)
    const eyes = inside(length(vec2(t.x - 12.6, t.y - 1.6)) - 0.95, w)
    const teal = max(max(max(dimple(midFoot, 5.4), dimple(hindFoot, 4.8)), max(dimple(foreFoot, 3), stripe)), max(bands, eyes))
    return printed(teal, coral, spot.point)
  },
)

// Midges dance in the air over the water.
const midges = shapes(
  { count: 6, instances: MIDGES, cover: 0.01, draw: 'triangles' },
  (v, i) => {
    const top = cast.at(vec2(MIDGE0 + i, 0))
    const corner = cornerOf(v)
    const big = cast.at(vec2(MIDGE0 + i, 1)).x * zoomOf()
    return { at: squareAt(top.xy, corner, 8 * big + 3), a: vec4(corner * (8 * big + 3), top.zw), b: vec4(big, i, 0, 0) }
  },
  spot => {
    const big = spot.b.x
    const w = crispOf(spot.px) * big
    const nose = spot.a.zw
    const at = vec2(dot(spot.a.xy, nose) / big, abs(nose.x * spot.a.y - nose.y * spot.a.x) / big)
    const body = (length(vec2(at.x / 3.6, at.y / 1.2)) - 1) * 1.2
    // Wings beat too fast to see: each prints as a pale fan.
    const wing = (length(vec2((at.x + 1.2 - at.y * 0.45) / 2.3, (at.y - 3) / 3)) - 1) * 2.3
    return printed(inside(wing, w) * 0.7, inside(body, w), spot.point)
  },
)

export default shader({
  fps: 30,
  passes: [cast, tank, water, minnows, leafShadows, striderShadows, smallShadows, crowns, leaves, beetles, striders, midges],
})
