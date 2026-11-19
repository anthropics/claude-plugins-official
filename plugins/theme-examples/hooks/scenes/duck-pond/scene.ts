// Duck Pond. Chunky four-colour pixel art with ordered dither: rubber ducks and their ducklings on flat dithered water.
//
// How the picture is made. Everything is drawn on a coarse grid of "art pixels", six points square, so the pixel art
// is real and not a filter. Four passes run each frame:
//   flock  8 x 3 texels. Each column is one duck: where it is, how fast it goes, which way it faces, what it is after.
//   pond   one texel an art pixel. A small wave field: ducks and pointers push on it and its rings travel and fade.
//   art    one texel an art pixel. The finished pixel art: four colours, and a dot of dark ink for each eye.
//   view   the picture. It shows the art and rules a faint display grid over it.
// The still Svg under the shader is the same pond at rest. The shader paints every pixel, so none of the Svg shows
// through; the shader reads one spot of it to learn whether the window is light or dark.
//
// Units: positions are in art pixels ("cells") from the bottom left, y up.
import {
  PI, abs, buffer, clamp, cos, dot, dt, exp, first, floor, fract, int, length, max, min, mix, picture, pointers, range,
  res, scene, shader, sign, signed, sin, size, smoothstep, step, table, time, vec2, vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

// Points in one art pixel.
const CELL = 6
const DUCKS = 8

// One row a duck: who it follows (-1 for a grown duck, who leads), then its home as a share of the pond, then a phase
// that keeps the ducks out of step with each other. Rows 0 to 2 are the grown ducks.
const KIN = table([
  [-1, 0.183, 0.494, 0],
  [-1, 0.5, 0.83, 5.03],
  [-1, 0.792, 0.587, 2.5],
  [0, 0.135, 0.494, 1.3],
  [3, 0.099, 0.494, 3.3],
  [4, 0.063, 0.494, 5.2],
  [2, 0.873, 0.582, 0.7],
  [6, 0.909, 0.582, 2.9],
])

// Lily pads: centre as a share of the pond, which sprite (0 big, 1 small), and whether it carries a flower.
const PADS = [
  [0.115, 0.15, 0, 1],
  [0.2, 0.075, 1, 0],
  [0.925, 0.88, 0, 1],
  [0.83, 0.94, 1, 0],
  [0.95, 0.3, 1, 1],
  [0.84, 0.11, 0, 0],
] as const

// Fish under the surface, seen as soft shadows: the lane each keeps to (a share of the height), how fast it swims,
// and a phase.
const FISH = [
  [0.27, 0.031, -0.5],
  [0.74, 0.024, 0.35],
  [0.3, 0.037, 2.6],
] as const

// The dither's thresholds, a 4 x 4 tile: each next threshold sits as far as it can from those before it.
const DITHER = table([8, 0, 10, 2, 6, 14, 5, 13, 11, 3, 9, 1, 4, 12, 7, 15])

// Every sprite, packed one int a row, top row first, leftmost pixel in the lowest bits: two
// bits a pixel, but for the fish, which is one.
// Ducks: 1 yellow, 2 accent (bill and shading), 3 the eye. Pads: 1 pad, 2 plain water. Flower: 1 yellow,
// 2 accent. Reeds: 1 stalk, 3 seed head.
const INK = table([
  348160, 1397760, 1528832, 177558528, 43340800, 348161, 1397765, 5592405,
  5592469, 5614164, 9786712, 2796192, 349440, 1398080, 1922880, 1418560,
  1485120, 349440, 1398080, 5592400, 23418260, 23418260, 9786720, 2796160,
  349440, 1398080, 1398080, 1398080, 349440, 1398080, 5592400, 23418260,
  23438740, 22698580, 9786720, 2796160, 0, 0, 20480, 87040,
  349440, 1398080, 1398080, 1398080, 42292520, 10835360, 2446720, 698880,
  1344, 42816, 1344, 1361, 1365, 1364, 2720, 1360,
  3440, 1680, 5460, 5460, 1360, 640, 1360, 1360,
  1360, 5460, 5780, 1360, 640, 0, 320, 1360,
  1360, 34130, 9560, 2720, 11184640, 173364640, 626349400, -1789569706,
  -1789553322, -1789564586, -1789569386, 626349416, 173364640, 11184640, 698880, 10835360,
  39146840, 39163224, 39474520, 10835360, 698880, 136, 666, 168,
  12288, 12595200, 12595248, 281030704, 281022512, 272699408, 71372816, 71373072,
  71373072, 71569680, 71569668, 272896260, 272897028, 273683460, 72356880, 72356880,
  72619280, 89412944, 12288, 32641, 131059, 262142, 131059, 32641,
  12288,
], 'int')
// Where each sheet starts in INK and its size in cells. A duck has four sheets in order: side, front, back, dabbling.
const ADULT = { start: 0, wide: 14, tall: 12, ringX: 6.5, ringY: 2 }
const CHICK = { start: 48, wide: 8, tall: 7, ringX: 3.5, ringY: 1.5 }
const PAD_BIG = { start: 76, tall: 10 }
const PAD_SMALL = { start: 86, tall: 7 }
const FLOWER = { start: 93, tall: 3 }
const REED = { start: 96, tall: 18 }
// The fish is 18 x 7, one bit a pixel.
const FISH_INK = 114

// Two bits of a sprite row.
const inkAt = (row: number, column: number) => signed(int((INK.at(row) >> int(column * 2)) & 3))
const ditherAt = (cell: vec2) => DITHER.at(signed(int((int(cell.x) & 3) + ((int(cell.y) & 3) << 2))))

// The scene's own integer mixer, for everything here that is left to chance: where a sparkle shows, where a bug
// lands, where a dragonfly goes next. Three whole numbers in, 32 scrambled bits out.
const mixed = (a: number, b: number, c: number) => {
  let n = int((int(a) * 40193) ^ (int(b) * 27941))
  n = int(n + int(c) * 11579)
  n = int(n ^ (n >>> 12))
  n = int(n * 59921 + 6871)
  n = int(n ^ (n << 9))
  n = int(n * 31769)
  n = int(n ^ (n >>> 14))
  return n
}
// A share 0 to 1 from ten bits of a mixed int, starting at bit "from".
const share = (n: number, from: number) => signed(int((int(n) >>> from) & 1023)) / 1024

// The pond drops a bug of its own every 18 seconds, on one side and then the other, and the ducks near it go for
// it. "beat" runs 0 to 1 through each 18 seconds; the bug lands at 0.
const ambientOf = (world: vec2) => {
  const slot = (time + 12) / 18
  const count = floor(slot)
  const roll = mixed(count, 17, 3)
  const right = signed(int(int(count) & 1))
  const at = vec2(floor(world.x * (mix(0.06, 0.8, right) + 0.14 * share(roll, 0))), floor(world.y * (0.25 + 0.5 * share(roll, 10))))
  return { at, beat: slot - count }
}

// How far through its bob a duck is, 0 to 1: up for the first half, down for the second. Paddling hurries it a
// little, never past about one bob a second. Every two-frame cycle here (bob, wriggle, wag, wing beat) is kept
// slower than four changes a second, for the app's flash limit. Ripples can cross a pixel more often; they are
// safe because they are drawn only in the water's second tone, which sits close to the first in luminance.
const bobOf = (index: number, phase: number, paddled: number) => fract(time / 1.6 + phase * 0.37 + paddled * 0.06 + index * 0.13)

// flock: the ducks' state.
// Row 0: x, y, speed x, speed y (cells, cells a second).
// Row 1: heading x, heading y, distance paddled, view (0 right, 1 away from us, 2 left, 3 toward us; add 4 while
//        it dabbles, tail in the air).
// Row 2: the spot it is after x, y, how keen it still is 0 to 1, whether bugs were dropped there (a press) 0 or 1.
const flock: Buffer = buffer({ size: [DUCKS, 3], float: 32, filter: 'nearest' }, (p): vec4 => {
  const index = p.cell.x
  const row = p.cell.y
  const world = pond.size
  const kin = KIN.at(index)
  const grown = step(kin.x, -0.5)
  const home = vec2(kin.yz * world)
  // A grown duck's slow closed path around home. The second duck's path crosses the pond, lingering at each side.
  // It runs mostly from side to side, so the ducks are mostly seen from the side and their rows stay level.
  const second = index > 0.5 && index < 1.5
  const turn = time * (second ? 0.03 : 0.09) + kin.w
  const roam = sin(turn)
  const wander = vec2(
    second ? world.x * (0.5 + 0.39 * roam * (1.5 - 0.5 * roam * roam)) : home.x + 14 * roam,
    home.y + 8 * sin(turn * 1.7 + kin.w * 2) + 3 * sin(turn * 4.1),
  )
  if (first) {
    // Everyone starts where the still Svg shows them (in a window of the still's own shape), facing into the pond.
    const start = vec2(grown > 0.5 ? wander : home)
    const inward = start.x < world.x / 2 ? 1 : -1
    if (row < 0.5) return vec4(start, 0, 0)
    if (row < 1.5) return vec4(inward, 0, 0, inward > 0 ? 0 : 2)
    return vec4(start, 0, 0)
  }
  const a = flock.at(vec2(index, 0))
  const b = flock.at(vec2(index, 1))
  const g = flock.at(vec2(index, 2))
  const at = vec2(a.xy)
  let speed = vec2(a.zw)
  let heading = vec2(b.xy)
  let view = b.w > 3.5 ? b.w - 4 : b.w
  let goal = vec2(g.xy)
  let keen = g.z
  let fed = g.w

  // A duck goes after the nearest pointer that is on open water and not too far off. A pointer over the app's own
  // text or controls is only watched.
  let pull = 0
  let pullAt = vec2(0)
  let press = 0
  let look = 0
  let lookAt = vec2(0)
  for (const finger of pointers) {
    const live = 1 - smoothstep(0, 0.6, finger.gone)
    const spot = vec2((finger.at / size) * world)
    const away = length(vec2(spot - at))
    const score = (live * (1 - smoothstep(70, 105, away))) / (12 + away)
    if (score * (1 - finger.over) > pull) {
      pull = score * (1 - finger.over)
      pullAt = spot
      press = finger.down
    }
    if (score * finger.over > look) {
      look = score * finger.over
      lookAt = spot
    }
  }
  // The pond's own bug counts as a press there for its first eight seconds, if no pointer is nearer.
  const drop = ambientOf(world)
  if (drop.beat > 0.03 && drop.beat < 0.45) {
    const away = length(vec2(drop.at - at))
    const score = (0.6 * (1 - smoothstep(60, 90, away))) / (12 + away)
    if (score > pull) {
      pull = score
      pullAt = vec2(drop.at + 0.5)
      press = 1
    }
  }
  if (pull > 0) {
    // It turns to a new spot quickly but not at once, so a scrubbed pointer only slides the goal about.
    goal = vec2(mix(goal, pullAt, keen < 0.05 ? 1 : 1 - exp(-dt * 5)))
    keen = min(1, keen + dt * 3)
    fed = press
  } else {
    // It remembers the spot for a few seconds after the pointer has gone.
    keen = max(0, keen - dt / 6)
  }

  // It only watches when it has nothing to go after, neither a pointer on the water nor a bug.
  const watching = look > 0 && pull <= 0 && keen < 0.05
  let want = vec2(0)
  let reach = 0
  let pace = 0
  if (grown > 0.5) {
    const eager = smoothstep(0, 0.5, keen)
    want = vec2(mix(wander, goal, eager))
    // It stops a little short of a hovering pointer and watches it; where bugs were dropped it goes right in.
    reach = mix(1.5, 9 - 6 * fed, eager)
    // While it watches a pointer over the text it all but stops.
    pace = watching ? 0.4 : mix(3.2, 5.5 + 1.5 * fed, eager)
  } else {
    // A duckling keeps station behind the one it follows, a little further back when they swim up or down the
    // window: a duck is about as tall as the gap, and they would overlap.
    const lead = flock.at(vec2(kin.x, 0))
    const leadHeading = flock.at(vec2(kin.x, 1))
    const gap = kin.x < 2.5 ? 12 : 9
    want = vec2(lead.xy - leadHeading.xy * vec2(gap, gap * 1.35))
    reach = 0.8
    pace = 8
  }
  const to = vec2(want - at)
  const far = length(to)
  let wish = vec2((to / max(far, 0.01)) * pace * smoothstep(reach, reach + 5, far))

  // It keeps clear of the other ducks, of the lily pads and of the edge.
  for (const other of range(DUCKS)) {
    const them = flock.at(vec2(other, 0))
    const apart = vec2(at - them.xy)
    const room = (grown > 0.5 ? 7.5 : 4.5) + (other < 3 ? 7.5 : 4.5)
    const near = length(apart)
    if (abs(index - other) > 0.5) wish = vec2(wish + (apart / max(near, 0.01)) * max(0, room - near) * 1.2)
  }
  for (const pad of PADS) {
    const apart = vec2(at - vec2(pad[0], pad[1]) * world)
    const near = length(vec2(apart.x, apart.y * 1.6))
    wish = vec2(wish + (apart / max(near, 0.01)) * max(0, (pad[2] ? 5 : 7) + 9 - near) * 1.5)
  }
  wish.x += max(0, 10 - at.x) - max(0, at.x - (world.x - 10))
  wish.y += max(0, 6 - at.y) - max(0, at.y - (world.y - 16))

  speed = vec2(mix(speed, wish, 1 - exp(-dt * 1.8)))
  const next = vec2(at + speed * dt)
  const going = length(speed)

  // It faces the way it swims; once it has all but stopped near a pointer, or is watching one, it faces the pointer.
  let face = vec2(heading)
  if (going > 0.7) face = vec2(speed / going)
  else if (keen > 0.3 && grown > 0.5) face = vec2((goal - at) / max(length(vec2(goal - at)), 0.01))
  else if (watching && grown > 0.5) face = vec2((lookAt - at) / max(length(vec2(lookAt - at)), 0.01))
  heading = vec2(mix(heading, face, 1 - exp(-dt * 3.5)))
  heading = vec2(heading / max(length(heading), 0.2))
  // The view changes only once the heading is well past the diagonal, so it never flickers between two sprites.
  const sideways = view < 0.5 || (view > 1.5 && view < 2.5)
  const lean = sideways ? 1.5 : 0.67
  if (abs(heading.x) * lean > abs(heading.y)) {
    if (sideways) {
      if (heading.x > 0.25) view = 0
      if (heading.x < -0.25) view = 2
    } else view = heading.x > 0 ? 0 : 2
  } else view = heading.y > 0 ? 1 : 3

  // Dabbling, tail in the air: a grown duck does it over dropped bugs, and now and then for no reason; a duckling
  // does it when the one it follows does, on its own beat.
  let dabble = false
  if (grown > 0.5) {
    const eating =
      fed > 0.5 && keen > 0.15 && length(vec2(goal - next)) < reach + 5 && going < 1.5 && fract(time / 2.4 + kin.w) < 0.55
    const slot = time / 9 + kin.w
    const whim =
      time > 12 && keen < 0.05 && share(mixed(index, floor(slot), 5), 0) < 0.22 && fract(slot) > 0.3 && fract(slot) < 0.55 && going < 2.2
    dabble = eating || whim
  } else {
    dabble = flock.at(vec2(kin.x, 1)).w > 3.5 && going < 1.5 && fract(time / 2.4 + kin.w) < 0.6
  }
  if (dabble) view += 4

  if (row < 0.5) return vec4(next, speed)
  if (row < 1.5) return vec4(heading, b.z + going * dt, view)
  return vec4(goal, keen, fed)
})

// pond: the wave field.
// r is the water's height at this cell and g its height a frame ago. b is a bug's remaining life, 1 down to 0, if one
// floats here.
const pond: Buffer = buffer({ scale: 1 / CELL, float: 16, filter: 'nearest' }, (p): vec4 => {
  const here = pond.at(p.cell)
  const sides =
    pond.at(p.cell + vec2(1, 0)).r + pond.at(p.cell - vec2(1, 0)).r + pond.at(p.cell + vec2(0, 1)).r + pond.at(p.cell - vec2(0, 1)).r
  const corners =
    pond.at(p.cell + vec2(1, 1)).r + pond.at(p.cell + vec2(-1, 1)).r + pond.at(p.cell + vec2(1, -1)).r + pond.at(p.cell - vec2(1, 1)).r
  // Rings travel about 12 cells a second at any frame rate down to about 22 a second, and slower below that.
  // Spreading over nine cells, not five, keeps them round on a square grid.
  const courant = min(0.3, 144 * dt * dt)
  let height = here.r + (here.r - here.g) * (1 - 0.25 * dt) + (courant * (4 * sides + corners - 20 * here.r)) / 6
  height *= 1 - 0.6 * dt
  const spot = vec2(p.cell + 0.5)

  // The shape of every push: the water rises in the middle and sinks in a shallow moat twice as wide around it,
  // so that over all none is added.
  const hat = (away: number) => exp(-away * away) - 0.25 * exp(-away * away * 0.25)
  let push = 0
  for (const index of range(DUCKS)) {
    const a = flock.at(vec2(index, 0))
    const b = flock.at(vec2(index, 1))
    const kin = KIN.at(index)
    const blob = hat(length(vec2(spot - a.xy - vec2(0, 0.5))) / (index < 3 ? 2.2 : 1.32)) * (index < 3 ? 1 : 0.45)
    // The moment a duck bobs down it sets one ring going; a paddling duck also pushes a small wake.
    const going = length(vec2(a.zw))
    if (fract(bobOf(index, kin.w, b.z) + 0.5) < dt * (0.625 + 0.06 * going)) height += blob * 3.5
    push += blob * 1.2 * going
  }
  for (const finger of pointers) {
    // A pointer sheds one ring at a time, about three every two seconds, wherever it is then: a held one makes a set
    // of rings inside each other.
    const live = (finger.gone > 0 ? 0 : 1) * (1 - 0.4 * finger.over)
    const now = vec2((finger.at / size) * pond.size)
    const before = vec2((finger.was / size) * pond.size)
    if (fract(finger.age * 1.6) < 1.6 * dt) height += hat(length(vec2(spot - now)) / 1.8) * live * 4 * (0.85 + 0.15 * finger.down)
    // Its wake: this frame's stroke, from where the pointer was to where it is, pushes the water along its whole
    // length. "along" is how far down the stroke this cell sits and "across" how far to the side of it. A slow
    // stroke and a quick one push about as hard; a very quick one pushes less, so hard scrubbing stays calm.
    const stroke = vec2(now - before)
    const run = length(stroke)
    if (run > 0.01) {
      const heading = vec2(stroke / run)
      const from = vec2(spot - before)
      const along = clamp(dot(from, heading), 0, run)
      const across = length(vec2(from - heading * along))
      push += (hat(across / 1.6) * live * 26 * min(run / max(dt, 0.001), 40)) / 90
    }
  }
  height += push * dt

  // Bugs. A pressed pointer on open water drops a handful near itself in its first two seconds, then one every two
  // seconds. Each floats for ten seconds unless a duck dabbles near it first.
  let bug = max(0, here.b - dt / 10)
  for (const finger of pointers) {
    const due = fract(finger.age * 2.5) < 2.5 * dt && (finger.age < 1.7 || fract(finger.age * 0.5) < 0.2)
    if (finger.down > 0.5 && finger.gone <= 0 && finger.over < 0.5 && due) {
      const at = vec2((finger.at / size) * pond.size)
      const roll = mixed(floor(finger.age * 2.5), floor(at.x), floor(at.y))
      // It lands in a loose ring around the pointer, 5 to 11 cells out, so a duck sitting on the spot does not hide it.
      const bearing = share(roll, 0) * 2 * PI
      const out = 5 + share(roll, 10) * 6
      const land = vec2(floor(at.x + cos(bearing) * out), floor(at.y + sin(bearing) * out * 0.7))
      if (p.cell.x == land.x && p.cell.y == land.y) bug = 1
    }
  }
  const drop = ambientOf(pond.size)
  if (drop.beat < dt / 18) {
    if (p.cell.x == drop.at.x && p.cell.y == drop.at.y) bug = 1
    height += hat(length(vec2(spot - drop.at - 0.5)) / 1.8) * 2.5
  }
  for (const index of range(DUCKS)) {
    const a = flock.at(vec2(index, 0))
    const dabbling = flock.at(vec2(index, 1)).w > 3.5
    if (dabbling && length(vec2(spot - a.xy - vec2(0, 1))) < (index < 3 ? 12 : 5)) bug = 0
  }

  // Lily pads are solid, so rings break on them and nothing floats on them; the pond's rim soaks waves up.
  for (const pad of PADS) {
    const centre = vec2(floor(pad[0] * pond.size.x) - (pad[2] ? 1.5 : 0), floor(pad[1] * pond.size.y) + (pad[2] ? 0.5 : 0))
    const q = vec2((spot - centre) / (pad[2] ? vec2(5.5, 3) : vec2(7.5, 4.5)))
    if (dot(q, q) < 1) {
      height = 0
      bug = 0
    }
  }
  const rim = min(min(spot.x, pond.size.x - spot.x), min(spot.y, pond.size.y - spot.y))
  height *= mix(0.8, 1, smoothstep(0, 8, rim))
  height = clamp(height, -6, 6)
  if (first) return vec4(0, 0, 0, 1)
  return vec4(height, here.r, bug, 1)
})

// art: the four-colour pixel art.
// What one duck puts on this art pixel. ink: 0 nothing, 1 yellow, 2 accent, 3 the eye's dark ink, 4 its glint.
// under: what it puts on the water around it, 1 the ring at its water line, 2 a fleck of its reflection.
const duckAt = (cell: vec2, index: number, kind: typeof ADULT) => {
  const a = flock.at(vec2(index, 0))
  const b = flock.at(vec2(index, 1))
  const kin = KIN.at(index)
  const middle = floor(a.x)
  const water = floor(a.y)
  const down = step(0.5, bobOf(index, kin.w, b.z))
  const view = b.w
  // Sheet 0 side, 1 front, 2 back, 3 dabbling; the side view is mirrored to face left.
  const sheet = view > 3.5 ? 3 : view > 2.5 ? 1 : view > 1.5 ? 0 : view > 0.5 ? 2 : 0
  const top = kind.start + sheet * kind.tall
  let across = cell.x - (middle - kind.wide / 2)
  let ink = 0
  let under = 0
  if (across >= 0 && across < kind.wide) {
    if (view > 1.5 && view < 2.5) across = kind.wide - 1 - across
    // On the down beat the whole duck sits one pixel lower and the water line hides its bottom row.
    const up = cell.y - water + down
    if (cell.y >= water && up < kind.tall) {
      ink = inkAt(top + kind.tall - 1 - up, across)
      const blink = fract(time / 4.3 + index * 0.37) < 0.035
      if (ink > 2.5 && blink) ink = 1
      // A grown duck's eye has a glint: one light pixel just above it.
      if (kind.tall > 10 && index != 1 && !blink && ink > 0.5 && ink < 1.5 && up >= 1) {
        if (inkAt(top + kind.tall - up, across) > 2.5) ink = 4
      }
      // The second duck, the one that crosses the pond, wears shades: dark lenses with one pixel of shine.
      if (index == 1 && ink > 0.5 && sheet < 1.5) {
        const side = sheet < 0.5
        if (up == kind.tall - 3) {
          if (side && across >= 6 && across <= 9) ink = across == 9 ? 4 : 3
          if (!side && across >= 3 && across <= 10) ink = across == 4 ? 4 : 3
        }
        if (up == kind.tall - 4) {
          if (side && across >= 8 && across <= 9) ink = 3
          if (!side && (across == 4 || across == 5 || across == 8 || across == 9)) ink = 3
        }
      }
    }
    // One checkered row of reflection a little under the water line.
    const checker = signed(int(int(cell.x + cell.y + down) & 1))
    if (water - cell.y == 2 && checker < 0.5 && inkAt(top + kind.tall - 2, across) > 0.5) under = 2
  }
  // The two-frame ring at the water line: a small oval, then a wider broken one. Only its near half is drawn.
  const ringX = kind.ringX + 2 * down
  const ringY = kind.ringY + down
  const dx = cell.x + 0.5 - middle
  const dy = cell.y + 0.5 - water
  const oval = (x: number, y: number) => (x * x) / (ringX * ringX) + (y * y) / (ringY * ringY)
  if (dy < 0 && oval(dx, dy) <= 1 && (oval(dx + sign(dx), dy) > 1 || oval(dx, dy - 1) > 1)) {
    if (down < 0.5 || signed(int((int(cell.x) >> 1) & 1)) < 0.5) under = max(under, 1)
  }
  // Dabbling throws up two drops that hop on two frames.
  if (sheet > 2.5) {
    const hop = step(fract(time * 1.4 + index * 0.3), 0.5)
    const px = cell.x - middle
    const py = cell.y - water
    const reach = kind.wide < 10 ? 4 : 6
    const high = kind.wide < 10 ? 5 : 8
    if ((px == -reach - hop && py == high + hop) || (px == reach - 1 + hop && py == high + 1 - hop)) under = max(under, 1)
  }
  return { ink, under, depth: a.y }
}

const art = buffer({ scale: 1 / CELL, filter: 'linear' }, p => {
  const cell = p.cell
  const world = pond.size
  const grain = ditherAt(cell)

  // The water. Its second tone is laid as ordered dither in long wavy bands, like slow streaks on a pond. Water
  // that is disturbed, here or in the next cell, loses its dots, so a ring always reads against plain water.
  const water = pond.at(cell)
  const wave = water.r
  const westward = pond.at(cell - vec2(1, 0))
  const eastward = pond.at(cell + vec2(1, 0))
  const west = westward.r
  const east = eastward.r
  const south = pond.at(cell - vec2(0, 1)).r
  const north = pond.at(cell + vec2(0, 1)).r
  const stir = max(max(abs(wave), max(abs(west), abs(east))), max(abs(south), abs(north)))
  const streak = 1.8 * sin(cell.y * 0.085 + 1.6 * sin(cell.x * 0.011 + 0.8) + 0.4) + 0.5 * sin(cell.x * 0.023 - cell.y * 0.031)
  const level = 0.7 + streak - 14 * stir
  // 0 water, 1 the water's second tone, 2 yellow, 3 accent, 4 the eye's dark ink, 5 its glint.
  let tone = step(grain + 0.5, level)

  // Fish glide under the surface: each is a checkered shadow whose tail wags on two frames. A ripple passing
  // overhead hides them.
  for (const n of range(FISH.length)) {
    const fish = FISH[n]!
    const turn = time * fish[1] + fish[2]
    const heading = cos(turn) >= 0 ? 1 : -1
    const column = 9 + floor(cell.x - world.x * (0.5 + 0.46 * sin(turn))) * heading
    const wag = column < 4 && fract(time * 1.3 + n * 0.4) < 0.5 ? 1 : 0
    const rowOf = 3 - floor(cell.y - world.y * (fish[0] + 0.1 * sin(turn * 1.9 + fish[2] * 2.3))) + wag
    if (column >= 0 && column < 18 && rowOf >= 0 && rowOf < 7 && abs(wave) < 0.25) {
      const set = signed(int((INK.at(FISH_INK + rowOf) >> int(column)) & 1))
      if (set > 0.5) tone = signed(int(int(cell.x + cell.y) & 1))
    }
  }

  // A ring is the crest line of a wave, one art pixel wide, drawn where the crest stands proud of the water on
  // either side. As the wave weakens the dither breaks the line into dashes and then dots.
  const crest = west + east < south + north ? wave > west && wave >= east : wave > south && wave >= north
  const proud = 2 * wave - min(west + east, south + north)
  if (crest && wave > 0.02 && proud > 0.07 && proud * 3 > (grain + 0.5) / 16) tone = 1

  let padded = 0
  for (const pad of PADS) {
    const kind = pad[2] ? PAD_SMALL : PAD_BIG
    const left = floor(pad[0] * world.x) - 8
    const bottom = floor(pad[1] * world.y) - floor(kind.tall / 2)
    const column = cell.x - left
    const up = cell.y - bottom
    if (column >= 0 && column < 16 && up >= 0 && up < kind.tall) {
      const ink = inkAt(kind.start + kind.tall - 1 - up, column)
      if (ink > 0.5) {
        tone = ink < 1.5 ? 1 : 0
        padded = 1
      }
    }
    if (pad[3]) {
      const petalColumn = column - (pad[2] ? 5 : 7)
      const petalUp = up - (pad[2] ? 3 : 4)
      if (petalColumn >= 0 && petalColumn < 8 && petalUp >= 0 && petalUp < FLOWER.tall) {
        const ink = inkAt(FLOWER.start + FLOWER.tall - 1 - petalUp, petalColumn)
        if (ink > 0.5) tone = ink + 1
      }
    }
  }

  // Reeds stand in the shallows at the two bottom corners; their tops lean one pixel over and back, slowly.
  for (const n of range(2)) {
    const rowOf = REED.tall - 1 - cell.y
    const lean = rowOf < 6 && fract(time / 3.4 + n * 0.5) < 0.5 ? 1 : 0
    const column = cell.x - (n < 0.5 ? 1 : world.x - 18) - lean
    if (rowOf >= 0 && column >= 0 && column < 16) {
      const ink = inkAt(REED.start + rowOf, column)
      if (ink > 0.5) {
        tone = ink < 1.5 ? 1 : 3
        padded = 1
      }
    }
  }

  // Bugs: three pixels of accent that wriggle between a V and a dash. What a cell's bug is doing: -1 no bug,
  // 0 legs up, 1 legs out, 2 legs pulled in (an old bug's last second).
  const bugOf = (life: number, at: vec2) =>
    life <= 0.001 ? -1 : life < 0.1 ? 2 : signed(int(int(floor(time / 0.45 + at.x * 0.37 + at.y * 0.61)) & 1))
  const below = vec2(cell - vec2(0, 1))
  const legUpA = bugOf(pond.at(below + vec2(1, 0)).b, vec2(below + vec2(1, 0)))
  const legUpB = bugOf(pond.at(below - vec2(1, 0)).b, vec2(below - vec2(1, 0)))
  const legOutA = bugOf(eastward.b, vec2(cell + vec2(1, 0)))
  const legOutB = bugOf(westward.b, vec2(cell - vec2(1, 0)))
  if (water.b > 0.001 || abs(legUpA) < 0.5 || abs(legUpB) < 0.5 || abs(legOutA - 1) < 0.5 || abs(legOutB - 1) < 0.5) tone = 3

  // Sparkles: now and then one pixel of yellow opens into a small cross and closes again.
  const far = vec2(floor(cell.x / 26), floor(cell.y / 20))
  const tick = time / 2.6 + share(mixed(far.x, far.y, 3), 5)
  const dice = mixed(far.x, far.y, floor(tick) + 77)
  if (share(dice, 0) < 0.12 && padded < 0.5) {
    const sx = far.x * 26 + 3 + floor(share(dice, 10) * 20)
    const sy = far.y * 20 + 3 + floor(share(dice, 20) * 14)
    const phase = fract(tick)
    const reach = abs(cell.x - sx) + abs(cell.y - sy)
    const arms = phase > 0.2 && phase < 0.4 ? 1.5 : 0.5
    if (phase < 0.6 && (cell.x == sx || cell.y == sy) && reach < arms) tone = 2
  }

  // The ducks. Where two overlap, the one nearer the bottom of the window is in front.
  let ink = 0
  let front = 100000
  let under = 0
  for (const index of range(DUCKS)) {
    const duck = duckAt(cell, index, index < 3 ? ADULT : CHICK)
    if (duck.ink > 0.5 && duck.depth < front) {
      ink = duck.ink
      front = duck.depth
    }
    under = max(under, duck.under)
  }
  if (under > 0.5) tone = under
  if (ink > 0.5) tone = ink + 1

  // A dragonfly over each clump of reeds: a long accent body and yellow wings that beat on two frames. It hovers,
  // and every few seconds glides to another spot of its patch.
  for (const n of range(2)) {
    const beat = time / 4.2 + n * 0.5
    const count = floor(beat)
    const rollA = mixed(count, n, 41)
    const rollB = mixed(count + 1, n, 41)
    const left = n < 0.5 ? 6 : world.x - 58
    const from = vec2(left + share(rollA, 0) * 52, 8 + share(rollA, 10) * 44)
    const to = vec2(left + share(rollB, 0) * 52, 8 + share(rollB, 10) * 44)
    const fly = vec2(mix(from, to, smoothstep(0.7, 1, beat - count)))
    const column = (cell.x - floor(fly.x)) * (to.x >= from.x ? 1 : -1)
    const rowOf = cell.y - floor(fly.y)
    const spread = fract(time / 0.7 + n * 0.5) < 0.5
    if (rowOf == 0 && column >= -3 && column <= 1) tone = 3
    if (abs(rowOf) == 1 && (column == 0 || (spread && column == -1))) tone = 2
  }

  // Four colours a mode, and two more that only a duck's face uses: a dark ink for the eye and a light glint.
  // The middle of the still Svg says which mode this is.
  const glow = dot(scene.sample(vec2(0.5, 0.5)).rgb, vec3(0.2126, 0.7152, 0.0722))
  const day = step(0.4, glow)
  const plain = mix(vec3(0.06, 0.14, 0.2), vec3(0.91, 0.925, 0.85), day)
  const second = mix(vec3(0.135, 0.375, 0.445), vec3(0.69, 0.9, 0.875), day)
  const yellow = mix(vec3(0.96, 0.77, 0.205), vec3(0.96, 0.74, 0.15), day)
  const accent = mix(vec3(0.94, 0.44, 0.24), vec3(0.77, 0.29, 0.12), day)
  const eye = mix(vec3(0.17, 0.115, 0.085), vec3(0.17, 0.115, 0.085), day)
  const glint = mix(vec3(0.955, 0.93, 0.845), vec3(0.91, 0.925, 0.85), day)
  const color =
    tone < 0.5 ? plain : tone < 1.5 ? second : tone < 2.5 ? yellow : tone < 3.5 ? accent : tone < 4.5 ? eye : glint
  return vec4(color, 1)
})

// view: the picture.
const view = picture(p => {
  const at = vec2(p.uv * art.size)
  const wide = vec2(art.size / res)
  // "at" is this screen pixel in art pixels and "wide" its width there. The art is shown so that every art pixel
  // comes out the same size at any sharpness: a screen pixel that straddles the line between two art pixels takes
  // its share of each, and every other one takes exactly one.
  const edge = vec2(floor(at + 0.5))
  const straddle = vec2(clamp((at - edge) / wide + 0.5, 0, 1))
  const color = art.sample(vec2((edge - 0.5 + straddle) / art.size)).rgb
  // The display's own flaw: a faint ruled grid between art pixels. It is averaged over the screen pixel, so it
  // never shimmers, and at low sharpness it melts into an even tone.
  const gap = 1 / CELL
  const ruled = (t: vec2) => vec2(floor(t) * gap + min(fract(t), gap))
  const cover = vec2((ruled(vec2(at + wide / 2)) - ruled(vec2(at - wide / 2))) / wide)
  const line = 1 - (1 - cover.x) * (1 - cover.y)
  return vec4(vec3(color * (1 - 0.055 * line)), 1)
})

export default shader({ fps: 30, passes: [flock, pond, art, view] })
