// Sea Sparkle. A three-ink linocut of a night sea seen from above: two dark inks and one luminous ink, all flat.
// Light is never a soft bloom here. It is stipple: carved grains whose size and count carry the brightness.
// Passes: "seed" works out once the wakes the swimmers laid before the start, "school" keeps where the swimmers are (a
// few texels of state, so they can shy from a pointer and drift back), "wake" keeps how stirred the water is (a
// quarter-scale buffer that fades over a few seconds), "sea" draws the ground and the plankton over every pixel, and
// four small "shapes" draws lay the moon jellies, the fry, the ray and the fish on top.
import {
  abs, atan, buffer, clamp, composer, cos, dot, dt, exp, first, floor, int, length, max, min, mix, mod, normalize,
  picture, pointer, pointers, scene, shader, shapes, sin, size, smoothstep, sqrt, step, table, time, unsigned, vec2,
  vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

// Inks.
// Midnight proof: deep ink, slate ink, luminous mint. Morning proof: the same blocks pulled on pale paper,
// with deep teal where the luminous ink was.
const inks = () => {
  // There is no light or dark input. The Svg under the shader is written in the shown mode, so read three spots of it.
  const seen = vec3(
    scene.sample(vec2(0.03, 0.97)).rgb + scene.sample(vec2(0.97, 0.97)).rgb + scene.sample(vec2(0.5, 0.02)).rgb,
  )
  const day = smoothstep(1.2, 1.8, seen.r * 0.3 + seen.g * 0.6 + seen.b * 0.1)
  return {
    day,
    deep: mix(vec3(0.035, 0.055, 0.11), vec3(0.925, 0.94, 0.932), day),
    slate: mix(vec3(0.1, 0.165, 0.31), vec3(0.78, 0.85, 0.875), day),
    glow: mix(vec3(0.59, 0.96, 0.84), vec3(0.115, 0.415, 0.5), day),
  }
}
// The luminous block is printed a little out of register, in paper space.
const SLIP = vec2(1.6, -1.1)

// Numbers from cells.
// An integer mix: two odd multipliers fold the cell in, then a rotate-xor, a multiply, an add-shift and a last
// multiply-xor.
const turned = (h: number, by: number) => (h << by) | (h >>> (32 - by))
const cellMix = (ix: number, iy: number, salt: number) => {
  let h = int(ix) * 0x181f02b7 + int(iy) * 0x317adc0d + salt
  h = (h ^ turned(h, 9) ^ turned(h, 22)) * 0x75ffbd1f
  h = h + (h >>> 12)
  h = (h * 0x7a31bd2b) ^ (h >>> 18)
  return h
}
// A second draw of numbers from a mix.
const again = (h: number) => (h * 0x1ed77a81) ^ (h >>> 11)
// Ten bits of a mix as a number from 0 to 1.
const share = (h: number, from: number) => unsigned((h >>> from) & 1023) / 1024
// A soft-edged cut: 1 where "inside" (in points) is positive, blended over one pixel. "sharp" is pixels a point.
const cutOf = (inside: number, sharp: number) => clamp(0.5 + inside * sharp, 0, 1)

// Where the swimmers are.
// Each fish: how far behind the leader along the path (radians), how far to the side of the path (points), where
// round a held finger it comes to feed (an angle), and its size. Neighbors swim on opposite sides of the path and a
// body length apart along it, so no two bodies overlap anywhere on the lap.
const FISH = table([
  [0, 20, 0, 1.8],
  [0.13, -30, 1.05, 1.5],
  [0.26, 34, 2.1, 1.6],
  [0.39, -22, 3.14, 1.3],
  [0.52, 30, 4.19, 1.9],
  [0.65, -36, 5.24, 1.4],
  [3.2, 4, 0.5, 1.7],
  [3.33, -32, 2.6, 1.3],
  [3.46, 30, 4.7, 1.5],
])
const FISH_COUNT = 9
const RAY_SLOT = 9
const SWARM_SLOT = 10
const FRY_COUNT = 22
// The ray is drawn in its own units, this many points each.
const RAY_BIG = 1.4

// Moon jellies: where each drifts about (shares of the window), its size in points, its own phase.
// They keep to the four corners and the middles of the two loops the ray flies, clear of its wings.
const JELLY = table([
  [0.205, 0.5, 20, 0.4],
  [0.07, 0.1, 15, 2.1],
  [0.785, 0.52, 22, 3.3],
  [0.94, 0.1, 16, 4.9],
  [0.07, 0.9, 17, 5.6],
  [0.94, 0.88, 18, 1.3],
])
const JELLY_COUNT = 6
const jellyHome = (row: vec4) =>
  vec2(size.x * (row.x + 0.02 * sin(time * 0.021 + row.w)), size.y * (row.y + 0.03 * cos(time * 0.017 + 2 * row.w)))
// The bell beats slowly.
const jellyBig = (row: vec4) => row.z * (1 + 0.1 * sin(time * 1.4 + row.w * 3))

// The ray glides a figure of eight that loops in both side margins, about two and a quarter minutes a lap. It crosses
// the middle, where the words are, a little faster than it rounds the margins.
const rayHome = (at: number) => {
  const along = 0.95 + at * 0.046
  const a = along + 0.15 * sin(2 * along)
  const pos = vec2(size.x * (0.5 + 0.42 * sin(a)), size.y * (0.5 + 0.27 * sin(2 * a)))
  const dir = normalize(vec2(size.x * 0.42 * cos(a), size.y * 0.54 * cos(2 * a)))
  return { pos, dir }
}
// The fish go round the window the other way on a lumpy ring.
const fishHome = (lag: number, at: number) => {
  const a = 2.4 - at * 0.06 + lag
  const pos = vec2(size.x * (0.5 + 0.41 * cos(a)), size.y * (0.5 + 0.32 * sin(a) + 0.06 * sin(3 * a + 1)))
  const dir = normalize(vec2(size.x * 0.41 * sin(a), -size.y * (0.32 * cos(a) + 0.18 * cos(3 * a + 1))))
  return { pos, dir }
}

// A swarm of fry wanders a slow path of its own; each fry circles the swarm's middle at its own pace.
const swarmHome = (at: number) => {
  const a = 5.5 + at * 0.031
  return vec2(size.x * (0.5 + 0.43 * sin(a)), size.y * (0.5 + 0.3 * sin(1.7 * a + 1)))
}

// Row 0: where each swimmer is and which way it faces. Row 1: how far it has shied from the pointers, eased twice
// over (a push moves the first stage, the first moves the second), so a scrubbed pointer cannot shake it or spin it.
const school: Buffer = buffer({ size: [11, 2], float: 32, filter: 'nearest' }, (p): vec4 => {
  const slot = p.cell.x
  const row = FISH.at(slot)
  let home = vec2(0, 0)
  let dir = vec2(1, 0)
  let reach = 150
  let far = 46
  let ease = 0.4
  let lured = 1
  if (slot > 9.5) {
    home = swarmHome(time)
    reach = 170
    far = 60
    ease = 0.6
  } else if (slot > 8.5) {
    const ray = rayHome(time)
    home = ray.pos
    dir = ray.dir
    reach = 230
    far = 36
    ease = 0.9
    lured = 0
  } else {
    const fish = fishHome(row.x, time)
    const bob = vec2(sin(time * 0.6 + slot * 2.1), cos(time * 0.47 + slot * 1.3)) * 5
    home = vec2(fish.pos + vec2(-fish.dir.y, fish.dir.x) * row.y + bob)
    dir = fish.dir
  }
  const kept = school.at(vec2(slot, 1))
  const shied = kept.zw
  // Its own place round a held finger, 56 points out.
  const place = vec2(cos(row.z), sin(row.z)) * 56
  let push = vec2(0, 0)
  for (const finger of pointers) {
    const away = vec2(home + shied - finger.at)
    const d = length(away)
    const hold = 1 - smoothstep(0, 0.8, finger.gone)
    // A pointer scares, moving or hovering. A finger pressed and held nearly still draws the fish and fry in to feed
    // on what it stirs: each leaves its path by up to 80 points for its own place beside the finger.
    const speed = length(vec2(finger.at - finger.was)) / max(dt, 0.004)
    const calm = lured * finger.down * smoothstep(0.3, 1.2, finger.age) * exp(-speed / 60)
    const lure = vec2(finger.at + place - home)
    const gap = length(lure)
    push = vec2(push + (away / max(d, 1)) * far * exp(-(d * d) / (reach * reach)) * hold * (1 - calm))
    push = vec2(push + (lure / max(gap, 1)) * min(gap, 80) * exp(-(gap * gap) / 90000) * hold * calm)
  }
  push = vec2(push * min(1, 80 / max(length(push), 1)))
  const gain = 1 - exp(-dt / ease)
  const early = vec2(kept.xy + (push - kept.xy) * gain)
  const next = vec2(shied + (early - shied) * gain)
  if (p.cell.y > 0.5) return vec4(early, next)
  // It turns a little toward where it is drifting, by the eased stages only.
  return vec4(home + next, normalize(dir + (early - next) * 0.03))
})

// How far a point is outside the column of text, 0 to 1: the column is as wide as the prompt box and stands over it.
// Before the app has measured the box, take a column 784 points wide in the middle. The swimmers' wakes and the
// plankton's own breathing are held down inside the column, so what passes behind the words stays gentle.
const marginOf = (x: number) => {
  const known = step(0.001, composer.z - composer.x)
  const middle = mix(0.5, (composer.x + composer.z) * 0.5, known) * size.x
  const half = mix(392, (composer.z - composer.x) * 0.5 * size.x + 24, known)
  return smoothstep(half - 70, half + 90, abs(x - middle))
}

// How far a point is from the straight stretch between two places, in the stretch's own frame: across it, and along
// it only past either end. The second measure covers a stretch of no length, which has no frame.
const farFromStretch = (point: vec2, from: vec2, to: vec2) => {
  const run = vec2(to - from)
  const long = length(run)
  const heading = vec2(run / max(long, 0.001))
  const off = vec2(point - from)
  const along = dot(off, heading)
  const across = dot(off, vec2(-heading.y, heading.x))
  const overshoot = along - clamp(along, 0, long)
  return max(length(vec2(overshoot, across)), length(off) - long)
}

// How stirred the water is.
// What the ray's trailing edge stirs at one place: a ribbon off the whole edge, strongest at the wingtips.
const rayStir = (q: vec2, pos: vec2, dir: vec2) => {
  const rel = vec2(q - pos) / RAY_BIG
  const u = dot(rel, dir)
  const v = abs(dot(rel, vec2(-dir.y, dir.x)))
  const out = smoothstep(0.75, 1, v / 74)
  const off = length(vec2(u + 28 - 8 * out, max(v - 74, 0))) * RAY_BIG
  return mix(0.75, 1.3, out) * exp(-off / mix(14, 18, out))
}
// The wakes the swimmers would have laid down before the scene began, worked out once from where their paths ran over
// the seconds before the start, so the first frame already has its veil and trails, as the Svg under the shader does.
const SEED_STEPS = 28
const seed = buffer({ scale: 0.25, float: 16, filter: 'linear', once: true }, p => {
  const q = p.point
  let trail = 0
  for (let k = 0; k < SEED_STEPS; k++) {
    const ago = k * 0.5
    const faded = exp(-ago / 6)
    const ray = rayHome(-ago)
    trail = max(trail, rayStir(q, ray.pos, ray.dir) * faded)
    for (let i = 0; i < FISH_COUNT; i++) {
      const row = FISH.at(i)
      const now = fishHome(row.x, -ago)
      const before = fishHome(row.x, -ago - 0.5)
      const d = farFromStretch(
        q,
        vec2(now.pos + vec2(-now.dir.y, now.dir.x) * row.y - now.dir * 16 * row.w),
        vec2(before.pos + vec2(-before.dir.y, before.dir.x) * row.y - before.dir * 16 * row.w),
      )
      trail = max(trail, 1.2 * exp(-d / 10) * faded)
    }
  }
  return vec4(0, trail * (0.4 + 0.6 * marginOf(q.x)), 0, 0)
})

const PAIRS = [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]
const wake: Buffer = buffer({ scale: 0.25, float: 16, filter: 'linear' }, (p): vec4 => {
  const q = p.point
  // Slow eddies carry the old wake, so it curls and frays as it dies.
  const eddy =
    vec2(
      sin(q.y * 0.021 + time * 0.3) + 0.6 * sin(q.y * 0.047 - time * 0.4 + q.x * 0.013),
      cos(q.x * 0.019 - time * 0.25) + 0.6 * cos(q.x * 0.043 + time * 0.35 - q.y * 0.011),
    ) * 15 + vec2(3, 0)
  const was = wake.sample(vec2(p.uv - (eddy * dt) / size))
  let stir = was.r * exp(-dt / 2.6)
  let trail = first ? seed.at(p.cell).g : was.g * exp(-dt / 6)
  // Ripples are kept apart and die fast, so a ring reads as a ring traveling and not as a filled pool.
  let ripple = was.b * exp(-dt / 0.45)
  // The ring itself, as a line for the slate ink: it dies faster still, so the line stays thin.
  let ringLine = was.a * exp(-dt / 0.1)
  // Inside the column of text every stamp is held down, the pointer's too, so the words stay easy to read.
  const hush = 0.4 + 0.6 * marginOf(q.x)
  // Each pointer stamps the stretch it covered since last frame, so a fast stroke leaves no gaps.
  for (const finger of pointers) {
    const d = farFromStretch(q, finger.was, finger.at)
    const here = 1 - step(0.0001, finger.gone)
    const reach = 14 + 10 * finger.down * smoothstep(0, 1.5, finger.age)
    // Stirred past full: the grains read at most 1, so water stirred again and again stays lit and does not blink.
    const power = (0.9 + 0.9 * finger.down) * (1 - 0.55 * finger.over) * hush
    stir = max(stir, power * here * exp(-d / reach))
    // A press sends out a ripple, and another every 0.9 s while it is held still, two in the water at a time. A tap's
    // ripple keeps traveling through the second its pointer lingers after lifting. The ring is cut in the slate ink,
    // which is close to the ground in tone, and wakes only a thin line of plankton as it passes, so that ripples
    // crossing a spot one after another never add up to a flash.
    const speed = length(vec2(finger.at - finger.was)) / max(dt, 0.004)
    const beat = mod(finger.age, 0.9)
    const reachOut = length(vec2(q - finger.at))
    const lasting =
      finger.down * (1 - smoothstep(0.6, 1, finger.gone)) * (1 - 0.55 * finger.over) * exp(-speed / 60) * hush
    for (const older of [0, 1]) {
      const lived = beat + 0.9 * older
      const ring = abs(reachOut - 16 - 75 * lived)
      const alive = lasting * step(0.9 * older, finger.age) * exp(-lived * 0.5)
      ripple = max(ripple, 0.8 * alive * exp(-ring / 4))
      ringLine = max(ringLine, alive * exp(-ring / 3.5))
    }
  }
  // Two or more pressed pointers: a thread of stirred water is strung between each pair.
  for (const pair of PAIRS) {
    const one = pointer(pair[0]!)
    const two = pointer(pair[1]!)
    // Only between fingers that rest or move slowly: under four fast fingers the threads would fill the window.
    const hurry = (length(vec2(one.at - one.was)) + length(vec2(two.at - two.was))) / max(dt, 0.004)
    const both =
      one.down * two.down * (1 - step(0.0001, one.gone)) * (1 - step(0.0001, two.gone)) * exp(-hurry / 240)
    stir = max(stir, 0.9 * both * hush * exp(-farFromStretch(q, one.at, two.at) / 7))
  }
  // The swimmers' own wakes, held down the same way.
  const old = trail
  // The ray sheds a veil of stirred water off its whole trailing edge, strongest at the wingtips.
  const ray = school.at(vec2(RAY_SLOT, 0))
  trail = max(trail, rayStir(q, ray.xy, ray.zw))
  for (let i = 0; i < FISH_COUNT; i++) {
    const fish = school.at(vec2(i, 0))
    const d = length(vec2(q - fish.xy + fish.zw * 16 * FISH.at(i).w))
    trail = max(trail, 1.2 * exp(-d / 10))
  }
  // The fry stir a faint cloud about their swarm.
  const swarm = length(vec2(q - school.at(vec2(SWARM_SLOT, 0)).xy))
  trail = max(trail, 0.42 * exp(-(swarm * swarm) / 2500))
  // Each jelly keeps a faint halo of stirred water about its rim.
  for (let i = 0; i < JELLY_COUNT; i++) {
    const row = JELLY.at(i)
    const rim = abs(length(vec2(q - jellyHome(row))) - jellyBig(row) * 1.3)
    trail = max(trail, 0.5 * exp(-rim / 7))
  }
  trail = max(old, trail * hush)
  return vec4(stir, trail, ripple, ringLine)
})

// The sea: ground and plankton.
const sea = picture(p => {
  const q = p.point
  const ink = inks()
  const sharp = 1 / p.px

  // Swell cuts: rows of long lens-shaped gouges in the slate ink, sliding a few points a second, row against row.
  const rowHeight = 54
  const row = floor(q.y / rowHeight + 0.5)
  const side = mod(row, 2) * 2 - 1
  const xs = q.x + side * time * 5 + row * 131
  const stirred = wake.sample(p.uv)
  // The cuts ride up a little on stirred water, and settle as it calms.
  const lift = 6 * min(stirred.r, 1)
  const mid = row * rowHeight + 8 * sin(xs * 0.011 + row * 1.7) + 3.5 * sin(xs * 0.027 - row) + lift
  const fat = 3.1 * sin(xs * 0.018 + row * 2.3) + 1.3 * sin(xs * 0.049 + row) - 0.7
  const fine = 1.5 * sin(xs * 0.023 + row * 4.1 + 2) - 0.8
  const swell = max(cutOf(fat - abs(q.y - mid), sharp), cutOf(fine - abs(q.y - mid + 12), sharp))
  // Current nicks: short thin cuts of the same ink between the rows, drifting slowly the one way.
  const qn = vec2(q.x + 2.2 * time, q.y)
  const cn = floor(vec2(qn / vec2(46, 18)))
  const hn = cellMix(cn.x, cn.y, 71)
  const hm = again(hn)
  const nickAt = vec2((cn + 0.5) * vec2(46, 18) + (vec2(share(hn, 10), share(hn, 20)) - 0.5) * vec2(26, 9))
  const nickHalf = 4 + 5 * share(hm, 0)
  const nx = qn.x - nickAt.x
  const nick =
    cutOf(0.8 * (1 - abs(nx) / nickHalf) - abs(qn.y - nickAt.y - (share(hm, 10) - 0.5) * 0.16 * nx), sharp) *
    step(share(hn, 0), 0.42)
  // Ripples from a press: rings in the slate ink, narrower as they spread. On pale paper that ink stands well off the
  // ground, so there the rings print faint: a ring that sweeps a spot again and again must never count as a flash.
  const rings = cutOf((stirred.a - 0.4) * 7, sharp) * (0.9 - 0.55 * ink.day)
  let color = mix(ink.deep, ink.slate, max(max(swell, rings), nick * 0.8))

  const ql = vec2(q + SLIP)
  // Grains breathe on and off by themselves, most of all in slow drifting clouds where the plankton gather.
  const cloud =
    0.2 +
    0.8 *
      smoothstep(
        -0.1,
        0.8,
        sin(q.x * 0.0052 + time * 0.031 + 1) * sin(q.y * 0.0075 - time * 0.023) +
          0.35 * sin((q.x + q.y) * 0.011 + time * 0.04),
      )
  const field = min(min(stirred.r, 1) + min(stirred.g, 1) + stirred.b, 1)
  // Water stirred hard prints its grains a little fatter.
  const hot = 1 + 0.3 * smoothstep(1, 1.7, stirred.r)
  // The tide's breath: every two minutes a soft front crosses the sea, and plankton wake along it as it passes.
  // It crosses 0.8 x + 0.6 y from 400 before the window to 400 past it, so it comes and goes out of sight.
  const front =
    q.x * 0.8 + q.y * 0.6 + 40 * sin(q.y * 0.008 + time * 0.05) + 400 -
    mod(time * 22 + 920, 0.8 * size.x + 0.6 * size.y + 800)
  const quiet = 0.55 + 0.45 * marginOf(q.x)
  const tide = exp(-(front * front) / 12000) * quiet
  const roused = cloud * cloud * 0.28 * quiet + 0.3 * tide
  // Inside the front a grain spends more of its slow beat lit.
  const wakeful = 0.86 - 0.5 * tide

  // Pecks, one to a cell of 7.5 points. Each layer's lattice is turned so that no rows line up with the window.
  const qa = vec2(ql.x * 0.956 + ql.y * 0.292 - 3.2 * time, ql.y * 0.956 - ql.x * 0.292 + 1.1 * time)
  const ca = floor(vec2(qa / 7.5))
  const ha = cellMix(ca.x, ca.y, 17)
  const hb = again(ha)
  const centerA = vec2((ca + 0.5) * 7.5 + (vec2(share(ha, 0), share(ha, 10)) - 0.5) * 5.4)
  const breathA =
    smoothstep(0, 0.1, 0.06 + roused - share(hb, 0)) *
    max(0, sin(time * (0.25 + 0.3 * share(hb, 10)) + share(hb, 20) * 6.283) - wakeful) * 7
  const litA = smoothstep(0, 0.3, field + breathA - 0.03 - 0.95 * share(ha, 20))
  const radA = (1 + 1.2 * share(hb, 22)) * litA * hot
  const peck = cutOf(radA - length(vec2(qa - centerA)), sharp) * min(1, litA * 5)

  // Larger rice-grain cuts, one to a cell of 23 points, slanted the way the carver's hand sat.
  const qb = vec2(ql.x * 0.875 - ql.y * 0.485 + 4.6 * time, ql.y * 0.875 + ql.x * 0.485 - 0.8 * time)
  const cb = floor(vec2(qb / 23))
  const hc = cellMix(cb.x, cb.y, 91)
  const hd = again(hc)
  const centerB = vec2((cb + 0.5) * 23 + (vec2(share(hc, 0), share(hc, 10)) - 0.5) * 13)
  const breathB =
    smoothstep(0, 0.1, 0.12 + 2 * roused - share(hd, 0)) *
    max(0, sin(time * (0.2 + 0.3 * share(hd, 10)) + share(hd, 20) * 6.283) - wakeful) * 7
  const litB = smoothstep(0, 0.3, field + breathB - 0.05 - 0.95 * share(hc, 20))
  const d = vec2(qb - centerB)
  const lean = 0.8 + 0.5 * (share(hd, 22) - 0.5)
  const ex = d.x * 0.6 + d.y * lean
  const ey = d.y * 0.6 - d.x * lean
  const half = 4 + 3 * share(hc, 22)
  const wide = 1.6 + share(hd, 12)
  // A gouge mark: blunt where the tool went in, pointed where it came out.
  const taper = 1 - 0.45 * clamp(ex / half, -1, 1)
  const grain = cutOf(wide * litB * hot - length(vec2((ex * wide) / half, ey / taper)), sharp) * min(1, litB * 5)
  // Some grains take the ink thin.
  const thin = 1 - 0.4 * step(0.8, share(hd, 2))

  // Sparks: where the water is stirred hard, a few four-pointed nicks, two crossed cuts each.
  const qc = vec2(ql.x * 0.766 + ql.y * 0.643 + 1.5 * time, ql.y * 0.766 - ql.x * 0.643 + 2.4 * time)
  const cc = floor(vec2(qc / 41))
  const he = cellMix(cc.x, cc.y, 53)
  const centerC = vec2((cc + 0.5) * 41 + (vec2(share(he, 0), share(he, 10)) - 0.5) * 26)
  const litC = smoothstep(0, 0.35, field - 0.25 - 0.7 * share(he, 20))
  const dc = vec2(abs(qc - centerC))
  const reachC = (5 + 3 * share(he, 22)) * litC
  const star = sqrt(dc.x) + sqrt(dc.y)
  const spark = cutOf(reachC - star * star, sharp * 0.5) * min(1, litC * 5)

  color = mix(color, ink.glow, max(max(peck, grain * thin), spark))
  return vec4(color, 1)
})

// The moon jellies.
const CORNERS = table([[-1, -1], [1, -1], [1, 1], [-1, -1], [1, 1], [-1, 1]])
const jellyDraw = shapes(
  { count: 6, instances: JELLY_COUNT, cover: 0.035 },
  (vertex, instance) => {
    const row = JELLY.at(instance)
    const big = jellyBig(row)
    const local = vec2(CORNERS.at(vertex) * 1.36)
    return { at: vec2(((jellyHome(row) + local * big) / size) * 2 - 1), a: vec4(local, instance, big) }
  },
  spot => {
    const ink = inks()
    const big = spot.a.w
    const sharp = 1 / spot.px
    const spin = JELLY.at(spot.a.z).w + time * 0.04
    // The slate block: a scalloped disc, seen from above.
    const r = length(vec2(spot.a.xy))
    const disc = cutOf((1 + 0.05 * cos(8 * (atan(spot.a.y, spot.a.x) - spin)) - r) * big, sharp)
    // The luminous block, slipped: the rim, a rosette of four rings, sixteen rim ticks and a fringe of pecks.
    const pl = vec2(spot.a.xy - SLIP / big)
    const rl = length(pl)
    const around = ((atan(pl.y, pl.x) - spin) * 16) / 6.2832
    const rim = cutOf(0.6 - abs(rl - 0.97 - 0.0485 * cos(around * 3.1416)) * big, sharp)
    const folded = vec2(abs(pl.x * cos(spin) + pl.y * sin(spin)), abs(pl.y * cos(spin) - pl.x * sin(spin)))
    const rosette = cutOf(0.6 - abs(length(vec2(folded - 0.2546)) - 0.2) * big, sharp)
    const spoke = abs(mod(around, 1) - 0.5) * 0.3927 * rl * big
    const ticks = cutOf(0.4 - spoke, sharp) * step(0.68, rl) * step(rl, 0.86)
    const between = (mod(around + 0.5, 1) - 0.5) * 0.3927 * rl * big
    const fringe = cutOf(0.9 - length(vec2((rl - 1.18) * big, between)), sharp)
    const lit = max(max(rim, rosette), max(ticks, fringe))
    const cover = max(disc * 0.85, lit)
    return vec4(mix(ink.slate, ink.glow, lit) * cover, cover)
  },
)

// The fry.
// Where fry number i is about the swarm's middle, and which way it heads: each circles on an oval of its own, at its
// own pace, weaving in and out.
const fryAbout = (i: number) => {
  const reach = (12 + 34 * mod(i * 0.37 + 0.11, 1)) * (1 + 0.28 * sin(time * 0.9 + i * 1.7))
  const turn = i * 2.4 + time * (0.25 + 0.3 * mod(i * 0.73, 1))
  const flat = 0.5 + 0.45 * mod(i * 0.53, 1)
  return { at: vec2(cos(turn), flat * sin(turn)) * reach, dir: normalize(vec2(-sin(turn), flat * cos(turn))) }
}
const fryDraw = shapes(
  { count: 6, instances: FRY_COUNT, cover: 0.03 },
  (vertex, instance) => {
    const corner = CORNERS.at(vertex)
    const fry = fryAbout(instance)
    const local = vec2(-0.75 + corner.x * 6.75, corner.y * 3.2)
    const world = vec2(
      school.at(vec2(SWARM_SLOT, 0)).xy + fry.at + (fry.dir * local.x + vec2(-fry.dir.y, fry.dir.x) * local.y) * 1.5,
    )
    return { at: vec2((world / size) * 2 - 1), a: vec4(local, instance, 0) }
  },
  spot => {
    const ink = inks()
    const u = spot.a.x
    // A sliver with a forked tail, wriggling.
    const v = abs(spot.a.y - 0.7 * clamp((2 - u) / 6, 0, 1) * sin(u * 0.9 + time * 11 + spot.a.z * 2.3))
    const t = clamp((u + 3.5) / 9, 0, 1)
    const body = min(6.2 * t * (1 - t) * (0.5 + 0.5 * t) - v, u + 3.5)
    const back = clamp((-3 - u) / 3, 0, 1)
    const tail = min(min(0.35 + 1.5 * back - v, v - (back - 0.45) * 1.6), min(-3 - u, u + 6))
    const cover = cutOf(max(body, tail), 1.5 / spot.px) * 0.9
    return vec4(ink.glow * cover, cover)
  },
)

// The ray.
// The ray's outline in its own units: positive inside. Swept wings with hooked tips, a broad head with the mouth bitten
// out between two head fins, a whip tail that sways. "flap" runs -1 to 1 over a wingbeat.
const rayShape = (u: number, v: number, flap: number) => {
  const span = 76 + 7 * flap
  const back = 5 - 5 * flap
  const s = abs(v) / span
  const s2 = s * s
  const lead = 30 - (22 + back) * s2 - 22 * s2 * s2
  const rear = -34 + 34 * s - back * s2 - 14 * s2 * s
  const wing = min(lead - u, u - rear) * 0.8
  const mouth = (1 - length(vec2((u - 46) / 9, v / 8.5))) * 8.5
  const head = min((1 - length(vec2((u - 24) / 20, v / 17))) * 17, -mouth)
  const down = clamp((-30 - u) / 92, 0, 1)
  const sway = 11 * down * down * sin(u * 0.05 + time * 1.3 + 0.6)
  const tail = min(2.7 - 2.4 * down - abs(v - sway), min(-28 - u, u + 122))
  // The knife wanders a little: a small wobble on every edge.
  const wobble = 0.5 * sin(u * 0.83 + v * 0.31) * sin(v * 0.71 - u * 0.27)
  // Two small pelvic fins at the root of the tail.
  const pelvic = (1 - length(vec2((u + 36) / 7, (abs(v) - 6.5 + 0.25 * (u + 36)) / 3.4))) * 3.4
  return { inside: max(max(wing, head), max(tail, pelvic)) + wobble, s, lead, rear, down, sway }
}
const rayDraw = shapes(
  { count: 6, cover: 0.08 },
  (vertex, instance) => {
    const corner = CORNERS.at(vertex)
    const ray = school.at(vec2(RAY_SLOT, 0))
    const across = vec2(-ray.w, ray.z)
    const local = vec2(-39 + corner.x * 90, corner.y * 90)
    const world = vec2(ray.xy + (ray.zw * local.x + across * local.y) * RAY_BIG)
    // The luminous block's slip, turned into the ray's own frame.
    const slip = vec2(dot(SLIP, ray.zw), dot(SLIP, across)) / RAY_BIG
    return { at: vec2((world / size) * 2 - 1), a: vec4(local, slip) }
  },
  spot => {
    const ink = inks()
    const edge = RAY_BIG / spot.px
    const flap = sin(time * 1.6 + 0.58)
    // The slate block: the silhouette, with a spine and four gill slits a side carved back to the deep ink.
    const u = spot.a.x
    const v = spot.a.y
    const body = cutOf(rayShape(u, v, flap).inside, edge)
    const spine = cutOf(0.6 - abs(v), edge) * step(-30, u) * step(u, 14)
    const slit = abs(mod(u + 0.35 * abs(v) - 1, 4.5) - 2.25)
    const gills = cutOf(0.6 - slit, edge) * step(3, u) * step(u, 21) * step(6, abs(v)) * step(abs(v), 13.5)
    // The luminous block, slipped. Under the slate it prints the whole outline a touch fat, so a bright sliver shows
    // along one side; over it, a dashed rim on the leading edges, eyes, stipple on the back and beads down the tail.
    const ul = u - spot.a.z
    const vl = v - spot.a.w
    const lum = rayShape(ul, vl, flap)
    const under = cutOf(lum.inside + 0.8, edge)
    const behind = lum.lead - ul
    const dash = step(mod(lum.s * 11, 1), 0.7) * step(0.16, lum.s) * step(lum.s, 0.98)
    const rim = cutOf(1.7 * (1 - 0.5 * lum.s) - abs(behind - 2.8), edge) * dash
    const eyes = cutOf(1.8 - length(vec2(ul - 33, abs(vl) - 11)), edge)
    // Stipple shading on the back, densest just behind the rim, thinning toward the trailing edge.
    const cell = floor(vec2(vec2(ul, vl) / 5))
    const hs = cellMix(cell.x, cell.y, 29)
    const place = vec2((cell + 0.5) * 5 + (vec2(share(hs, 0), share(hs, 10)) - 0.5) * 2.4)
    const deepIn = clamp(behind / max(lum.lead - lum.rear, 1), 0, 1)
    const take =
      step(share(hs, 20), 1 - 1.4 * deepIn) * step(5.5, behind) * step(0.14, lum.s) * step(lum.s, 1) * step(lum.rear + 3, ul)
    const stipple = cutOf(0.65 + 0.65 * share(hs, 22) - length(vec2(vec2(ul, vl) - place)), edge) * take
    const tipBeads =
      cutOf(1.9 - 1.4 * lum.down - abs(vl - lum.sway), edge) * step(0.45, lum.down) * step(-122, ul) * step(mod(ul, 8), 4.5)
    // Two remoras keep station behind the wings: small fish, fatter at the head, with a forked tail.
    const along = (ul + 54) / 8
    const aside = abs(abs(vl) - 15 - 0.5 * sin(ul * 0.5 + time * 3))
    const fork = clamp((-0.8 - along) / 0.6, 0, 1)
    const remora = cutOf(
      max(
        min(1.9 * (1 - along * along) * (1 + 0.3 * along) - aside, 1 - abs(along)),
        min(min(2 * fork - aside, aside - (fork - 0.55) * 2.2), min(-0.8 - along, along + 1.4)),
      ),
      edge,
    )
    const lit = max(max(rim, eyes), max(max(stipple * 0.75, tipBeads), remora))
    let color = mix(ink.glow, mix(ink.slate, ink.deep, max(spine, gills) * 0.9), body)
    color = mix(color, ink.glow, lit)
    const cover = max(max(body, under), lit)
    return vec4(color * cover, cover)
  },
)

// The fish.
// A fish's outline in its own units: positive inside. The body swims: a wave runs down it, widest at the tail.
const fishShape = (u: number, v0: number, beat: number) => {
  const bend = clamp((7 - u) / 24, 0, 1)
  const v = v0 - 3.4 * bend * bend * sin(u * 0.3 + beat)
  const side = abs(v)
  const t = clamp((u + 11) / 24, 0, 1)
  const girth = max(9.3 * t * sqrt(1 - t) * (0.4 + 0.6 * t), 0.65)
  const body = min(girth - side, min(13 - u, u + 11))
  const tt = clamp((-10 - u) / 9, 0, 1)
  const tail = min(min(0.65 + 3.5 * tt - side, side - (tt - 0.5) * 4.2), min(-10 - u, u + 19))
  const fa = -(u - 5.5) * 0.64 + (side - 2.9) * 0.77
  const fb = (u - 5.5) * 0.77 + (side - 2.9) * 0.64
  const fin = min(0.95 * (1 - fa / 5.2) - abs(fb), min(fa, 5.2 - fa))
  return { inside: max(max(body, tail), fin), v, side, girth }
}
const fishDraw = shapes(
  { count: 6, instances: FISH_COUNT, cover: 0.05 },
  (vertex, instance) => {
    const corner = CORNERS.at(vertex)
    const fish = school.at(vec2(instance, 0))
    const big = FISH.at(instance).w
    const across = vec2(-fish.w, fish.z)
    const local = vec2(-3.5 + corner.x * 20, corner.y * 12)
    const world = vec2(fish.xy + (fish.zw * local.x + across * local.y) * big + SLIP)
    const slip = vec2(dot(SLIP, fish.zw), dot(SLIP, across)) / big
    return { at: vec2((world / size) * 2 - 1), a: vec4(local, instance, big), b: vec4(slip, 0, 0) }
  },
  spot => {
    const ink = inks()
    const u = spot.a.x
    const edge = spot.a.w / spot.px
    const beat = time * 6.5 + spot.a.z * 1.9 + 0.8
    // The luminous block: the fish itself, with a spine, a gill cut, two eyes and three scale nicks a side carved out.
    const lum = fishShape(u, spot.a.y, beat)
    const shape = cutOf(lum.inside, edge)
    const spine = cutOf(0.42 - lum.side, edge) * step(-7, u) * step(u, 4.5)
    const gill = cutOf(0.42 - abs(u - 8.2 + 0.14 * lum.v * lum.v), edge) * step(lum.side, 2.6)
    const eye = cutOf(0.55 - length(vec2(u - 9.7, lum.side - 1.55)), edge)
    const slant = u + 0.556 * (lum.side - 0.95) - 0.5
    const scales =
      cutOf(0.3 - abs(mod(slant - 0.7, 3) - 1.5), edge) *
      step(0.95, lum.side) * step(lum.side, min(2.3, lum.girth * 0.78)) * step(-4.3, slant) * step(slant, 2.7)
    // The slate block prints the same fish a little fat underneath, so each one keeps a dark keyline among the plankton.
    const key = cutOf(fishShape(u + spot.b.x, spot.a.y + spot.b.y, beat).inside + 1.5 / spot.a.w, edge)
    let color = mix(ink.slate, ink.glow, shape)
    color = mix(color, ink.deep, max(max(spine, gill), max(eye, scales)) * shape)
    const cover = max(key, shape)
    return vec4(color * cover, cover)
  },
)

export default shader({ fps: 30, passes: [seed, school, wake, sea, jellyDraw, fryDraw, rayDraw, fishDraw] })
