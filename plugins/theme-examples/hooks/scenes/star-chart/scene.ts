// Star Chart: a copperplate celestial chart. Stars in three engraved sizes flare now and then, three drawing hands rule
// figure lines between them and let them fade, a slow meteor crosses with a dotted tail, and three small planets creep
// along a dotted ecliptic.
// Touch: the stars near a pointer rule stippled copper lines to it, the chart's own lines near it show in copper, and a
// press sets a graduated circle down. Two to four pointers are joined by a copper thread that runs from star to star.
// The picture is a chart of 1512 by 945 points laid over the window the way the still Svg is (centred, filling it), and
// its first frame is the still Svg, which is drawn from the same numbers.
// The ground is the picture pass. Everything on it is drawn as shapes, so a pixel pays only for the ink that lands on it.
// Each shapes pass declares the most of the window its shapes can cover: counted as the engine counts them, with
// their spare pixels, on a screen of one pixel to two points, plus a third.
import {
  PI, abs, atan, buffer, clamp, cos, dot, dt, exp, floor, fract, int, length, max, min, mix, mod, picture, pointer,
  pointerCount, pointers, px, scene, shader, shapes, sin, size, smoothstep, step, table, time, unsigned, vec2, vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

const W = 1512
const H = 945
// One star lives in every cell of this many points.
const CELL = 120
// A pointer rules lines to the stars within REACH, and lights the chart's own lines within GLOW.
const REACH = 175
const GLOW = 210
// Lines stop this far short of a star, as engraved lines do, and this far short of a pointer.
const CLEAR = 12
const HAND = 7
// A drawing hand rules the lines of the stars within this far of the spot it picked.
const FIGURE = 240
const METEOR_EVERY = 21
const METEOR_LEAD = 5.5
const METEOR_SPEED = 50

// This scene's own integer mixer: two multiplies fold the pair, then two rounds of a doubled xor-shift and a multiply,
// and one last xor-shift.
const weave = (x: number, y: number) => {
  let h = int(x * 0x2d8a61b7 + y * 0x6e13c94d + 1309)
  h = int(h ^ (h >>> 9) ^ (h >>> 22))
  h = int(h * 0x3b52a7e9)
  h = int(h ^ (h >>> 12) ^ (h << 7))
  h = int(h * 0x51f6d24b)
  h = int(h ^ (h >>> 14))
  return h
}
const low = (h: number) => unsigned(int(h & 0xffff)) / 65536
const high = (h: number) => unsigned(int(h >>> 16)) / 65536
const sat = (x: number) => clamp(x, 0, 1)

// The chart fills the window as the Svg does: one scale for both axes, centred, cropped at the longer side.
const zoom = () => max(size.x / W, size.y / H)
const toChart = (at: number) => vec2((at - size * 0.5) / zoom() + vec2(W / 2, H / 2))
// A place in the part of the chart that shows: (0, 0) its bottom left, (1, 1) its top right.
const inView = (share: number) => vec2(vec2(W / 2, H / 2) + ((share - 0.5) * size) / zoom())
// A chart place as a shape's vertex wants it, -1 to 1 across the window.
const toClip = (at: number) => vec2(((at - vec2(W / 2, H / 2)) * 2 * zoom()) / size)

// Where the star of cell (i, j) is, on the chart.
const starPos = (i: number, j: number) => {
  const h = weave(int(i), int(j))
  return vec2((i + 0.05 + 0.9 * low(h)) * CELL, (j + 0.05 + 0.9 * high(h)) * CELL)
}

// How much a pointer counts: it eases in when it comes, out over the second after it lifts, and is dimmer over the app's own text.
const hold = (f: { gone: number; age: number; over: number }) =>
  (1 - smoothstep(0, 1, f.gone)) * smoothstep(0, 0.2, f.age) * (1 - 0.35 * f.over)

// How strongly a pointer at "at" rules a line to the star at s.
const pull = (s: number, at: number) => {
  const r = length(vec2(at - s)) / REACH
  return sat(1 - r * r * r * r)
}

// The thread between two consecutive pointers runs through one star in each column between them (each row, for a steep pair).
// This lays the pair out along x, left to right, whichever way it really runs.
const pairOf = (k: number) => {
  const a = pointer(k)
  const b = pointer(k + 1)
  const pa = toChart(a.at)
  const pb = toChart(b.at)
  const d = vec2(pb - pa)
  const wide = abs(d.x) >= abs(d.y)
  const lean = abs(abs(d.x) - abs(d.y)) / max(abs(d.x) + abs(d.y), 1)
  const strength =
    step(k + 1.5, pointerCount) * hold(a) * hold(b) * smoothstep(70, 150, length(d)) * smoothstep(0, 0.12, lean)
  const A = wide ? pa : vec2(pa.y, pa.x)
  const B = wide ? pb : vec2(pb.y, pb.x)
  const flip = A.x > B.x
  const L = flip ? B : A
  const R = flip ? A : B
  return { wide, strength, L, R, first: floor(L.x / CELL), last: floor(R.x / CELL), slope: (R.y - L.y) / max(R.x - L.x, 1) }
}
type Pair = ReturnType<typeof pairOf>
// Which row the pair's thread takes in a column, as a row number with its fraction.
const rowAt = (pair: Pair, col: number) =>
  (pair.L.y + pair.slope * (clamp((col + 0.5) * CELL, pair.L.x, pair.R.x) - pair.L.x)) / CELL
// A thread lets go of a star as its line nears the edge of the star's row, so that it never jumps from one star to the next.
const grip = (row: number) => smoothstep(0, 0.15, min(row - floor(row), 1 - row + floor(row)))

// How strongly the threads hold the star of cell (i, j).
const threaded = (i: number, j: number) => {
  let best = 0
  for (const k of [0, 1, 2]) {
    const pair = pairOf(k)
    const ci = pair.wide ? i : j
    const cj = pair.wide ? j : i
    const row = rowAt(pair, ci)
    best = max(best, ci >= pair.first && ci <= pair.last && cj === floor(row) ? pair.strength * grip(row) : 0)
  }
  return best
}

const GRID = { size: [16, 16], float: 16, filter: 'nearest' } as const

// One texel: 1 on parchment, 0 on the ink-blue plate, read from the Svg's ground at the middle of the window, which the
// still keeps bare. Two of three nearby readings decide, so one stray pixel cannot turn the inks over.
const plate = buffer({ size: [1, 1], filter: 'nearest' }, p => {
  let votes = 0
  for (const nudge of [-0.004, 0, 0.004]) {
    votes += step(0.4, dot(scene.sample(vec2(0.5 + nudge, 0.5 - nudge)).rgb, vec3(0.3, 0.6, 0.1)))
  }
  return vec4(step(1.5, votes), 0, 0, 1)
})

// What the pointers have inked at each star, eased in time so that a hand rushing past leaves only a trace:
// how lit the star's figure line is, how strong its lines to pointers may be, and how strong its links in a thread.
const ease = (was: number, goal: number, up: number, down: number) =>
  was + (goal - was) * (1 - exp(-dt * (goal > was ? up : down)))
const glow: Buffer = buffer(GRID, (p): vec4 => {
  const i = p.cell.x - 1
  const j = p.cell.y - 1
  const s = starPos(i, j)
  let lit = 0
  let fan = 0
  for (const f of pointers) {
    const at = toChart(f.at)
    const d = length(vec2(at - s)) / GLOW
    lit = max(lit, sat(1 - d * d * d) * hold(f))
    fan = max(fan, pull(s, at) * hold(f))
  }
  const thread = threaded(i, j)
  const was = glow.at(p.cell)
  return vec4(ease(was.r, max(lit, thread), 5, 1.3), ease(was.g, fan, 6, 4), ease(was.b, thread, 6, 4), 1)
})
const glowAt = (i: number, j: number) => glow.at(vec2(i + 1, j + 1))

// Two inks over a flat ground: the chart's ink and a copper ink, each with a dark plate and a light one.
const plated = (dark: number, light: number) => vec3(mix(dark, light, plate.at(vec2(0, 0)).r))
const groundTone = () => plated(vec3(0.063, 0.106, 0.188), vec3(0.925, 0.886, 0.792))
const arcInk = () => plated(vec3(0.3, 0.4, 0.56), vec3(0.55, 0.45, 0.3))
const lineInk = () => plated(vec3(0.62, 0.71, 0.86), vec3(0.24, 0.29, 0.42))
const starInk = () => plated(vec3(0.96, 0.9, 0.74), vec3(0.13, 0.16, 0.26))
const copperInk = () => plated(vec3(0.93, 0.6, 0.36), vec3(0.74, 0.33, 0.18))

// The ground: flat, with the chart's coordinate arcs and a band of hatching.
const ground = picture(p => {
  const z = zoom()
  const pt = vec2((p.point - size * 0.5) / z + vec2(W / 2, H / 2))
  const grain = p.px / z
  const ipx = 1 / grain
  // Circles and meridians about a pole above the chart, with a ladder of ticks on the circles.
  const rel = vec2(pt - vec2(W * 0.8, H * 1.32))
  const rad = length(rel)
  const off = mod(rad + 80, 160) - 80
  const ang = atan(rel.y, rel.x)
  const sect = PI / 12
  const merid = abs(fract(ang / sect + 0.5) - 0.5) * sect * rad
  const tick = abs(fract((ang * 6) / sect + 0.5) - 0.5) * (sect / 6) * rad
  const arcs = max(
    max(sat((0.5 - min(abs(off), abs(off - 5))) * ipx + 0.5), sat((0.5 - merid) * ipx + 0.5)),
    sat((0.45 - tick) * ipx + 0.5) * step(0, off) * step(off, 5),
  )
  // The way an engraver shades the Milky Way. Too fine for a coarse picture, so it turns to a flat tone there.
  const bandAt = dot(vec2(pt - vec2(W * 0.87, H * 0.5)), vec2(0.978, -0.208)) + 40 * sin(dot(pt, vec2(0.208, 0.978)) / 170)
  const band = 1 - smoothstep(50, 115, abs(bandAt))
  const hatch = sat((0.4 - abs(fract((pt.x - pt.y) / 9.9) - 0.5) * 7) * ipx + 0.5)
  const shade = band * mix(0.11, hatch, sat(1.7 - grain))
  return vec4(mix(groundTone(), arcInk(), max(arcs * 0.24, shade * 0.16)), 1)
})

// The two triangles of a quad: which end and which side each of the six vertices is.
const ENDS = [0, 1, 0, 1, 1, 0]
const SIDES = [-1, -1, 1, -1, 1, 1]
// A quad around a stroke from "from" along the unit heading "dir": inked from lo to hi and reaching half to either side,
// with a pixel to spare all round for a soft edge. Its a.xy is the place in the stroke's own frame.
const strokeQuad = (v: number, from: number, dir: vec2, lo: number, hi: number, half: number) => {
  const grain = px / zoom()
  const along = mix(lo - grain, hi + grain, ENDS[v]!)
  const side = SIDES[v]! * (half + grain)
  return { at: toClip(vec2(from + dir * along + vec2(-dir.y, dir.x) * side)), along, side }
}
// How much of a pixel a stroke of half-width "half" inks, between lo and hi along it. Its ends taper, as a burin's cut does.
const swell = (t: number, n: number, lo: number, hi: number, half: number, ipx: number) => {
  const inside = min(t - lo, hi - t)
  return sat((half * (0.6 + 0.4 * sat(inside * 0.06)) - abs(n)) * ipx + 0.5) * sat(inside * ipx + 0.5)
}

// Stipple: fine specks on a grid of their own, breathing slowly.
const specks = shapes(
  { count: 693, cover: 0.07, draw: 'points' },
  v => {
    const si = mod(v, 33)
    const sj = floor(v / 33)
    const hd = weave(int(int(si) + 911), int(int(sj) - 577))
    const r = 0.7 + 0.7 * fract(low(hd) * 13.7)
    const shown = step(fract(high(hd) * 7.3), 0.7) * (0.55 + 0.25 * sin(time * 0.6 + low(hd) * 40))
    const grain = px / zoom()
    const span = 2 * r + 2 * grain
    return {
      at: toClip(vec2((si + 0.12 + 0.76 * low(hd)) * 46, (sj + 0.12 + 0.76 * high(hd)) * 46)),
      size: span / grain,
      a: vec4(r, shown, span, 0),
      hide: shown < 0.01,
    }
  },
  s => {
    const cover = sat(((s.a.x - length(vec2(s.coord - 0.5)) * s.a.z) * zoom()) / s.px + 0.5) * s.a.y
    return vec4(starInk() * cover, cover)
  },
)

// Each star's one figure line to a neighbour. Three drawing hands rule them; pointers light them in copper.
const figureLines = shapes(
  { count: 6, instances: 150, cover: 0.35 },
  (v, n) => {
    const i = mod(n, 15) - 1
    const j = floor(n / 15) - 1
    const s = starPos(i, j)
    const h2 = weave(weave(int(i), int(j)), 7)
    // Even columns may rule east, north-east, north or north-west; odd ones east or north.
    const pick = low(h2)
    const q = mod(i, 2) < 0.5 ? floor(pick * 4) : floor(pick * 2) * 2
    const dx = q < 1.5 ? 1 : q < 2.5 ? 0 : -1
    const dy = q < 0.5 ? 0 : 1
    const d = vec2(starPos(i + dx, j + dy) - s)
    const len = length(d)
    const rank = high(h2)
    // The two hands with the strongest claim on this line: how strong each is, and how much of the line it has ruled.
    let a1 = 0
    let g1 = 0
    let a2 = 0
    let g2 = 0
    // Each hand picks a spot in a side margin and rules the lines near it outward, then the figure fades.
    for (const k of [0, 1, 2]) {
      const period = [34, 43, 55][k]!
      const tt = time + [12, 10.5, 0][k]!
      const turn = floor(tt / period)
      const tau = tt - turn * period
      const hs = weave(int(turn), int([8, 12, 130][k]!))
      const mx = 0.04 + 0.2 * low(hs)
      const share = vec2(mod(turn + [0, 1, 1][k]!, 2) > 0.5 ? 1 - mx : mx, 0.18 + 0.64 * high(hs))
      // The first figures stand where the still shows them; later ones keep to the part of the chart that shows.
      const seed = turn < 0.5 ? vec2(share * vec2(W, H)) : inView(share)
      const dist = length(vec2(s - seed))
      const member = (1 - smoothstep(0.7 * FIGURE, FIGURE, dist)) * step(rank, 0.85)
      const gk = sat((tau - 1 - (6 * dist) / FIGURE) / 1.8)
      const ak = member * (1 - smoothstep(20, 27, tau)) * step(0.001, gk)
      if (ak > a1) {
        a2 = a1
        g2 = g1
        a1 = ak
        g1 = gk
      } else if (ak > a2) {
        a2 = ak
        g2 = gk
      }
    }
    const lit = min(glowAt(i, j).r, glowAt(i + dx, j + dy).r)
    // A line being ruled gets a wider quad, for the burr beside it.
    const working = max(
      step(0.004, a1) * step(0.002, g1) * step(g1, 0.998),
      step(0.004, a2) * step(0.002, g2) * step(g2, 0.998),
    )
    const quad = strokeQuad(v, s, vec2(d / max(len, 0.01)), CLEAR, len - CLEAR, 1 + 3.5 * working)
    return {
      at: quad.at,
      a: vec4(quad.along, quad.side, len - CLEAR, lit),
      b: vec4(a1, g1, a2, g2),
      hide: a1 + lit < 0.004,
    }
  },
  s => {
    const ipx = zoom() / s.px
    const t = s.a.x
    const n = s.a.y
    const full = s.a.z
    // What one hand has made of the line: its ink as far as it has ruled, the burin at the tip while it rules,
    // and the burr the burin throws up to either side, which stays where it fell and fades as the tip moves on.
    const ruledBy = (strength: number, share: number) => {
      const to = CLEAR + (full - CLEAR) * share
      const working = strength * step(0.002, share) * step(share, 0.998)
      const nib = working * sat((2 - abs(t - to) - abs(n)) * ipx + 0.5)
      const behind = to - t
      const beat = fract(t / 10)
      const burr =
        working * step(1, behind) * sat(1 - behind / 40) * 0.8 *
        sat((0.9 - length(vec2((abs(beat - 0.5) - 0.25) * 10, n - (beat < 0.5 ? 2.4 : -2.4)))) * ipx + 0.5)
      return { ink: strength * 0.85 * swell(t, n, CLEAR, to, 0.6, ipx), tool: max(nib, burr) }
    }
    // Where two hands' figures share a line, the eye gets the stronger ink at each place, so no line ever starts over.
    const one = ruledBy(s.b.x, s.b.y)
    const two = ruledBy(s.b.z, s.b.a)
    const chart = max(one.ink, two.ink)
    const copper = max(s.a.a * 0.9 * swell(t, n, CLEAR, full, 0.55, ipx), max(one.tool, two.tool))
    return vec4(mix(lineInk() * chart, copperInk(), copper), chart + copper - chart * copper)
  },
)

// The thread's links: for each pair of pointers, one link back from each column's star toward the pointer the thread
// starts from, and one on from the last star to the pointer at the far end.
const threadLinks = shapes(
  { count: 6, instances: 48, cover: 0.18 },
  (v, n) => {
    const pair = pairOf(floor(n / 16))
    const c = mod(n, 16)
    const isLast = c > 14.5
    const ci = isLast ? pair.last : c - 1
    const row = rowAt(pair, ci)
    const before = rowAt(pair, ci - 1)
    const isFirst = ci === pair.first
    const cell = pair.wide ? vec2(ci, floor(row)) : vec2(floor(row), ci)
    const s = starPos(cell.x, cell.y)
    const prev = pair.wide ? starPos(ci - 1, floor(before)) : starPos(floor(before), ci - 1)
    const toHand = isLast || isFirst
    const end = isLast ? pair.R : pair.L
    const target = toHand ? (pair.wide ? end : vec2(end.y, end.x)) : prev
    const w =
      (ci >= pair.first && ci <= pair.last ? 1 : 0) * pair.strength * grip(row) * (toHand ? 1 : grip(before))
    const alpha = min(w, glowAt(cell.x, cell.y).b)
    const d = vec2(target - s)
    const len = length(d)
    const reach = len - (toHand ? HAND : CLEAR)
    const quad = strokeQuad(v, s, vec2(d / max(len, 0.01)), CLEAR, reach, 1)
    return { at: quad.at, a: vec4(quad.along, quad.side, reach, alpha), hide: alpha < 0.004 }
  },
  s => {
    const cover = s.a.a * 0.9 * swell(s.a.x, s.a.y, CLEAR, s.a.z, 0.75, zoom() / s.px)
    return vec4(copperInk() * cover, cover)
  },
)

// Each pointer's lines to the stars around it: the sixteen cells about the pointer hold every star within REACH.
const fanLines = shapes(
  { count: 6, instances: 64, cover: 0.1 },
  (v, n) => {
    const f = pointer(floor(n / 16))
    const slot = mod(n, 16)
    const at = toChart(f.at)
    const ci = floor(at.x / CELL - 0.5) - 1 + mod(slot, 4)
    const cj = floor(at.y / CELL - 0.5) - 1 + floor(slot / 4)
    const s = starPos(ci, cj)
    const d = vec2(at - s)
    const len = length(d)
    const alpha = min(pull(s, at) * hold(f) * step(floor(n / 16) + 0.5, pointerCount), glowAt(ci, cj).g)
    const quad = strokeQuad(v, s, vec2(d / max(len, 0.01)), CLEAR, len - HAND, 1.3)
    return { at: quad.at, a: vec4(quad.along, quad.side, len - HAND, alpha), hide: alpha < 0.004 }
  },
  s => {
    // A hairline with a row of dots on it that runs toward the pointer, slowly enough that no spot on the line
    // sees a dot pass more than about once a second.
    const ipx = zoom() / s.px
    const t = s.a.x
    const inside = sat(min(t - CLEAR, s.a.z - t) * ipx + 0.5)
    const dots = sat((1.15 - length(vec2((fract(t / 7 - time * 0.9) - 0.5) * 7, s.a.y))) * ipx + 0.5)
    const hair = 0.4 * sat((0.3 - abs(s.a.y)) * ipx + 0.5)
    const cover = s.a.a * 0.9 * inside * max(dots, hair)
    return vec4(copperInk() * cover, cover)
  },
)

// A star with four long points and four short ones, folded into one eighth: two edges, each a unit normal and an offset.
const STAR_BIG = [0.147, 0.989, 1.543, 0.912, -0.411, 2.056]
const STAR_MID = [0.138, 0.99, 0.912, 0.971, -0.238, 1.451]
const pointedStar = (a: number, b: number, S: readonly number[]) =>
  min(a * S[0]! + b * S[1]! - S[2]!, a * S[3]! + b * S[4]! - S[5]!)

// The stars, in three engraved sizes: eight-point with a glory of fine strokes, four-point, and a small ring.
// Now and then one flares, and the ones a pointer has linked flare too.
const starGlyphs = shapes(
  { count: 6, instances: 150, cover: 0.35 },
  (v, n) => {
    const i = mod(n, 15) - 1
    const j = floor(n / 15) - 1
    const h3 = weave(weave(int(i), int(j)), 19)
    const rank = low(h3)
    const every = 7 + 12 * high(h3)
    const flare = sin(PI * sat((fract(time / every + rank * 7.3) * every) / 2.6))
    const lit = glowAt(i, j)
    const reach = max(flare * flare, max(lit.g, lit.b))
    const tip = rank < 0.16 ? 10.5 : 6.6
    const half = (rank < 0.16 || reach > 0.01 ? tip + 6 + 7 * reach : tip + 1) + px / zoom()
    const corner = vec2(ENDS[v]! * 2 - 1, SIDES[v]!) * half
    return { at: toClip(vec2(starPos(i, j) + corner)), a: vec4(corner, reach, rank) }
  },
  s => {
    const ipx = zoom() / s.px
    const reach = s.a.z
    const isBig = s.a.a < 0.16
    const near = length(s.a.xy)
    const q = abs(s.a.xy)
    const qa = max(q.x, q.y)
    const qb = min(q.x, q.y)
    const tip = isBig ? 10.5 : 6.6
    const pointed =
      sat(-(isBig ? pointedStar(qa, qb, STAR_BIG) : pointedStar(qa, qb, STAR_MID)) * ipx + 0.5) *
      (isBig ? sat((near - 1.5) * ipx + 0.5) : 1)
    const ring = sat((0.75 - abs(near - 3)) * ipx + 0.5)
    const taper = sat(1 - (qa - tip) / (9 * reach + 0.01))
    const ray = sat((0.65 * taper - qb) * ipx + 0.5) * step(tip - 0.5, qa) * sat(taper * 6)
    // The glory: sixteen short strokes around the star, which lengthen when it flares.
    const across = abs(fract(atan(qb, qa) / (PI / 8)) - 0.5) * (PI / 8) * near
    const glory =
      sat((0.45 - across) * ipx + 0.5) * step(tip + 2.5, near) * sat((tip + 6 + 7 * reach - near) * 0.5) * (isBig ? 1 : reach)
    const cover = s.a.a > 0.58 ? max(ring, glory * reach) : max(pointed, max(ray, glory * 0.85))
    return vec4(starInk() * cover, cover)
  },
)

// The meteor, in its own frame: u runs along its path from where it began, v across it.
const meteor = shapes(
  { count: 6, cover: 0.03 },
  v => {
    const turn = floor((time + METEOR_LEAD) / METEOR_EVERY)
    const tau = time + METEOR_LEAD - turn * METEOR_EVERY
    const h = weave(int(turn), 4934)
    const h2 = weave(h, 99)
    const mx = 0.07 + 0.13 * low(h)
    const share = vec2(mod(turn, 2) > 0.5 ? 1 - mx : mx, 0.85 + 0.2 * high(h))
    // The first meteor is where the still shows it; later ones keep to the part of the chart that shows.
    const start = turn < 0.5 ? vec2(share * vec2(W, H)) : inView(share)
    const ang = -PI / 2 + (low(h2) - 0.5) * 0.7
    const life = smoothstep(0, 1, tau) * (1 - smoothstep(10.5, 12, tau))
    const uh = METEOR_SPEED * tau
    const quad = strokeQuad(v, start, vec2(cos(ang), sin(ang)), uh - 360, uh + 13, 26)
    return { at: quad.at, a: vec4(quad.along, quad.side, uh, life), b: vec4(unsigned(int(h2 >>> 22)), 0, 0, 0), hide: life < 0.004 }
  },
  s => {
    const ipx = zoom() / s.px
    const u = s.a.x
    const v = s.a.y
    const uh = s.a.z
    const back = uh - u
    const av = abs(v)
    // Its head is an eight-point star with a pricked centre.
    const head =
      sat(-pointedStar(max(abs(back), av), min(abs(back), av), STAR_BIG) * ipx + 0.5) *
      sat((length(vec2(back, v)) - 1.5) * ipx + 0.5)
    // Five engraved strokes in its wake, the middle one longest.
    const lane = clamp(floor(v / 3.2 + 0.5), -2, 2)
    const wakeLen = 84 - 28 * abs(lane)
    const wake = sat((0.45 - abs(v - lane * 3.2)) * ipx + 0.5) * step(12, back) * sat((wakeLen - back) / (0.5 * wakeLen))
    // The dotted tail: dots left on the path, each shrinking with its age.
    const uk = (floor(u / 13) + 0.5) * 13
    const young = step(0, uh - 14 - uk) * sat(1 - (uh - 14 - uk) / METEOR_SPEED / 6) * step(0, u)
    const dots = sat((0.7 + 2.3 * young - length(vec2(u - uk, v))) * ipx + 0.5) * step(0.001, young)
    // Stippled dust in copper: three sets of finer specks that drift off the path as they age.
    let dust = 0
    for (const layer of [0, 1, 2]) {
      const gap = 5 + 2 * layer
      const k2 = floor(u / gap)
      const hk = weave(int(k2), int(floor(s.b.x + 0.5) + layer * 57))
      const uk2 = (k2 + 0.2 + 0.6 * low(hk)) * gap
      const age = (uh - uk2) / METEOR_SPEED
      const vk = (high(hk) - 0.5) * 2 * (3 + 18 * sat(age / 7))
      dust = max(
        dust,
        sat((0.9 + 0.7 * fract(low(hk) * 9.1) - length(vec2(u - uk2, v - vk))) * ipx + 0.5) *
          step(0, age) * sat(1 - age / 7) * step(0, u),
      )
    }
    const copper = dust * 0.85 * s.a.a
    const dark = max(head, max(wake * 0.7, dots * 0.9)) * s.a.a
    return vec4(mix(copperInk() * copper, starInk(), dark), copper + dark - copper * dark)
  },
)

// The ecliptic: a dotted copper circle across the chart, every sixth dot a small ring.
const ECLIPTIC = { x: 529, y: -1040, r: 1600, from: 1.9077, span: 0.9984 }
const eclipticAt = (turn: number) => vec2(ECLIPTIC.x + ECLIPTIC.r * cos(turn), ECLIPTIC.y + ECLIPTIC.r * sin(turn))
const ecliptic = shapes(
  { count: 161, cover: 0.03, draw: 'points' },
  v => {
    const r = mod(v, 6) < 0.5 ? 2.1 : 0.75
    const grain = px / zoom()
    const span = 2 * r + 2 * grain
    return { at: toClip(eclipticAt(ECLIPTIC.from - v * 0.00624)), size: span / grain, a: vec4(r, span, 0, 0) }
  },
  s => {
    const d = length(vec2(s.coord - 0.5)) * s.a.y
    const ipx = zoom() / s.px
    const cover = 0.75 * (s.a.x > 1 ? sat((0.4 - abs(d - 1.6)) * ipx + 0.5) : sat((s.a.x - d) * ipx + 0.5))
    return vec4(copperInk() * cover, cover)
  },
)

// Three wanderers creep along the ecliptic, each a small engraved planet with a few dots in its wake.
const wanderers = shapes(
  { count: 6, instances: 3, cover: 0.02 },
  (v, n) => {
    const along = fract(time / [140, 230, 330][n]! + [0.1, 0.815, 0.67][n]!)
    const turn = ECLIPTIC.from - along * ECLIPTIC.span
    const quad = strokeQuad(v, eclipticAt(turn), vec2(sin(turn), -cos(turn)), -50, 18, 16)
    return {
      at: quad.at,
      a: vec4(quad.along, quad.side, n, smoothstep(0, 0.03, along) * (1 - smoothstep(0.97, 1, along))),
    }
  },
  s => {
    // Drawn at 1.8 times the size the numbers below are written in.
    const ipx = (1.8 * zoom()) / s.px
    const x = s.a.x / 1.8
    const y = s.a.y / 1.8
    const r = length(vec2(x, y))
    const kind = floor(s.a.z + 0.5)
    // A ringed one: a disc, and an ellipse that passes behind it.
    const ringed = max(
      sat((3 - r) * ipx + 0.5),
      sat((0.45 - abs(length(vec2(x, y * 2.8)) - 7.2)) * ipx + 0.5) * max(step(3.9, r), step(y, 0)),
    )
    // A crescent: a disc with a bite out of it.
    const crescent = sat((4.2 - r) * ipx + 0.5) * sat((length(vec2(x - 1.9, y - 0.9)) - 3.7) * ipx + 0.5)
    // One with a moon: a small disc, a dotted orbit, and a moon going round it.
    const turn = atan(y, x)
    const moon = max(
      max(sat((2.6 - r) * ipx + 0.5), sat((1 - length(vec2(x - 6.8 * cos(time * 0.7), y - 6.8 * sin(time * 0.7)))) * ipx + 0.5)),
      0.7 * sat((0.45 - length(vec2(abs(fract(turn / (PI / 5) + 0.5) - 0.5) * (PI / 5) * r, r - 6.8))) * ipx + 0.5),
    )
    const body = kind < 0.5 ? ringed : kind < 1.5 ? crescent : moon
    // Dots in its wake, smaller the further back.
    const back = -x - 8.5
    const wake =
      step(0, back) * step(back, 20) * (1 - back / 26) *
      sat((1 - back / 40 - length(vec2((fract(back / 5) - 0.5) * 5, y))) * ipx + 0.5)
    const cover = max(body, wake) * s.a.a * 0.9
    return vec4(copperInk() * cover, cover)
  },
)

// Letters beside the brighter stars, as a star chart names them. Each is three rows on a grid of 4 by 6. A row is a
// stroke from (x, y) to (x, y); or a ring, written as its centre, then its radius as a negative number, then 0;
// or four nines, which is no stroke at all.
const LETTERS = table([
  [0, 0, 2, 3],
  [0.8, 6, 4, 0],
  [9, 9, 9, 9],
  [0, 4.5, 1.8, 0],
  [1.8, 0, 4, 4.5],
  [9, 9, 9, 9],
  [0, 4.6, 4, 4.6],
  [2, 4.6, 2, 0.7],
  [2, 0.7, 3.1, 0],
  [0, 4.6, 4, 4.6],
  [1, 4.6, 0.8, 0],
  [3, 4.6, 3.3, 0],
  [0, 5, 4, 0],
  [4, 5, 0, 0],
  [9, 9, 9, 9],
  [2, 4.6, 2, 0.8],
  [2, 0.8, 3.1, 0],
  [9, 9, 9, 9],
  [2, 2.3, -2, 0],
  [9, 9, 9, 9],
  [9, 9, 9, 9],
  [2, 2, -2, 0],
  [1, 3.8, 3.4, 6],
  [9, 9, 9, 9],
  [0, 4.8, 2, 2],
  [4, 4.8, 2, 2],
  [2, 2, 2, 0],
  [0.6, 4.6, 0.6, 0],
  [3.8, 4.6, 0.6, 2.2],
  [1.7, 2.9, 4, 0],
  [1.9, 2, -1.9, 0],
  [1.9, 3.9, 4, 3.9],
  [9, 9, 9, 9],
])
const letters = shapes(
  { count: 6, instances: 150, cover: 0.05 },
  (v, n) => {
    const i = mod(n, 15) - 1
    const j = floor(n / 15) - 1
    const h3 = weave(weave(int(i), int(j)), 19)
    const h4 = weave(h3, 5)
    const rank = low(h3)
    const tip = rank < 0.16 ? 10.5 : 6.6
    const corner = vec2(ENDS[v]! * 2 - 1, SIDES[v]!) * (vec2(3.8, 5.3) + px / zoom())
    return {
      // Far enough out that a flaring star's strokes stop short of it.
      at: toClip(vec2(starPos(i, j) + vec2(tip + 11.5, -tip * 0.5 - 11.5) + corner)),
      a: vec4(corner, floor(high(h4) * 11), 0),
      hide: rank > 0.58 || (rank > 0.16 && low(h4) > 0.5),
    }
  },
  s => {
    const g = vec2(s.a.xy / 1.5 + vec2(2, 3))
    const id = floor(s.a.z + 0.5)
    // How far this pixel is from the letter's nearest stroke, in grid units.
    let off = 99
    for (const k of [0, 1, 2]) {
      const row = LETTERS.at(id * 3 + k)
      const rel = vec2(g - row.xy)
      // The pixel in the stroke's own frame, as the line quads have it: along the stroke and to its side.
      const run = vec2(row.zw - row.xy)
      const reach = length(run)
      const heading = vec2(run / max(reach, 0.001))
      const along = rel.x * heading.x + rel.y * heading.y
      const side = rel.x * heading.y - rel.y * heading.x
      const stroke = length(vec2(along - clamp(along, 0, reach), side))
      const ring = abs(length(rel) + row.z)
      off = row.x > 8.5 ? off : min(off, row.z < 0 ? ring : stroke)
    }
    const cover = 0.8 * sat(((0.5 - off * 1.5) * zoom()) / s.px + 0.5)
    return vec4(lineInk() * cover, cover)
  },
)

// Hours in Roman numerals where the meridians cross two of the circles. A row is the numeral's strokes
// (base 4, lowest first: 1 an I, 2 a V, 3 an X) and its width.
const NUMERALS = table([
  [1, 2.4],
  [5, 5.6],
  [21, 8.8],
  [9, 7.8],
  [2, 4.6],
  [6, 7.8],
  [22, 11],
  [86, 14.2],
  [13, 7.8],
  [3, 4.6],
  [7, 7.8],
  [23, 11],
  [87, 14.2],
  [39, 13.2],
  [11, 10],
  [27, 13.2],
  [91, 16.4],
  [347, 19.6],
  [55, 13.2],
  [15, 10],
  [31, 13.2],
  [95, 16.4],
  [351, 19.6],
])
const numerals = shapes(
  { count: 6, instances: 46, cover: 0.03 },
  (v, n) => {
    const hour = mod(n, 23) + 1
    const turn = (-hour * PI) / 12
    const radial = vec2(cos(turn), sin(turn))
    const tangent = vec2(-radial.y, radial.x)
    const row = NUMERALS.at(hour - 1)
    const grain = px / zoom()
    // Drawn at 1.35 times the size the strokes are written in.
    const lx = (ENDS[v]! * 2 - 1) * ((row.y * 0.5 + 1.2) * 1.35 + grain)
    const ly = SIDES[v]! * (4.4 * 1.35 + grain)
    const centre = vec2(vec2(W * 0.8, H * 1.32) + radial * ((n < 22.5 ? 800 : 1280) + 15) + tangent * (row.y * 0.675 + 5))
    return { at: toClip(vec2(centre + tangent * lx - radial * ly)), a: vec4(lx / 1.35, ly / 1.35, row.x, row.y) }
  },
  s => {
    const x = s.a.x
    const y = s.a.y
    const half = s.a.a * 0.5
    let pen = -half
    let code = floor(s.a.z + 0.5)
    let d = 99
    for (const k of [0, 1, 2, 3, 4]) {
      const sym = mod(code, 4)
      code = floor(code / 4)
      const wide = sym > 1.5
      // An I is one upright; a V is two strokes to a foot; an X is two that cross.
      const mid = pen + (wide ? 2.3 : 1.2)
      const lean = wide ? 2 : 0
      const foot = sym > 2.5 ? lean : 0
      const t = sat((3 - y) / 6)
      const one = abs(x - (mid - lean + (lean + foot) * t))
      const two = abs(x - (mid + lean - (lean + foot) * t))
      d = sym > 0.5 ? min(d, min(one, two)) : d
      pen += sym > 0.5 ? (wide ? 4.6 : 2.4) + 0.8 : 0
    }
    const ipx = (1.35 * zoom()) / s.px
    const strokes = sat((0.4 - d) * ipx + 0.5) * sat((3 - abs(y)) * ipx + 0.5)
    const bars = sat((0.32 - abs(abs(y) - 3.3)) * ipx + 0.5) * sat((half + 0.7 - abs(x)) * ipx + 0.5)
    const cover = 0.7 * max(strokes, bars)
    return vec4(arcInk() * cover, cover)
  },
)

// A few clusters, marked the way a star chart marks them: a dashed circle with a handful of dots inside.
const CLUSTER = [[0, 0.4], [3.4, 1.6], [-2.6, 3.1], [-3, -2.6], [2.1, -3.6], [0.3, 4.6]]
const clusters = shapes(
  { count: 6, instances: 24, cover: 0.02 },
  (v, n) => {
    const i = mod(n, 6)
    const j = floor(n / 6)
    const h = weave(int(int(i) + 73), int(int(j) + 401))
    const turn = low(h) * 40
    const corner = vec2(vec2(ENDS[v]! * 2 - 1, SIDES[v]!) * (10 + px / zoom()))
    const at = vec2((i + 0.15 + 0.7 * low(h)) * 270, (j + 0.15 + 0.7 * high(h)) * 260)
    // A mark that would sit on a star is left out.
    let clear = 1e4
    for (const oy of [-1, 0, 1]) {
      for (const ox of [-1, 0, 1]) {
        clear = min(clear, length(vec2(starPos(floor(at.x / CELL) + ox, floor(at.y / CELL) + oy) - at)))
      }
    }
    return {
      at: toClip(vec2(at + corner)),
      a: vec4(corner.x * cos(turn) + corner.y * sin(turn), corner.y * cos(turn) - corner.x * sin(turn), 0, 0),
      hide: fract(high(h) * 5.7) > 0.4 || clear < 32,
    }
  },
  s => {
    const ipx = zoom() / s.px
    const r = length(s.a.xy)
    let cover = sat((0.4 - abs(r - 8.5)) * ipx + 0.5) * step(abs(fract(atan(s.a.y, s.a.x) / (PI / 6)) - 0.5), 0.3)
    for (const d of CLUSTER) cover = max(cover, sat((0.85 - length(vec2(s.a.xy - vec2(d[0]!, d[1]!)))) * ipx + 0.5))
    return vec4(lineInk() * cover * 0.8, cover * 0.8)
  },
)

// Pressing sets a pair of dividers down: a graduated copper circle about the pointer, inked over the first half second of the press.
const dividers = shapes(
  { count: 6, instances: 4, cover: 0.09 },
  (v, n) => {
    const f = pointer(n)
    const w = f.down * hold(f) * step(n + 0.5, pointerCount) * smoothstep(0.1, 0.5, f.age)
    const corner = vec2(ENDS[v]! * 2 - 1, SIDES[v]!) * (67 + px / zoom())
    return { at: toClip(vec2(toChart(f.at) + corner)), a: vec4(corner, w, 0), hide: w < 0.004 }
  },
  s => {
    const ipx = zoom() / s.px
    const r = length(s.a.xy)
    const turn = atan(s.a.y, s.a.x)
    const circle = sat((0.4 - abs(r - 58)) * ipx + 0.5)
    const isLong = step(abs(fract(turn / (PI / 4) + 0.5) - 0.5) * (PI / 4) * r, 1.5)
    const ticks =
      sat((0.4 - abs(fract(turn / (PI / 12) + 0.5) - 0.5) * (PI / 12) * r) * ipx + 0.5) * step(58, r) * step(r, 61.5 + 3.5 * isLong)
    const stipple = 0.8 * sat((0.7 - length(vec2(abs(fract(turn / (PI / 30) + 0.5) - 0.5) * (PI / 30) * r, r - 51))) * ipx + 0.5)
    const cover = s.a.z * 0.8 * max(circle, max(ticks, stipple))
    return vec4(copperInk() * cover, cover)
  },
)

// Two faint shooting specks, each a head with a short row of dots left on its path, gone in a breath.
const sparks = shapes(
  { count: 6, instances: 2, cover: 0.01 },
  (v, n) => {
    const every = [4.7, 7.3][n]!
    const tt = time + [2.2, 4.1][n]!
    const turn = floor(tt / every)
    const tau = tt - turn * every
    const h = weave(int(turn), int(n * 31 + 7))
    const h2 = weave(h, 3)
    const heading = -PI / 2 + (low(h2) - 0.5) * 2.2
    const uh = 90 * tau
    const quad = strokeQuad(v, inView(vec2(0.03 + 0.94 * low(h), 0.2 + 0.8 * high(h))), vec2(cos(heading), sin(heading)), uh - 46, uh + 3, 2)
    const life = sin(PI * sat(tau / 1.3))
    return { at: quad.at, a: vec4(uh - quad.along, quad.side, life, quad.along), hide: life < 0.01 }
  },
  s => {
    const ipx = zoom() / s.px
    const back = s.a.x
    // The dots stay where they were left and shrink as the head moves on.
    const dots =
      sat((1.2 * (1 - back / 46) - length(vec2((fract(s.a.a / 6) - 0.5) * 6, s.a.y))) * ipx + 0.5) * step(2, back) * step(0, s.a.a)
    const head = sat((1.3 - length(vec2(back, s.a.y))) * ipx + 0.5)
    const cover = max(dots, head) * s.a.z * 0.8
    return vec4(starInk() * cover, cover)
  },
)

export default shader({
  fps: 60,
  passes: [plate, glow, ground, numerals, ecliptic, specks, clusters, figureLines, letters, wanderers, threadLinks, fanLines, dividers, starGlyphs, sparks, meteor],
})
