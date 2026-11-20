// Field Lines. Technical pencil on lab graph paper; chalk on slate in the dark.
// One pencil dash in every paper square turns along a magnetic field. Two poles wander in the side margins,
// plotting compasses sit at the sheet's edges, and graphite dust gathers and creeps where the field is strong.
// Every pointer is one more pole. A pointer lights nothing: it adds a thin ring under itself, draws dust
// to itself and presses nearby dashes a little harder; everything else only turns, lengthens and shifts.
import {
  PI, abs, clamp, dot, floor, fract, int, length, max, min, mix, picture, pointers, range,
  scene, shader, sin, size, smoothstep, time, unsigned, vec2, vec3, vec4,
} from 'claude-code/shader'

// One paper square, in points. Rules run every square, heavier every fifth.
const G = 28
// Where the rules start, so that a 1512x945 window's middle falls in the middle of a square.
const OFF_X = 14
const OFF_Y = 10.5
// A pole is softened so the field stays finite on top of it (points squared).
const SOFT = 500
// How far a pole's field reaches: a lone pole's reads as a little under half strength at this many points.
const NEAR = 160

// The scene's own integer stir: two lanes folded into each other, then one value out.
const stir = (ix: number, iy: number) => {
  let a = int(int(ix) * 0x2f6b4a9d + 0x51a3)
  const b = int((int(iy) * 0x6d1c85e3) ^ (a >>> 9))
  a = int((a ^ (b << 5)) * 0x19e4b7a5)
  a = int(a ^ (a >>> 14))
  a = int((a + b) * 0x4b3d92c7)
  return int(a ^ (a >>> 17))
}
// A fresh word from an old one, for the next handful of bits.
const again = (h: number) => {
  const a = int((h ^ (h >>> 12)) * 0x35a9c6d3 + 0x2b71)
  return int(a ^ (a >>> 15))
}
// Some bits of a word as a number from 0 up to, not including, 1.
const slice = (h: number, shift: number, mask: number) =>
  unsigned(int((h >>> shift) & mask)) / (mask + 1)

// Distance from q to a straight stroke, given by its middle, its way (a unit vector) and half its length.
// Worked in the stroke's own two axes, the same way a dash is drawn below.
const toStroke = (q: vec2, mid: vec2, way: vec2, halfLong: number) => {
  const d = vec2(q - mid)
  return length(vec2(max(abs(dot(d, way)) - halfLong, 0), d.x * way.y - d.y * way.x))
}
// How strong a field of this size reads, 0 far from every pole to 1 beside one.
const grade = (pull: number) => clamp((pull * NEAR / (pull * NEAR + 1) - 0.3) / 0.45, 0, 1)

