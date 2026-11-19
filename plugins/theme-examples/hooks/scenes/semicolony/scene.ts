// semicolony: a 1-bit specimen sheet where code punctuation lives as small creatures.
// Three passes: where the loupes have rested, the sheet drawn small (one texel per art pixel, 4 points wide), and the picture,
// which reads both and lays the ink and the sheet's faint printing over the paper colour it finds in the Svg.
import {
  abs, atan, buffer, clamp, dot, dt, exp, floor, fract, int, length, max, min, mix, mod, picture, pointers, px, range, res, scene, shader, sign, signed, sin, size, smoothstep, step, still, time, vec2, vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

// An integer mixer of this file's own: two whole numbers in, 32 scrambled bits out.
const scramble = (a: number, b: number) => {
  let h = int(int(a) * 3471823 + int(b) * 5908417 + 733)
  h = int(h ^ (h >>> 17))
  h = int(h * 93827461)
  h = int(h ^ (h >>> 11))
  h = int(h * 2753197)
  h = int(h ^ (h >>> 14))
  return h
}
// Eight bits of a scramble as a number from 0 to 1.
const part = (h: number, shift: number) => signed(int((int(h) >>> shift) & 255)) / 256
// 1 where a whole number equals another.
const is = (x: number, y: number) => step(abs(x - y), 0.25)
// 1 where low <= x <= high, for whole numbers.
const within = (x: number, low: number, high: number) => step(low - 0.25, x) * step(x, high + 0.25)

// The clock starts here, at a moment whose first frame is well composed: the Svg shows that frame.
const START = 147

// This pass remembers where a loupe has rested. Red: how long each art pixel has lain under a loupe lately. Green:
// whether it is in focus. Blue: how much of a loupe's rim it carries this frame. An art pixel comes into focus after
// about a third of a second under glass and leaves focus about four tenths of a second after the glass has gone.
// Those two waits keep the focus itself from switching any spot more than three times in a second, however the pointer is shaken.
const dwell: Buffer = buffer({ scale: 0.25, filter: 'nearest' }, (p): vec4 => {
  const cellX = floor(p.pixel.x)
  const cellY = floor(p.pixel.y)
  let under = 0
  let rim = 0
  for (const finger of pointers) {
    // A loupe opens as its pointer arrives. After a hover leaves it lingers a moment before it closes; after a press
    // lifts it closes within a fifth of a second.
    const w = clamp(finger.age * 3.3, 0, 1) * (1 - smoothstep(0.35 * (1 - finger.down), 1 - 0.8 * finger.down, finger.gone))
    const overX = p.pixel.x - finger.at.x * res.x / size.x
    const overY = p.pixel.y - finger.at.y * res.y / size.y
    const away = length(vec2(overX, overY))
    // The disc opens from nothing and closes to nothing; at rest its radius is 88 points.
    const reach = 22 * (1 - (1 - w) * (1 - w))
    under = max(under, step(away, reach) * step(0.02, w))
    // The rim: a ring one art pixel wide of beads, two on and two off, that step round it, and four ticks that point
    // in at the middle and are longer while the pointer is pressed.
    const beads = abs(overX) > abs(overY) ? cellY * sign(overX) : -cellX * sign(overY)
    const ring = step(abs(away - reach + 0.5), 0.5) * step(mod(beads + floor(time * 2.5), 4), 1.5)
    const ticks = max(is(floor(overX), 0), is(floor(overY), 0)) * step(reach - 4 - 3 * finger.down, away) * step(away, reach)
    rim = max(rim, max(ring, ticks) * w)
  }
  const was = dwell.at(p.cell)
  // The count runs fast below three tenths and above seven, and slowly between them: 0.32 s to climb the middle, 0.4 s to fall.
  const climbed = was.r < 0.295 ? min(0.302, was.r + dt * 6) : (was.r < 0.695 ? min(0.702, was.r + dt * 1.25) : min(1, was.r + dt * 6))
  const fallen = was.r > 0.71 ? max(0.702, was.r - dt * 6) : (was.r > 0.31 ? max(0.302, was.r - dt) : max(0, was.r - dt * 6))
  const filled = under > 0.5 ? climbed : fallen
  // Focus switches on at the top of the middle and off at the bottom, and keeps its last answer in between.
  const focus = filled >= 0.7 ? 1 : (filled <= 0.305 ? 0 : step(0.5, was.g))
  return vec4(filled, focus, rim, 1)
})

// 1 where the sheet is in focus at a place given in points.
const big = (atX: number, atY: number): number => step(0.5, dwell.sample(vec2(atX / size.x, atY / size.y)).g)
// A creature that grows in focus is drawn at twice its size: this turns a distance in art pixels into one in the creature's own pixels.
const near = (d: number, grown: number): number => floor(d / (1 + grown))

// The sheet itself: a small 1-bit frame, one texel for each art pixel of 4 points. It keeps nothing from frame to frame;
// it is drawn small so that every creature is worked out once per art pixel, not once per screen pixel.
// Red holds ink (a half for ink that shows only in focus), green which creature the ink belongs to, blue the sheet's
// faint printing, alpha whether that creature is drawn in focus.
const art = buffer({ scale: 0.25, filter: 'nearest' }, p => {
  // Under Reduce Motion the sheet stays at the first frame, the one the Svg shows.
  const now = time * (1 - still) + START
  const a = px
  const qx = floor(p.pixel.x)
  const qy = floor(p.pixel.y)
  const atX = (qx + 0.5) * a
  const atY = (qy + 0.5) * a

  let ink = 0
  let kind = 0
  // Ink that shows only where the sheet is in focus.
  let hidden = 0
  // Whether the ink here belongs to a creature that is drawn in focus: such a creature is coloured all over.
  let tinted = 0
  const put = (on: number, id: number, grown: number) => {
    ink = max(ink, on)
    kind = mix(kind, id, on)
    tinted = mix(tinted, grown, on)
  }

  // Brace jellies rise in the gutters, opening and closing.
  {
    const lane = floor(atX / 168 + 0.5)
    const laneHash = scramble(lane, 7)
    const rise = now * (5 + 4 * part(laneHash, 0)) + 470 * part(laneHash, 8)
    const cell = floor((atY - rise) / 470)
    const h = scramble(lane, cell + 288)
    const beat = now / (2.4 + part(h, 0)) + part(h, 8)
    const swell = sin(6.2832 * beat)
    const cx = lane * 168 + 3 * sin(now * 0.31 + 6 * part(h, 16))
    const cy = (cell + 0.3 + 0.4 * part(h, 16)) * 470 + rise + 3 * sin(6.2832 * beat - 1.2)
    const grown = big(cx, cy + 20)
    const lx = near(qx - floor(cx / a), grown) + 0.5
    const ly = near(qy - floor(cy / a), grown)
    const half = floor(2.2 + 1.2 * swell)
    const col = abs(lx) - 0.5 - half
    const row = min(ly, 10 - ly)
    // The brace, drawn once: six rows of four, mirrored top to bottom and left to right.
    const bits = int(3 + 4 * 16 + 4 * 256 + 4 * 4096 + 4 * 65536 + 8 * 1048576)
    let body = 0
    if (col >= 0 && col < 4 && row >= 0) {
      body = signed(int((bits >>> int(row * 4 + col)) & 1))
    }
    const blink = step(fract(now * 0.23 + part(h, 24)), 0.95)
    const eyes = is(ly, 5) * (is(abs(lx), 1.5) * step(1.5, half) * blink + is(abs(lx), 0.5) * step(half, 1.5))
    // Three dotted strands trail below and sway.
    const depth = -1 - ly
    const sway = floor(sin(now * 1.6 + depth * 0.7 + 6 * part(h, 24)) * depth * 0.22 + 0.5)
    const sx = lx - 0.5 - sway
    const strand = within(depth, 1, 7 - 2 * step(1, abs(sx))) * is(fract(depth * 0.5), 0.5) * (is(sx, 0) + is(abs(sx), 3))
    // Two bubbles leave on each beat.
    let fizz = 0
    for (const side of [-1, 1]) {
      const u = fract(beat + 0.25 * side)
      const far = abs(ly - 12 - floor(u * 18)) + abs(lx - 0.5 - side * 2 - floor(sin(u * 9 + side) + 0.5))
      fizz = max(fizz, is(far, 0) * step(u, 0.8) + is(far, 1) * step(0.8, u) * step(u, 0.88))
    }
    const alive = step(part(h, 4), 0.02 + 1.25 * abs(lane * 168 / size.x - 0.5)) * step(40, lane * 168) * step(lane * 168, size.x - 40)
    put(body * alive, 1, grown)
    put(eyes * alive, 0, grown)
    put(strand * alive, 6, grown)
    put(fizz * alive, 6, grown)
  }

  // Semicolon tadpoles climb on a slant in loose schools, tails wriggling.
  {
    const u = atX * 0.6 + atY * 0.8
    const v = atX * 0.8 - atY * 0.6
    const lane = floor(v / 250)
    const laneHash = scramble(lane, 91)
    const run = now * (9 + 5 * part(laneHash, 0)) + 560 * part(laneHash, 8)
    const cell = floor((u - run) / 560)
    const h = scramble(lane, cell + 323)
    const uc = (cell + 0.35 + 0.3 * part(h, 4)) * 560 + run
    const vc = (lane + 0.3 + 0.4 * part(h, 0)) * 250
    const sx = 0.6 * uc + 0.8 * vc
    const sy = 0.8 * uc - 0.6 * vc
    const alive = step(part(h, 8), 0.4)
    const count = 2 + floor(part(h, 16) * 2.99)
    for (const [i, ox, oy] of [[0, 0, 0], [1, -28, -20], [2, 22, -34], [3, -6, -56]] as const) {
      const ph = part(h, 24) * 6 + i * 1.9
      const cx = sx + ox + 4 * sin(now * 0.7 + ph)
      const cy = sy + oy + 3 * sin(now * 0.9 + ph * 1.3)
      const grown = big(cx + 4, cy + 16)
      const lx = near(qx - floor(cx / a), grown)
      const ly = near(qy - floor(cy / a), grown)
      const wide = within(lx, 0, 1)
      const d = 3 - ly
      const tx = floor(1 - 0.34 * d + 0.45 * d * sin(now * 3.4 + ph - d * 1.1) + 0.5)
      const tail = within(ly, 0, 2) * is(lx, tx)
      const body = max(wide * (within(ly, 6, 7) + within(ly, 3, 4)), tail)
      const b = fract(now * 0.3 + ph)
      const fizz = is(ly, 10 + floor(b * 12)) * is(lx, -2 - floor(b * 3)) * step(b, 0.7)
      const there = alive * step(i, count - 0.5)
      put(body * there, 2, grown)
      put(fizz * there, 6, grown)
    }
  }

  // Arrow darters cross the sheet in darts and rests, stretching while they dart.
  {
    const lane = floor(atY / 189)
    const laneHash = scramble(lane, 17)
    const dir = part(laneHash, 0) < 0.5 ? -1 : 1
    const beat = now / 3.4 + part(laneHash, 8)
    const f = fract(beat)
    const slow = 1 - min(f / 0.38, 1)
    const run = dir * 96 * (floor(beat) + 1 - slow * slow * slow) + 700 * part(laneHash, 16)
    const cell = floor((atX - run) / 700)
    const h = scramble(cell, lane + 500)
    const cx = (cell + 0.3 + 0.4 * part(h, 0)) * 700 + run
    const cy = (lane + 0.5) * 189
    const grown = big(cx - dir * 12, cy)
    const lx = near((qx - floor(cx / a)) * dir, grown)
    const ry = near(qy - floor(cy / a), grown)
    const ly = abs(ry)
    const fast = step(f, 0.22)
    const fat = step(0.5, part(h, 16))
    const head = is(lx + ly, 0) * step(ly, 2.25 + fat)
    const len = 5 + fat + 3 * fast
    const onShaft = is(ly, fat)
    const shaft = onShaft * within(lx, -len, -1 - fat)
    const flick = step(0.5, fract(now * 0.9 + part(h, 4))) * (1 - fast)
    const fin = is(lx, -len - 1) * is(ly, fat + 1) + flick * is(lx, -len - 2) * is(ly, fat + 2)
    const streak = fast * onShaft * (within(lx, -len - 5, -len - 4) + is(lx, -len - 8))
    const b = fract(now * 0.37 + part(h, 4))
    const fizz = is(ry, 3 + floor(b * 11)) * is(lx, -len - floor(b * 5)) * step(b, 0.7)
    const alive = step(part(h, 24), 0.55) * step(0.3, part(laneHash, 24))
    put(max(max(head, fin), max(shaft, streak)) * alive, 3, grown)
    put(fizz * alive, 6, grown)
  }

  // Tilde eels: a slow travelling wave of pixels, on the baselines the arrows leave free.
  {
    const lane = floor(atY / 189)
    const laneHash = scramble(lane, 17)
    const dir = part(laneHash, 0) < 0.5 ? 1 : -1
    const run = dir * now * (5 + 3 * part(laneHash, 8)) + 1100 * part(laneHash, 16)
    const cell = floor((atX - run) / 1100)
    const h = scramble(cell, lane + 700)
    const cx = (cell + 0.3 + 0.4 * part(h, 0)) * 1100 + run
    const cy = (lane + 0.5) * 189
    const grown = big(cx - dir * 30, cy)
    const lx = near((qx - floor(cx / a)) * dir, grown)
    const ly = near(qy - floor(cy / a), grown)
    const wave = floor(1.45 * sin(lx * 0.62 + now * 2.2 + 6 * part(h, 16)) + 0.5)
    const body = is(ly, wave) * within(lx, -15, 0)
    const head = is(ly, wave + 1) * within(lx, -1, 0)
    const alive = step(part(h, 24), 0.6) * step(part(laneHash, 24), 0.3)
    const b = fract(now * 0.33 + part(h, 4))
    const fizz = is(ly, 4 + floor(b * 9)) * is(lx, 1 - floor(b * 4)) * step(b, 0.7)
    put(max(body, head) * alive, 4, grown)
    put(fizz * alive, 6, grown)
  }

  // Plus-sign stars sit on the register crosses and turn to a times sign and back, with a sparkle at each turn.
  {
    const cxi = floor(atX / 168)
    const cyi = floor(atY / 189)
    const h = scramble(cxi, cyi + 929)
    const cx = (cxi + 0.5) * 168
    const cy = (cyi + 0.5) * 189
    const grown = big(cx, cy)
    const lx = abs(near(qx - floor(cx / a), grown))
    const ly = abs(near(qy - floor(cy / a), grown))
    const turn = step(0.5, fract(now * 0.17 + part(h, 16)))
    const far = max(lx, ly)
    const plus = is(min(lx, ly), 0)
    const cross = is(lx, ly)
    const spark = step(fract(2 * (now * 0.17 + part(h, 16))), 0.1)
    const on = mix(plus, cross, turn) * (step(far, 2.25) + spark * is(far, 4))
    put(min(on, 1) * step(part(h, 0), 0.1), 5, grown)
  }

  // Loose bubbles: single pixels rising everywhere, slowly.
  {
    const lane = floor(atX / 84)
    const laneHash = scramble(lane, 29)
    const rise = now * (4 + 5 * part(laneHash, 0)) + 90 * part(laneHash, 8)
    const cell = floor((atY - rise) / 90)
    const h = scramble(lane, cell + 1300)
    const cx = (lane + 0.15 + 0.7 * part(h, 0)) * 84 + 3 * sin(now * 0.8 + 6 * part(h, 8))
    const cy = (cell + 0.5) * 90 + rise
    put(is(qx, floor(cx / a)) * is(qy, floor(cy / a)) * step(part(h, 16), 0.24), 6, 0)
  }

  // Pipe sea fern grows from the ruler at the foot of the sheet, taller toward the sheet's edges, and sways.
  {
    const lane = floor(atX / 28)
    const h = scramble(lane, 2100)
    const edge = abs((lane + 0.5) * 28 / size.x - 0.5) * 2
    const tall = floor((4 + 20 * part(h, 0)) * (0.3 + 0.7 * edge * edge))
    const up = qy - 3
    const lean = floor(sin(now * 0.7 + 6 * part(h, 8) + up * 0.16) * up * 0.09 + 0.5)
    const lx = qx - floor(((lane + 0.5) * 28 + 6 * (part(h, 16) - 0.5)) / a) - lean
    // Stacked pipes: three pixels of stalk, one of gap, and a loose tip.
    const bud = is(mod(up, 4), 3) * is(lx, mod(up, 8) < 4 ? 1 : -1) * within(up, 3, tall - 1)
    const stalk = is(lx, 0) * within(up, 0, tall) * (1 - is(mod(up, 4), 3)) + is(lx, 0) * is(up, tall + 2) + bud
    put(min(stalk, 1) * step(part(h, 24), 0.25 + 0.45 * edge), 4, 0)
  }

  // At-sign snails creep along the ruler, feelers waving, three dots of trail behind.
  {
    const run = now * 2.2
    const cell = floor((atX - run) / 540)
    const h = scramble(cell, 2469)
    const cx = (cell + 0.2 + 0.6 * part(h, 0)) * 540 + run
    const grown = big(cx, 24)
    const lx = near(floor(cx / a) - qx, grown) + 4
    const ly = near(qy - 3, grown)
    // The shell is six rows of six; then come the foot and the head.
    const rows = [30, 33, 45, 41, 57, 62]
    let shell = 0
    if (lx >= 0 && lx < 6 && ly >= 0 && ly < 6) {
      shell = signed(int((int(rows[5 - ly]!) >>> int(lx)) & 1))
    }
    const foot = is(ly, 0) * within(lx, -4, -1) + is(ly, 1) * is(lx, -4)
    const wave = step(0.5, fract(now * 0.9 + part(h, 8)))
    const feelers = is(lx, -5) * is(ly, 2 + wave) + is(lx, -3) * is(ly, 3 - wave)
    const trail = is(ly, 0) * within(lx, 8, 12) * is(mod(lx, 2), 0)
    put(min(shell + foot + feelers + trail, 1) * step(part(h, 16), 0.6), 7, grown)
  }

  // Question-mark seahorses hang in the lower water, bobbing, a fin flickering at the back.
  {
    const cxi = floor(atX / 216)
    const h = scramble(cxi, 2520)
    const edge = abs((cxi + 0.5) * 216 / size.x - 0.5) * 2
    const cx = (cxi + 0.25 + 0.5 * part(h, 0)) * 216 + 3 * sin(now * 0.4 + 6 * part(h, 8))
    const cy = 70 + 150 * part(h, 16) + 7 * sin(now * 0.9 + 6 * part(h, 8))
    const grown = big(cx + 12, cy + 20)
    const lx = near(qx - floor(cx / a), grown)
    const ly = near(qy - floor(cy / a), grown)
    // A question mark drawn as a seahorse: crest, snout, long neck, belly. Eight rows of six, never mirrored,
    // so that it stays a question mark.
    const rows = [8, 24, 8, 16, 32, 35, 18, 12]
    let body = 0
    if (lx >= 0 && lx < 6 && ly >= 2 && ly < 10) {
      body = signed(int((int(rows[ly - 2]!) >>> int(lx)) & 1))
    }
    // Its dot is a curled tail tip that flicks, and a fin flickers behind the neck.
    const flick = step(0.5, fract(now * 0.45 + part(h, 8)))
    const tail = is(ly, 0) * within(lx, 2 + flick, 3 + flick)
    const fin = is(lx, 6) * is(ly, 5 + step(0.5, fract(now * 0.9 + part(h, 8))))
    const b = fract(now * 0.28 + part(h, 24))
    const fizz = is(lx, -2 - floor(b * 2)) * is(ly, 9 + floor(b * 12)) * step(b, 0.75)
    const alive = step(part(h, 12), 0.15 + 0.6 * edge)
    put(min(body + tail + fin, 1) * alive, 3, grown)
    put(fizz * alive, 6, grown)
  }

  // Plankton: small swarms of single pixels, each mote circling its own spot in the swarm.
  {
    const lane = floor(atY / 270)
    const laneHash = scramble(lane, 2700)
    const run = now * (2 + 3 * part(laneHash, 0)) * (part(laneHash, 4) < 0.5 ? -1 : 1) + 400 * part(laneHash, 8)
    const cell = floor((atX - run) / 400)
    const h = scramble(cell, lane + 2800)
    const cx = (cell + 0.3 + 0.4 * part(h, 0)) * 400 + run
    const cy = (lane + 0.3 + 0.4 * part(h, 8)) * 270 + 10 * sin(now * 0.23 + 6 * part(h, 16))
    // Each swarm has the same loose shape, flipped and scaled.
    const spread = (part(h, 4) < 0.5 ? -1 : 1) * (0.7 + 0.5 * part(h, 12))
    let motes = 0
    for (const i of range(9)) {
      const swing = now * (0.9 - 0.06 * i) + i * 2.4 + 6 * part(h, 16)
      const mx = cx + spread * 30 * sin(i * 2.4) + 6 * sin(swing + 1.571)
      const my = cy + spread * 20 * sin(i * 1.7 + 2) + 5 * sin(swing)
      motes = max(motes, is(qx, floor(mx / a)) * is(qy, floor(my / a)))
    }
    put(motes * step(part(h, 24), 0.55), 6, 0)
  }

  // Colon fry: shoals of small colons in a loose wavering line.
  {
    const lane = floor(atY / 236)
    const laneHash = scramble(lane, 3100)
    const dir = part(laneHash, 0) < 0.5 ? -1 : 1
    const run = dir * now * (7 + 3 * part(laneHash, 8)) + 700 * part(laneHash, 16)
    const cell = floor((atX - run) / 700)
    const h = scramble(cell, lane + 3200)
    const cx = (cell + 0.3 + 0.4 * part(h, 0)) * 700 + run
    const cy = (lane + 0.5) * 236 + 60 * (part(h, 8) - 0.5)
    let shoal = 0
    for (const i of range(7)) {
      const fx = cx - dir * i * 14
      const fy = cy + 7 * sin(now * 1.3 + i * 0.8 + 6 * part(h, 16)) + 5 * mod(i, 2)
      const ly = qy - floor(fy / a)
      shoal = max(shoal, is(qx, floor(fx / a)) * (is(ly, 0) + is(ly, 2)))
    }
    put(shoal * step(part(h, 24), 0.5), 2, 0)
  }

  // The queen: a semicolon set at a larger size and crowned, climbing slowly on the same slant as the schools.
  // Queens are rare: the sheet seldom holds more than one.
  {
    const u = atX * 0.6 + atY * 0.8
    const v = atX * 0.8 - atY * 0.6
    const lane = floor(v / 520)
    const run = now * 6 + 4000 * part(scramble(lane, 4355), 8)
    const cell = floor((u - run) / 4000)
    const h = scramble(lane, cell + 4200)
    const uc = (cell + 0.5) * 4000 + run
    const vc = (lane + 0.3 + 0.4 * part(h, 0)) * 520
    const lx = qx - floor((0.6 * uc + 0.8 * vc + 5 * sin(now * 0.5)) / a)
    const ly = qy - floor((0.8 * uc - 0.6 * vc) / a)
    // Head and body are two rings with a row between them; the head has an eye.
    const rings = step(abs(length(vec2(lx - 4, ly - 19)) - 3), 0.55) + step(abs(length(vec2(lx - 4, ly - 11)) - 3), 0.55)
    const eye = is(lx, 5) * is(ly, 20)
    // The tail is two pixels thick and waves more toward its tip.
    const d = 8 - ly
    const tx = floor(4 - 0.3 * d + 0.3 * d * sin(now * 2.4 - d * 0.6) + 0.5)
    const tail = within(ly, 0, 7) * within(lx - tx, 0, 1)
    const crown = is(ly, 23) * within(lx, 2, 6) + is(ly, 24) * within(lx, 2, 6) * is(mod(lx, 2), 0)
    const b = fract(now * 0.25 + part(h, 8))
    const fizz = is(lx, -2 - floor(b * 3)) * is(ly, 24 + floor(b * 14)) * step(b, 0.75)
    const alive = step(part(h, 16), 0.8)
    put(min(rings + eye + tail, 1) * alive, 2, 0)
    put(min(crown, 1) * alive, 1, 0)
    put(fizz * alive, 6, 0)
  }

  // Caret moths: small life seen only where the sheet is in focus, one to each patch of the sheet, so that a loupe
  // seldom finds none. Each flaps between a caret and its upside-down and wanders its patch, drawn at twice its size.
  {
    const cxi = floor(atX / 100)
    const cyi = floor(atY / 100)
    const h = scramble(cxi, cyi + 5100)
    const cx = (cxi + 0.5) * 100 + 30 * sin(now * 0.21 + 6 * part(h, 0))
    const cy = (cyi + 0.5) * 100 + 30 * sin(now * 0.17 + 6 * part(h, 8))
    const lx = near(qx - floor(cx / a), 1)
    const ly = near(qy - floor(cy / a), 1)
    const flap = step(0.5, fract(now * 0.8 + part(h, 16)))
    hidden = within(ly, 0, 1) * is(abs(lx), mix(1 - ly, ly, flap))
  }

  // A press sends a ring of eight bubbles outward from the pointer; they slow, and pop.
  {
    let burst = 0
    for (const finger of pointers) {
      const reach = 5 + 22 * (1 - exp(-2.2 * finger.age))
      const fx = finger.at.x * res.x / size.x
      const fy = finger.at.y * res.y / size.y
      const live = finger.down * step(finger.age, 1)
      // Each bubble keeps to its own eighth of the circle, so only the one on this side needs looking at.
      const i = mod(floor(atan(qy + 0.5 - fy, qx + 0.5 - fx) / 0.7854 + 0.5), 8)
      const turn = i * 0.7854 + 0.3 * sin(i * 5.1)
      const out = reach * (1 + 0.14 * sin(i * 3.3))
      const far = abs(qx - floor(fx + out * sin(turn + 1.571))) + abs(qy - floor(fy + out * sin(turn)))
      burst = max(burst, live * (is(far, 0) * step(finger.age, 0.85) + is(far, 1) * step(0.85, finger.age)))
    }
    put(burst, 6, 0)
  }

  // The sheet's printing: dotted gutter rules, dotted baselines, a register cross in each column, a tally on each baseline.
  const gx = floor(abs(atX - floor(atX / 168 + 0.5) * 168) / a) - floor(36 / a)
  const gy = qy - floor((floor(atY / 189) + 0.5) * 189 / a)
  const dotted = is(fract((qx + qy) * 0.5), 0)
  const rule = min(is(gx, 0) * dotted + is(gy, 0) * dotted * is(fract(qx * 0.25), 0), 1)
  const ux = qx - floor((floor(atX / 168) + 0.5) * 168 / a)
  const cross = step(abs(ux), 1.25) * step(abs(gy), 1.25) * max(is(ux, 0), is(gy, 0))
  const count = mod(floor(atY / 189), 5) + 1
  const tally = within(qx, 3, 1 + 2 * count) * is(fract(qx * 0.5), 0.5) * within(gy, 2, 4)
  // The foot of the sheet is a ruler: a line, a tick every third pixel, a longer one every fifteenth.
  const ruler = is(qy, 2) + is(mod(qx, 3), 0) * within(qy, 0, 1) * step(1, qy + is(mod(qx, 15), 0))
  // Above the ruler lies a little silt, shaded the 1-bit way: an ordered scatter of dots that thins as it rises.
  const silt = within(qy, 3, 12) * step(mod(qx * 5 + qy * 3, 8) + 0.5, 7 - 0.75 * qy) * 0.5
  // Nothing swims over the ruler. Full ink is seen always; half ink is the life that only a place in focus shows.
  const open = step(2.5, qy)
  const veiled = hidden * (1 - ink) * open
  return vec4(ink * open + 0.5 * veiled, mix(kind, 5, veiled) / 8, max(max(0.5 * rule, silt), max(max(cross, tally), min(ruler, 1))), tinted)
})

const sheet = picture(p => {
  // Where this picture pixel is on the sheet, in art pixels.
  const spotX = p.uv.x * art.size.x
  const spotY = p.uv.y * art.size.y
  const lens = dwell.sample(p.uv)
  const glass = step(0.5, lens.g)
  const rim = lens.b
  const seen = art.sample(p.uv)
  // Full ink shows everywhere; half ink is the life that only a place in focus shows.
  const ink = seen.r > 0.75 ? 1 : (seen.r > 0.25 ? glass : 0)
  const kind = floor(seen.g * 8 + 0.5)
  const print = seen.b

  // The palette follows the paper of the Svg, read just off the sheet's middle. In a 1512 by 945 window that spot
  // is 22 of the Svg's units right of its centre and 24 above; in a wider or taller window it slides toward one axis or the other,
  // and the Svg keeps every spot it can slide to bare.
  const paper = vec3(scene.sample(vec2(0.5146, 0.5254)).rgb)
  const day = step(0.4, dot(paper, vec3(0.3, 0.6, 0.1)))
  const inkTone = vec3(mix(vec3(0.66, 0.69, 0.76), vec3(0.3, 0.32, 0.4), day))
  // In focus each creature takes its syntax colour.
  let hue = inkTone
  if (kind > 0.5) hue = vec3(mix(vec3(0.9, 0.76, 0.42), vec3(0.6, 0.42, 0.04), day))
  if (kind > 1.5) hue = vec3(mix(vec3(0.93, 0.56, 0.7), vec3(0.72, 0.22, 0.42), day))
  if (kind > 2.5) hue = vec3(mix(vec3(0.45, 0.8, 0.88), vec3(0.05, 0.45, 0.58), day))
  if (kind > 3.5) hue = vec3(mix(vec3(0.6, 0.84, 0.52), vec3(0.22, 0.5, 0.16), day))
  if (kind > 4.5) hue = vec3(mix(vec3(0.74, 0.64, 0.96), vec3(0.45, 0.3, 0.75), day))
  if (kind > 5.5) hue = vec3(mix(vec3(0.62, 0.8, 0.95), vec3(0.26, 0.42, 0.62), day))
  if (kind > 6.5) hue = vec3(mix(vec3(0.95, 0.62, 0.4), vec3(0.72, 0.36, 0.1), day))
  // Ink is coloured where the sheet is in focus, and all over a creature that is drawn in focus, even where it pokes out.
  const tone = vec3(mix(inkTone, hue, max(glass, step(0.5, seen.a))))

  // In focus the sheet also shows its pixel grid, one faint dot at each art pixel's corner.
  const grid = glass * step(fract(spotX), 0.25) * step(fract(spotY), 0.25)
  // On light paper the loupe's own marks are drawn fainter: a mark that follows the pointer must not change a spot's brightness much.
  const faint = 0.13 * step(0.25, print) + 0.09 * step(0.75, print) + (0.12 - 0.02 * day) * grid + (0.24 - 0.1 * day) * rim
  const ground = vec3(mix(paper, inkTone, faint))
  return vec4(vec3(mix(ground, tone, ink)), 1)
})

export default shader({ fps: 60, passes: [dwell, art, sheet] })