const sheet = picture(p => {
  const at = p.point
  const perPixel = 1 / p.px
  // How much of a pixel a mark covers: gap is the distance to its middle line, half its half width.
  // A mark thinner than a pixel is drawn a pixel wide and fainter, so it never breaks into dots.
  const cover = (gap: number, half: number) => {
    const wide = max(half, 0.5 * p.px)
    return clamp((wide - gap) * perPixel + 0.5, 0, 1) * min(1, 2 * half * perPixel)
  }
  // The same for a filled shape: edge is the distance outside it.
  const inside = (edge: number) => clamp(0.5 - edge * perPixel, 0, 1)
  // Evenly spaced hatching: the distance to the nearest of a family of parallel strokes.
  const hatch = (v: number, every: number) => abs(fract(v / every + 0.5) - 0.5) * every
  const between = (v: number, low: number, high: number) => (v > low && v < high ? 1 : 0)

  // Light or dark comes from the still picture's paper, read at the window's middle where it is kept bare.
  const under = scene.sample(vec2(0.5, 0.5))
  const dark = 1 - smoothstep(0.3, 0.6, dot(vec3(under.rgb), vec3(0.3, 0.6, 0.1)))
  const paper = vec3(mix(vec3(0.953, 0.945, 0.906), vec3(0.133, 0.153, 0.165), dark))
  const ruled = vec3(mix(vec3(0.56, 0.73, 0.9), vec3(0.25, 0.32, 0.37), dark))
  const lead = vec3(mix(vec3(0.27, 0.28, 0.33), vec3(0.91, 0.9, 0.86), dark))
  const redLead = vec3(mix(vec3(0.79, 0.23, 0.16), vec3(0.92, 0.45, 0.37), dark))

  // Paper tooth: one faint grain, also what breaks the graphite.
  const tooth = slice(stir(floor(at.x / 1.5) + 11, floor(at.y / 1.5) + 5), 3, 255)

  // Printed rules.
  const fine = max(cover(hatch(at.x - OFF_X, G), 0.4), cover(hatch(at.y - OFF_Y, G), 0.4))
  const bold = max(cover(hatch(at.x - OFF_X, 5 * G), 0.55), cover(hatch(at.y - OFF_Y, 5 * G), 0.55))

  // The two wandering poles, each in a lane of its own side margin. In a narrow window the lane is held
  // clear of the compasses' lane at the edge (a compass case and a pole's ring, with a little room).
  const edgeLane = max(0.06 * size.x, 56) + 70
  const northAt = vec2(
    max(size.x * (0.155 + 0.04 * sin(0.043 * time + 0.6)), edgeLane),
    size.y * (0.52 + 0.31 * sin(0.031 * time + 1.1)),
  )
  const southAt = vec2(
    min(size.x * (0.845 + 0.04 * sin(0.037 * time + 2.4)), size.x - edgeLane),
    size.y * (0.46 + 0.31 * sin(0.027 * time + 4)),
  )

  // Plotting compasses, each in the middle of a paper square, in a lane outside the poles' own,
  // and never so near the window's edge that the case is cut.
  const seatX = (share: number) => (floor((clamp(size.x * share, 56, size.x - 56) - OFF_X) / G) + 0.5) * G + OFF_X
  const seatY = (share: number) => (floor((clamp(size.y * share, 56, size.y - 56) - OFF_Y) / G) + 0.5) * G + OFF_Y
  const hubs = [
    vec2(seatX(0.04), seatY(0.82)),
    vec2(seatX(0.06), seatY(0.47)),
    vec2(seatX(0.04), seatY(0.14)),
    vec2(seatX(0.94), seatY(0.9)),
    vec2(seatX(0.96), seatY(0.6)),
    vec2(seatX(0.94), seatY(0.25)),
  ]
  const square = vec2(floor((at.x - OFF_X) / G), floor((at.y - OFF_Y) / G))
  const middle = vec2((square.x + 0.5) * G + OFF_X, (square.y + 0.5) * G + OFF_Y)
  // Where the field is read: the square's middle, or the compass's pivot inside a compass's nine squares.
  let hub = middle
  let onHub = 0
  let hubNo = 0
  for (const n of range(6)) {
    const d = vec2(at - hubs[n]!)
    if (max(abs(d.x), abs(d.y)) < 1.5 * G) {
      hub = hubs[n]!
      onHub = 1
      hubNo = n
    }
  }

  // The field at that place: each pole pushes along the line from itself, falling off with distance.
  let field = vec2(0)
  const pole = (where: vec2, charge: number) => {
    const d = vec2(hub - where)
    field = vec2(field + d * (charge / (dot(d, d) + SOFT)))
  }
  pole(northAt, 1)
  pole(southAt, -1)
  const calm = grade(length(field))
  // Pointers: a hover is a north pole, a press a south pole, and each is turned over once for every
  // earlier pointer still there. Slots are in arrival order, so fingers alternate, and because the
  // turning is weighted by the earlier pointer's fade, nothing jumps when a faded entry leaves its slot.
  // (The list holds four. A fifth entry inside half a second of a lift pushes a fading one out early,
  // and the dashes round it then step once.)
  let turned = 1
  let ringLead = 0
  let ringRed = 0
  for (const finger of pointers) {
    const here = clamp(finger.age / 0.35, 0, 1) * (1 - clamp(finger.gone / 0.5, 0, 1))
    const charge = (1 - 2 * finger.down) * turned
    // A pole flung across the paper is gone before the needles can follow: its pull is halved at 84 points
    // a frame (about 2500 a second at 30 frames a second) and keeps falling, so a hard scrub stirs the sheet
    // only a little. Measured by the frame and not by dt, which the engine smooths and which lags after
    // slow frames.
    const rush = length(vec2(finger.at - finger.was)) / 84
    const pull = here * mix(1.4, 0.5, finger.over) / (1 + rush * rush)
    pole(finger.at, charge * pull)
    const ring = cover(abs(length(vec2(at - finger.at)) - 12), 0.5) * pull * 0.45
    ringRed = max(ringRed, ring * max(charge, 0))
    ringLead = max(ringLead, ring * max(-charge, 0))
    turned = turned * (1 - 2 * here)
  }
  const strength = length(field)
  // Where the poles cancel exactly the field has no direction; a dash there lies level.
  const dir = vec2(strength > 1e-12 ? vec2(clamp(field / max(strength, 1e-12), -1, 1)) : vec2(1, 0))
  const stirred = grade(strength)
  // How hard the pencil pressed: by the wandering poles' field, and only a little more for a pointer,
  // so that a pointer turns the dashes and does not darken the paper under itself.
  const heavy = calm * calm + 0.35 * max(stirred * stirred - calm * calm, 0)

  // The square's dash: set down by hand (a little off the middle), longer and darker where the field is strong.
  const h = stir(square.x, square.y)
  const nudge = vec2(slice(h, 0, 15) - 0.5, slice(h, 4, 15) - 0.5) * (3 - 3 * heavy)
  const rel = vec2(at - middle - nudge)
  const along = dot(rel, dir)
  const reach = 6.2 + 5.8 * heavy + 0.8 * slice(h, 8, 7)
  const stop = clamp(along, -reach, reach)
  const across = rel.x * dir.y - rel.y * dir.x + 0.5 * sin(along * 0.16 + 6 * slice(h, 11, 7))
  const lift = stop / reach
  const half = (0.52 + 0.78 * heavy + 0.2 * slice(h, 14, 7)) * (1 - 0.5 * lift * lift)
  const press = 0.33 + 0.48 * heavy + 0.14 * slice(h, 17, 7)
  const dash = cover(length(vec2(along - stop, across)), half) * press * (0.68 + 0.32 * tooth)

  // Graphite dust: up to four specks a square, shown where the field is strong, creeping along it.
  let dust = 0
  let word = h
  for (const n of range(4)) {
    word = again(word)
    const home = vec2(slice(word, 0, 31) - 0.5, slice(word, 5, 31) - 0.5) * 16
    const beat = fract(time * 0.08 + slice(word, 10, 31))
    const speck = vec2(middle + home + dir * ((beat - 0.5) * 10))
    const need = 0.15 + 0.62 * slice(word, 18, 15)
    const shown = clamp((stirred - need) * 6, 0, 1) * sin(PI * beat)
    const grit = 0.6 + 0.9 * slice(word, 15, 7)
    dust = max(dust, clamp((grit - length(vec2(at - speck))) * perPixel + 0.5, 0, 1) * shown)
  }

  // No dash or dust is drawn across a wandering pole's own mark.
  const a = vec2(at - northAt)
  const b = vec2(at - southAt)
  const clear = clamp((min(length(a), length(b)) - 16.5) * 0.5, 0, 1)
  let inkLead = max(dash, dust * 0.8) * (1 - onHub) * clear
  let inkRed = 0

  // A compass: two rings, sixteen ticks, pencil shading on the far side, a diamond needle with a red
  // north half and a hatched south half, and a pivot.
  if (onHub > 0.5) {
    const c = vec2(at - hub)
    const r = length(c)
    const rim = max(cover(abs(r - 33), 0.8), cover(abs(r - 29.5), 0.3) * 0.7)
    const far = max(abs(c.x), abs(c.y))
    const near = min(abs(c.x), abs(c.y))
    const ticks = max(
      cover(near, 0.55) * between(r, 23.5, 29.5),
      max(
        cover((far - near) * 0.707, 0.4) * between(r, 25, 29.5),
        cover(abs(far * 0.3827 - near * 0.9239), 0.3) * between(r, 26.6, 29.5),
      ),
    )
    const shade =
      r < 28.6 && length(vec2(c - vec2(-6, 6))) > 27.5 ? cover(hatch(c.x + c.y, 3.6) * 0.707, 0.3) * 0.5 : 0
    const sway = 0.045 * sin(time * 1.7 + hubNo * 2.1) + 0.025 * sin(time * 2.9 + hubNo)
    const aim = vec2(dir.x - dir.y * sway, dir.y + dir.x * sway)
    const na = dot(c, aim)
    const nc = c.x * aim.y - c.y * aim.x
    const edge = (abs(nc) * 24 + abs(na) * 5 - 120) / 24.5
    const hole = r > 2.6 ? 1 : 0
    const body = inside(edge) * hole
    const north = na > 0 ? 1 : 0
    const outline = cover(abs(edge), 0.45) * hole
    const southHatch = cover(hatch(na, 2.8), 0.3) * 0.55 * (1 - north)
    const crease = cover(abs(nc), 0.25) * 0.45
    const pivot = max(cover(abs(r - 2.6), 0.45), inside(r - 0.9))
    inkRed = body * north * (nc > 0 ? 0.95 : 0.72) * (0.84 + 0.16 * tooth)
    inkLead = max(
      max(rim * 0.82, max(ticks * 0.7, shade)),
      max(max(outline * 0.85, body * max(southHatch, crease)), pivot * 0.9),
    )
  }

  // The wandering poles' marks: a ringed N in red pencil, a ringed S in graphite.
  const letterN = min(
    toStroke(a, vec2(-4, 0), vec2(0, 1), 6),
    min(toStroke(a, vec2(0, 0), vec2(0.5547, -0.8321), 7.21), toStroke(a, vec2(4, 0), vec2(0, 1), 6)),
  )
  const markN = max(cover(abs(length(a) - 15), 0.85), cover(letterN, 0.7))
  const up = vec2(b - vec2(0, 3.2))
  const low = vec2(b + vec2(0, 3.2))
  const upGap = up.x > 0 && up.y < 0 ? 9 : abs(length(up) - 3.2)
  const lowGap = low.x < 0 && low.y > 0 ? 9 : abs(length(low) - 3.2)
  const markS = max(cover(abs(length(b) - 15), 0.85), cover(min(upGap, lowGap), 0.7))

  inkRed = max(inkRed, max(markN * 0.88, ringRed))
  inkLead = max(inkLead, max(markS * 0.88, ringLead))

  let color = vec3(paper * (1 - 0.035 * (tooth - 0.5)))
  color = vec3(mix(color, ruled, max(fine * 0.45, bold * 0.8)))
  color = vec3(mix(color, lead, inkLead))
  color = vec3(mix(color, redLead, inkRed))
  return vec4(color, 1)
})

export default shader({ fps: 30, passes: [sheet] })
