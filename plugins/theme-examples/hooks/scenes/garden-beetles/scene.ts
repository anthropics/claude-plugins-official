// Garden Beetles: a handheld-console pixel garden behind the chat.
//
// Nine beetles and ladybirds patrol the side margins one pixel step at a time, leaving dotted
// footprints. Three of them push a keycap. Bring a pointer near and they leave it where it is,
// bolt to the nearest plant and tuck under it, two eyes among the leaves watching the pointer;
// when it is quiet a head shows, and they walk back. The stag beetle alone stands its ground.
// Around them: two files of ants along the cracks, two butterflies hopping between plants, dew,
// moss, and a few motes on the air.
//
// How it is drawn: the whole window is one small screen of 6-point pixels. A tiny 8-bit buffer
// (sim) remembers, for each bug, where it is on its loop and how scared it is. A second small
// buffer (draw) holds the finished pixel picture, one texel per big pixel, and keeps the
// footprints in its alpha lane. The picture pass only enlarges that with crisp pixel edges, so
// nearly all of the cost stays the same whatever the sharpness of the screen.
// Nothing here is a bitmap: each bug is a row-by-row girth profile plus a few rules, each plant
// three or four discs, and every colour one of sixteen.
import {
  abs, buffer, clamp, composer, dt, first, floor, fract, frame, int, max, min, mix, mod, picture, pointers,
  px, scene, shader, sign, size, sqrt, step, table, time, unsigned, vec2, vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

/** Points per big pixel. */
const PX = 6
const BUGS = 9
const LEAVES = 12
const MOTES = 6
const WINGS = 2
/** Paving tile, in big pixels. */
const TILE = 16

// The two 16-colour palettes, 0 to 255: rows 0 to 15 are "Moss at dusk" (dark), 16 to 31 "Sunlit patio" (light).
//  0 tile   1 tile, second tone   2 joint   3 fresh footprint
//  4 leaf shade   5 leaf   6 leaf light   7 ink (the outline)   8 cream
//  9 red   10 orange   11 teal   12 mint   13 amber   14 plum   15 brown
const INK = 7
const CREAM = 8
const paint = table([
  [38, 56, 57], [41, 61, 62], [29, 44, 46], [68, 96, 94],
  [24, 68, 48], [40, 106, 74], [70, 148, 92], [7, 12, 14], [242, 233, 207],
  [217, 84, 63], [241, 154, 91], [43, 156, 151], [143, 224, 196], [232, 176, 74], [138, 99, 194], [154, 95, 60],
  [236, 229, 211], [230, 222, 201], [214, 204, 179], [191, 179, 148],
  [60, 122, 72], [99, 168, 90], [156, 207, 120], [42, 40, 54], [255, 250, 240],
  [216, 79, 60], [243, 154, 98], [42, 157, 150], [159, 227, 205], [230, 169, 58], [139, 98, 196], [163, 100, 62],
])

// One row per bug: where it lives (0 left margin, 1 right margin, 2 the whole window),
// its kind (0 ladybird, 1 scarab, 2 stag beetle), its shell colour and its glint colour.
const cast = table([
  [0, 0, 9, 10], [0, 1, 11, 12], [0, 0, 13, 8], [0, 2, 15, 13],
  [1, 0, 13, 8], [1, 0, 9, 10], [1, 1, 14, 12], [1, 1, 11, 12],
  [0, 1, 14, 12],
])
// One row per bug: pixels walked a second, where on its loop it starts (0 to 1),
// the keycap it pushes (0 none, 1 semicolon, 2 brace, 3 bracket), seconds between rests.
// Bugs 3 and 8 share one loop half a lap apart, so they share a pace and a rhythm.
const gait = table([
  [7, 0.1, 0, 9], [5, 0.55, 0, 13], [7, 0.3, 0, 8], [5, 0.08, 2, 16],
  [6, 0.35, 0, 11], [7, 0.05, 0, 7], [5, 0.6, 0, 14], [5, 0.3, 3, 12],
  [5, 0.58, 1, 16],
])
// Each bug's loop: six corners as shares of its home (across, up), then the first again.
// Every leg of a loop runs straight across or straight up. In each margin three bugs keep to
// a patch of their own, one above the other, and the keycap pushers walk the lane around them,
// so no two loops cross. The lane keeps a little clear of the text column.
const route = table([
  [0.34, 0.86], [0.66, 0.86], [0.66, 0.68], [0.5, 0.68], [0.5, 0.76], [0.34, 0.76], [0.34, 0.86],
  [0.66, 0.59], [0.34, 0.59], [0.34, 0.41], [0.66, 0.41], [0.66, 0.41], [0.66, 0.59], [0.66, 0.59],
  [0.34, 0.32], [0.66, 0.32], [0.66, 0.14], [0.5, 0.14], [0.5, 0.22], [0.34, 0.22], [0.34, 0.32],
  [0.125, 0.95], [0.86, 0.95], [0.86, 0.05], [0.125, 0.05], [0.125, 0.05], [0.125, 0.95], [0.125, 0.95],
  [0.66, 0.86], [0.34, 0.86], [0.34, 0.68], [0.66, 0.68], [0.66, 0.68], [0.66, 0.86], [0.66, 0.86],
  [0.34, 0.59], [0.5, 0.59], [0.5, 0.51], [0.66, 0.51], [0.66, 0.41], [0.34, 0.41], [0.34, 0.59],
  [0.66, 0.32], [0.34, 0.32], [0.34, 0.14], [0.66, 0.14], [0.66, 0.14], [0.66, 0.32], [0.66, 0.32],
  [0.875, 0.95], [0.14, 0.95], [0.14, 0.05], [0.875, 0.05], [0.875, 0.05], [0.875, 0.95], [0.875, 0.95],
  [0.125, 0.95], [0.86, 0.95], [0.86, 0.05], [0.125, 0.05], [0.125, 0.05], [0.125, 0.95], [0.125, 0.95],
])
// The big plants the bugs hide under: home, across, up, and which way it is turned
// (0 to 3 are quarter turns of a three-leaf plant; 4 is the lucky one). Five to a margin, one
// in the middle of each patch and one in each lane, so cover is never far; two more peep in at
// the top and bottom of the text column.
const hides = table([
  [0, 0.5, 0.77, 0], [0, 0.5, 0.5, 1], [0, 0.5, 0.23, 2], [0, 0.125, 0.36, 3], [0, 0.8, 0.64, 2],
  [1, 0.5, 0.77, 1], [1, 0.5, 0.5, 3], [1, 0.5, 0.23, 4], [1, 0.875, 0.64, 0], [1, 0.2, 0.36, 2],
  [2, 0.45, 0.99, 2], [2, 0.6, 0.01, 0],
])
// Half the width of each bug, row by row from the head: ladybird, scarab, stag beetle.
const girth = table([
  [0, 0, 0], [0, 2, 0], [3, 3, 3], [4, 4, 4], [5, 5, 3], [6, 5, 5], [6, 5, 5],
  [6, 5, 5], [6, 5, 5], [6, 5, 5], [5, 4, 4], [4, 3, 3], [0, 0, 0],
])
// The rows the three pairs of legs leave from, for each kind.
const hips = table([[5, 7, 9], [3, 6, 9], [3, 6, 9]])

/** One of three numbers, by kind. */
function pick(v: vec3, kind: number): number {
  return kind < 0.5 ? v.x : kind < 1.5 ? v.y : v.z
}

/**
 * A bit mixer made for this scene: shifts, adds and exclusive-ors only.
 * Gives 0 to 1 for a pair of whole numbers.
 */
function grit(a: number, b: number): number {
  let h = int(a) + (int(b) << 11) + 7717
  h += h << 14
  h ^= h >>> 8
  h += h << 7
  h ^= h >>> 20
  h += h << 18
  h ^= h >>> 22
  h += h << 2
  h ^= h >>> 9
  h += h << 23
  h ^= h >>> 7
  return unsigned(h) / 4294967296
}

/** The screen in big pixels. */
function screenW(): number { return floor(size.x / PX + 0.5) }
function screenH(): number { return floor(size.y / PX + 0.5) }

/**
 * How wide a home is, in big pixels. The margins run from the window's edge to the prompt box,
 * and are never taken as less than 36.
 */
function room(home: number, W: number): number {
  const known = composer.z - composer.x > 0.05
  return home < 0.5 ? max((known ? composer.x : 0.26) * W, 36) : home < 1.5 ? max((known ? 1 - composer.z : 0.26) * W, 36) : W
}

/** Across, in big pixels, for a share of a home. */
function across(home: number, share: number, W: number): number {
  const wide = room(home, W)
  return floor(home < 0.5 ? share * wide : home < 1.5 ? W - wide + share * wide : share * W)
}

/** The pixel a given number of steps along bug i's loop, and which way the loop heads there: [x, y, headX, headY]. */
function spot(i: number, home: number, steps: number, W: number, H: number): [number, number, number, number] {
  let x = 0
  let y = 0
  let headX = 0
  let headY = 1
  let done = 0
  for (let k = 0; k < 6; k++) {
    const a = route.at(i * 7 + k)
    const b = route.at(i * 7 + k + 1)
    const ax = across(home, a.x, W)
    const ay = floor(a.y * H)
    const bx = across(home, b.x, W)
    const by = floor(b.y * H)
    const leg = abs(bx - ax) + abs(by - ay)
    if (steps >= done && steps < done + leg) {
      const into = floor(steps - done)
      headX = sign(bx - ax)
      headY = sign(by - ay)
      x = ax + headX * into
      y = ay + headY * into
    }
    done += leg
  }
  return [x, y, headX, headY]
}

/** Where an ant road runs in a margin: the up-and-down joint nearest the margin's middle. */
function antLane(road: number, W: number): number {
  return floor(across(road, 0.5, W) / TILE + 0.5) * TILE
}

/**
 * An amount to add to an 8-bit lane this frame, as a whole number of its 255 steps: one more on
 * some frames than on others (by the roll of the mixer), so that slow rates come out right at
 * any frame rate and never stall.
 */
function drip(amount: number, salt: number): number {
  return floor(amount * 255 + grit(frame, salt)) / 255
}

/** Two bytes for a whole number up to 65535. */
function low(n: number): number { return (n - floor(n / 256) * 256) / 255 }
function high(n: number): number { return floor(n / 256) / 255 }
function whole(lo: number, hi: number): number { return floor(lo * 255 + 0.5) + floor(hi * 255 + 0.5) * 256 }

// sim: 16 by 5 texels of 8 bits. Column i is bug i. Row 0 keeps its state from frame to frame:
// (place on the loop, high byte and low byte; dash, 0 walking to 1 tucked under a leaf;
// nerves, 1 just frightened falling to 0 calm). Rows 1 to 4 are this frame's pose for draw to
// read: where the bug is, where it left its loop, which way it faces (with whether it is bolting
// and whether it is airing its wings), and where its keycap is.
// The seven columns past the bugs hold the ants' wariness (see below).
const sim: Buffer = buffer({ size: [16, 5] }, (p): vec4 => {
  const i = p.cell.x
  const W = screenW()
  const H = screenH()
  const who = cast.at(i)
  const how = gait.at(i)
  const kept = sim.at(vec2(i, 0))
  let place = whole(kept.g, kept.r) / 65536
  let dash = kept.b
  let nerves = kept.a
  if (first) {
    place = how.y
    dash = 0
    nerves = 0
  }

  // The loop's length, then where this place on it falls.
  let lap = 0
  for (let k = 0; k < 6; k++) {
    const a = route.at(i * 7 + k)
    const b = route.at(i * 7 + k + 1)
    lap += abs(across(who.x, b.x, W) - across(who.x, a.x, W)) + abs(floor(b.y * H) - floor(a.y * H))
  }
  const walked = place * lap
  const [homeX, homeY, headX, headY] = spot(i, who.x, walked, W, H)
  // The keycap a bug pushes rides eleven steps further along the same loop, so it turns each corner first.
  const [capX, capY] = spot(i, who.x, mod(walked + 11, max(lap, 1)), W, H)

  // The nearest plant, counted in steps across plus steps up.
  let leafX = homeX
  let leafY = homeY
  let nearest = 100000
  for (let j = 0; j < LEAVES; j++) {
    const h = hides.at(j)
    const x = across(h.x, h.y, W)
    const y = floor(h.z * H)
    const far = abs(x - homeX) + abs(y - homeY)
    if (far < nearest) {
      nearest = far
      leafX = x
      leafY = y
    }
  }
  // Each bug has its own spot under a plant, so two that share one do not sit on the same pixels.
  leafX += (mod(i, 3) - 1) * 3
  leafY += (floor(i / 3) - 1) * 2

  // The dash is L-shaped: the longer leg first, then the shorter.
  const runX = leafX - homeX
  const runY = leafY - homeY
  const runLength = abs(runX) + abs(runY)
  const wide = abs(runX) >= abs(runY)
  const far = floor(dash * runLength + 0.5)
  const firstLeg = wide ? abs(runX) : abs(runY)
  const onFirst = min(far, firstLeg)
  const onSecond = far - onFirst
  const x = homeX + sign(runX) * (wide ? onFirst : onSecond)
  const y = homeY + sign(runY) * (wide ? onSecond : onFirst)
  const inFirst = far < firstLeg || runLength - firstLeg < 0.5
  const runHeadX = (wide ? inFirst : !inFirst) ? sign(runX) : 0
  const runHeadY = (wide ? inFirst : !inFirst) ? 0 : sign(runY)

  // Who is near? Each live pointer frightens a circle; a press reaches further, a pointer over
  // the app's own panels less far, and every extra pointer widens all of them.
  let live = 0
  for (const finger of pointers) live += 1 - step(0.3, finger.gone)
  let fright = 0
  for (const finger of pointers) {
    const fx = finger.at.x / PX
    const fy = finger.at.y / PX
    const reach = (17 + 9 * finger.down) * (1 - 0.3 * finger.over) * (1 + 0.25 * max(live - 1, 0))
    const fromBug = sqrt((fx - x) * (fx - x) + (fy - y) * (fy - y))
    const fromHome = sqrt((fx - homeX) * (fx - homeX) + (fy - homeY) * (fy - homeY))
    if (finger.gone < 0.3 && (fromBug < reach || fromHome < reach * 0.8)) fright = 1
  }

  // Frightened: nerves jump to 1. Left alone they settle: tucked until 0.5, peeking until 0.14, then home.
  // The stag beetle is the brave one: it never runs, it stops where it is and snaps its jaws.
  nerves = fright > 0.5 ? 1 : max(0, nerves - drip(dt / 3.6, i))
  const brave = who.y > 1.5
  const peek = clamp(1 - 8 / max(runLength, 1), 0, 1)
  const goal = brave ? 0 : nerves > 0.5 ? 1 : nerves > 0.14 ? peek : 0
  // It bolts at 90 pixels a second however far the plant is, edges out to peek at 16, and
  // walks home at its own pace.
  const pace = drip((goal > dash ? 90 : goal > 0.001 ? 16 : how.x) * dt / max(runLength, 1), i + 40)
  dash += clamp(goal - dash, -pace, pace)

  // Walk on only when calm, with a short rest every so often.
  const beat = fract(time / how.w + how.y * 7)
  let stride = step(0.2, beat)
  // Bugs 3 and 8 share a loop: whichever comes up close behind the other waits for it to move on.
  if (i == 3 || i == 8) {
    const mate = sim.at(vec2(i == 3 ? 8 : 3, 0))
    const ahead = fract(whole(mate.g, mate.r) / 65536 - place) * lap
    if (ahead < 32) stride = 0
  }
  // In the middle of a rest a ladybird lifts its wing cases for a moment.
  const calm = dash < 0.002 && nerves < (brave ? 0.5 : 0.002)
  const airing = calm && beat > 0.05 && beat < 0.15 ? 1 : 0
  if (calm) place = fract(place + stride * how.x * dt / max(lap, 1))

  // Which way it faces: along its loop, along the dash on the way in, and outward while tucked or coming out.
  let faceX = headX
  let faceY = headY
  if (dash > 0.002 && runLength > 0.5) {
    const inward = goal > dash + 0.002 ? 1 : -1
    faceX = runHeadX * inward
    faceY = runHeadY * inward
  }
  const facing = faceY > 0.5 ? 0 : faceX > 0.5 ? 1 : faceY < -0.5 ? 2 : 3

  // The seven spare columns remember how wary each stretch of the two ant roads is: four
  // stretches to a texel, each four pixels of road. Wariness jumps up near a pointer and ebbs
  // away slowly, so a pointer swept back and forth parts the file once instead of shaking it.
  if (i > 8.5) {
    if (p.cell.y > 3.5) return vec4(0, 0, 0, 0)
    const road = p.cell.y < 1.5 ? 0 : 1
    const first4 = ((i - 9) * 2 + p.cell.y - road * 2) * 4
    const was = sim.at(p.cell)
    const wary = [was.r, was.g, was.b, was.a]
    const lane = antLane(road, W)
    for (const k of [0, 1, 2, 3]) {
      const up = (first4 + k) * 4 + 2
      const rx = lane + mod(floor(up / TILE), 2) * (TILE / 2)
      let near = 0
      for (const finger of pointers) {
        const ax = finger.at.x / PX - rx
        const ay = finger.at.y / PX - up
        if (finger.gone < 0.3 && ax * ax + ay * ay < 170) near = 1
      }
      wary[k] = first ? 0 : wary[k]! + clamp(near - wary[k]!, -drip(dt / 1.6, i * 8 + k), dt / 0.12)
    }
    return vec4(wary[0]!, wary[1]!, wary[2]!, wary[3]!)
  }

  const steps = floor(place * 65536)
  if (p.cell.y < 0.5) return vec4(high(steps), low(steps), dash, nerves)
  if (p.cell.y < 1.5) return vec4(low(x), high(x), low(y), high(y))
  if (p.cell.y < 2.5) return vec4(low(homeX), high(homeX), low(homeY), high(homeY))
  if (p.cell.y < 3.5) return vec4(facing / 3, goal > 0.999 ? 1 : 0, 0, airing)
  return vec4(low(capX), high(capX), low(capY), high(capY))
})

// The drawing rules. Each returns a code, not a colour: 0 nothing, 1 ink, 2 body, 3 sheen, 4 cream,
// and for a bug 5 is a leg or a feeler.

/**
 * One pixel of a bug seen from above with its head up. side is pixels right of its middle,
 * row counts from 0 at the head to 12 at the tail. legs is 0 or 1, the two frames of its gait.
 * twitch is 1 while the antenna on this side is flicked. airing is 1 while a ladybird holds its wing cases open.
 */
function bugPixel(kind: number, side: number, row: number, legs: number, twitch: number, airing: number): number {
  const out = abs(side)
  const wide = pick(girth.at(row), kind)
  const above = pick(girth.at(row - 1), kind)
  const below = pick(girth.at(row + 1), kind)
  let code = 0
  if (row > 0.5 && row < 11.5 && out < wide) {
    const rim = out > wide - 1.5 || out >= above || out >= below
    code = rim ? 1 : 2
    if (!rim) {
      if (kind < 0.5) {
        // Ladybird: dark head with two pale eyes, a seam and three spots a side.
        if (row < 3.5) code = 1
        if (row == 3 && out == 2) code = 4
        if (row > 3.5 && out == 0) code = 1
        if ((row == 5 && out == 2) || (row == 7 && out == 3) || (row == 9 && out == 2)) code = 1
        // Wing cases lifted: the wings show down the middle.
        if (airing > 0.5 && row > 5.5 && out == 1) code = 3
      } else if (kind < 1.5) {
        // Scarab: small dark head, a bright collar, a seam and one groove of sheen down each wing case.
        if (row < 2.5) code = 1
        if (row == 2 && out == 1) code = 4
        if (row > 2.5 && row < 4.5) code = 3
        if (row > 4.5 && out == 0) code = 1
        // The sheen slides a row with every step, as it would on a polished shell.
        if (row > 5.5 + legs && row < 8.5 + legs && out == 2) code = 3
      } else {
        // Stag beetle: broad head with pale eyes, a narrow waist, a seam, sheen on the shoulders.
        if (row == 3 && out == 2) code = 4
        if (row == 4) code = 1
        if (row > 4.5 && out == 0) code = 1
        if (row > 5.5 && row < 8.5 && out == 3) code = 3
      }
    }
    // A ladybird airing its wings shows their tips past its tail.
    if (kind < 0.5 && airing > 0.5 && row == 11 && out < 2.5 && out > 0.5) code = 4
  }
  // Legs: one pixel at the hip, one beyond it a row ahead or behind. Front and hind legs of one
  // side move with the middle leg of the other, and the two frames swap them.
  const right = side > 0 ? 1 : 0
  const hip = hips.at(kind)
  for (let j = 0; j < 3; j++) {
    const at = j < 0.5 ? hip.x : j < 1.5 ? hip.y : hip.z
    const reach = pick(girth.at(at), kind)
    const swing = mod(j + right + legs, 2) * 2 - 1
    if ((row == at && out == reach) || (row == at + swing && out == reach + 1)) code = 5
  }
  // Feelers (and the stag's jaws, which close when it twitches).
  if (kind < 0.5) {
    if (row == 1 && out == 1) code = 5
    if (row == 0 && out == 2 - twitch) code = 5
  } else if (kind < 1.5) {
    if (row == 0 && out == 2 && twitch < 0.5) code = 5
    if (row == 1 && out == 3 && twitch > 0.5) code = 5
  } else {
    // The jaws take the sheen colour so they show on dark paving too.
    if (row == 1 && out == 3) code = 3
    if (row == 0 && (out == 3 - twitch || out == 2 - twitch)) code = 3
  }
  return code
}

/** A pale keycap seven pixels wide and nine tall with a sign on it. x and y count from its lower left. */
function keycap(mark: number, x: number, y: number): number {
  if (x < 0 || x > 6 || y < 0 || y > 8) return 0
  const edgeX = x == 0 || x == 6
  const edgeY = y == 0 || y == 8
  if (edgeX && edgeY) return 0
  if (edgeX || edgeY) return 1
  const col = x - 2
  const rowUp = y - 2
  let on = 0
  if (col >= 0 && col <= 2 && rowUp >= 0 && rowUp <= 4) {
    if (mark < 1.5) {
      // a semicolon
      on = (col == 1 && (rowUp == 4 || rowUp == 2 || rowUp == 1)) || (col == 0 && rowUp == 0) ? 1 : 0
    } else if (mark < 2.5) {
      // an opening brace
      on = (col == 2 && (rowUp == 4 || rowUp == 0)) || (col == 1 && rowUp != 2) || (col == 0 && rowUp == 2) ? 1 : 0
    } else {
      // a closing bracket
      on = col == 2 || (col == 1 && (rowUp == 4 || rowUp == 0)) ? 1 : 0
    }
  }
  return on > 0.5 ? 1 : 4
}

/**
 * One pixel of a big plant, measured from its middle. turn 0 to 3 is a quarter turn; 4 has four leaves.
 * Codes: 1 shade, 2 leaf, 3 light, 4 a glinting drop of dew (only while dew is 1).
 */
function plant(turn: number, x0: number, y0: number, dew: number): number {
  const x = turn < 0.5 ? x0 : turn < 1.5 ? -y0 : turn < 2.5 ? -x0 : turn < 3.5 ? y0 : x0
  const y = turn < 0.5 ? y0 : turn < 1.5 ? x0 : turn < 2.5 ? -y0 : turn < 3.5 ? -x0 : y0
  const lucky = turn > 3.5
  // Squared distance to each leaflet's middle.
  const top = x * x + (y - (lucky ? 5 : 4)) * (y - (lucky ? 5 : 4))
  const west = lucky ? (x + 5) * (x + 5) + y * y : (x + 4) * (x + 4) + (y + 3) * (y + 3)
  const east = lucky ? (x - 5) * (x - 5) + y * y : (x - 4) * (x - 4) + (y + 3) * (y + 3)
  const south = lucky ? x * x + (y + 5) * (y + 5) : 1000
  const near = min(min(top, west), min(east, south))
  let code = 0
  if (near <= 17) {
    code = near >= 11 ? 1 : 2
    // A dark crease where two leaflets of the three meet: where the nearest two are all but equally near.
    const second = top + west + east - near - max(max(top, west), east)
    if (!lucky && second - near < 2.5) code = 1
    // The pale chevron each leaflet wears, two pixels out from the middle of the plant.
    if (code == 2 && near >= 3 && near <= 6 && ((top == near && y < (lucky ? 5 : 4)) || (south == near && y > -5) || (west == near && x > (lucky ? -5 : -4)) || (east == near && x < (lucky ? 5 : 4)))) code = 3
  }
  if (dew > 0.5 && x == -1 && y == (lucky ? 6 : 5)) code = 4
  // The stalk, from the middle out between the two lower leaflets.
  if (!lucky && code == 0 && ((x == 0 && y < 0 && y > -7.5) || (x == 1 && y == -8))) code = 1
  return code
}

/** A small plant sprig, five pixels square, from its lower left: 1 dark, 2 leaf. */
function sprig(x: number, y: number): number {
  if (x < 0 || x > 4 || y < 0 || y > 4) return 0
  if (x == 2 && y < 2.5) return 1
  if ((y == 3 && x != 2) || (y == 2 && (x == 1 || x == 3)) || (y == 4 && (x == 0 || x == 4))) return 2
  return 0
}

// draw: the finished pixel picture, one texel per big pixel. rgb is the colour; alpha is how
// fresh the footprint on that pixel is.
const draw: Buffer = buffer({ scale: 1 / PX, filter: 'linear' }, (p): vec4 => {
  const x = p.cell.x
  const y = p.cell.y
  const W = screenW()
  const H = screenH()

  // Light or dark? The Svg under the shader knows; its middle pixel is bare paving in either mode.
  const under = scene.sample(vec2(0.5, 0.5))
  const day = step(0.4, under.r * 0.2126 + under.g * 0.7152 + under.b * 0.0722)

  // Paving: rows of tiles, every other row shifted half a tile, one tile in three a shade off.
  const course = floor(y / TILE)
  const shifted = x + mod(course, 2) * (TILE / 2)
  const tile = floor(shifted / TILE)
  const inX = shifted - tile * TILE
  const inY = y - course * TILE
  const roll = grit(tile, course)
  let slot = roll < 0.3 ? 1 : 0
  if (inX == 0 || inY == 0) slot = 2
  // A chipped corner here and there, a hairline crack across one tile in ten, and moss in the joints.
  if (roll > 0.86 && ((inX == 1 && inY == 1) || (inX == 2 && inY == 1) || (inX == 1 && inY == 2))) slot = 2
  const flaw = grit(tile + 53, course + 7)
  if (flaw < 0.1 && inX > 3.5 && inX < 10.5 && inX + floor(flaw * 60) == inY + 4 + floor(inX / 4)) slot = 2
  const mossy = slot == 2 && flaw > 0.8 && grit(x, y) < 0.2

  // Moss is the quiet green of each palette: the pale one by day, the deep one at dusk.
  if (mossy) slot = day > 0.5 ? 6 : 4

  // Footprints fade in two steps. They lie on the paving, under everything that grows or walks.
  // A print lasts about seven seconds.
  let print = max(draw.at(p.cell).a - drip(dt / 7, x * 7 + y * 131), 0)
  if (print > 0.5) slot = 3
  else if (print > 0.1 && slot != 2) slot = 2

  // Small plant sprigs grow out of some joints.
  const lot = grit(tile + 31, course + 17)
  if (lot < 0.16) {
    const s = sprig(inX - floor(lot * 60), inY + 2 - floor(lot * 12))
    if (s > 0.5) slot = 5
  }
  const lot2 = grit(tile + 5, course + 71)
  if (lot2 < 0.08) {
    const s = sprig(inX - 6 - floor(lot2 * 90), inY - 7 - floor(lot2 * 60))
    if (s > 0.5) slot = s < 1.5 ? 5 : 6
  }
  // And, rarely, a four-petalled flower.
  const lot3 = grit(tile + 97, course + 41)
  if (lot3 < 0.07) {
    const petalX = abs(inX - 4 - floor(lot3 * 120))
    const petalY = abs(inY - 5 - floor(lot3 * 100))
    if (petalX + petalY == 1) slot = 14
    if (petalX + petalY == 0) slot = 13
  }

  // Two files of ants follow the cracks up one margin and down the other: up a joint, along to the
  // next, up again. Near a pointer they break file to either side, and drift back into line when
  // it has gone.
  for (let side = 0; side < 2; side++) {
    const lane = antLane(side, W)
    const jog = mod(course, 2) * (TILE / 2)
    const off = x - lane - jog
    // How wary this stretch of road is, from sim's spare texels.
    const stretch = min(floor(y / 4), 55)
    const kept = sim.at(vec2(9 + floor(stretch / 8), side * 2 + floor(mod(stretch, 8) / 4)))
    const which = mod(stretch, 4)
    const shy = which < 0.5 ? kept.r : which < 1.5 ? kept.g : which < 2.5 ? kept.b : kept.a
    // How far along the road this pixel is: 24 to a course, 16 up the joint and 8 along to the next.
    const onJoint = inY > 0.5 || off == 0
    const along = onJoint ? course * 24 + inY : course * 24 - 8 + (mod(course, 2) > 0.5 ? x - lane : lane + TILE / 2 - x)
    const onLink = inY == 0 && x >= lane && x <= lane + TILE / 2
    // The road is cut into places of seven pixels; seven in ten hold an ant, somewhere in the
    // first four pixels of its place, so the file is ragged and not a dashed line.
    const march = along + (side < 0.5 ? -1 : 1) * time * 5
    const ant = floor(march / 7)
    const luck = grit(ant, side + 3)
    const part = march - ant * 7 - mod(floor(luck * 29), 4)
    const stray = floor(shy * 3 + 0.5) * (mod(ant, 2) * 2 - 1)
    if (luck > 0.3 && ((onJoint && off == stray) || (onLink && !onJoint && shy < 0.1))) {
      // Tail, then head, then (for one in three) the crumb it carries in front.
      const front = side < 0.5 ? part : 2.999 - part
      if (front >= 0 && front < 1) slot = 15
      else if (front >= 1 && front < 2) slot = day > 0.5 ? INK : 15
      else if (front >= 2 && front < 3 && luck > 0.75) slot = luck > 0.92 ? 12 : CREAM
    }
  }

  // Shadows first: every plant, keycap and bug darkens the paving one pixel down and to the right.
  let shade = 0
  for (let j = 0; j < LEAVES; j++) {
    const h = hides.at(j)
    const lx = x - 1 - across(h.x, h.y, W)
    const ly = y + 1 - floor(h.z * H)
    if (abs(lx) < 10.5 && abs(ly) < 10.5 && plant(h.w, lx, ly, 0) > 0.5) shade = 1
  }

  // Where the pointers are, taken together: tucked bugs glance that way.
  let seenX = 0
  let seen = 0
  for (const finger of pointers) {
    const live = finger.gone < 0.3 ? 1 : 0
    seenX += live * finger.at.x / PX
    seen += live
  }

  let alarm = 0
  let watching = 0
  let limb = 0
  for (let i = 0; i < BUGS; i++) {
    const state = sim.at(vec2(i, 0))
    const here = sim.at(vec2(i, 1))
    const home = sim.at(vec2(i, 2))
    const pose = sim.at(vec2(i, 3))
    const who = cast.at(i)
    const how = gait.at(i)
    const bx = whole(here.r, here.g)
    const by = whole(here.b, here.a)
    const hx = whole(home.r, home.g)
    const hy = whole(home.b, home.a)
    const dash = state.b
    const facing = floor(pose.r * 3 + 0.5)
    const fx = facing == 1 ? 1 : facing == 3 ? -1 : 0
    const fy = facing == 0 ? 1 : facing == 2 ? -1 : 0
    const dx = x - bx
    const dy = y - by
    // Where a margin is too slim for a lane around the patches, the keycap pushers stay away.
    const shown = how.z < 0.5 || room(who.x, W) > 50

    // Stamp a footprint under the tail on every third step, left foot and right foot in turn.
    const trod = fx != 0 ? bx : by
    const foot = mod(floor(trod / 3), 2) * 2 - 1
    if (shown && dash < 0.97 && mod(trod, 3) < 0.5 && dx == -3 * fx + 2 * foot * fy && dy == -3 * fy - 2 * foot * fx) print = 1

    // The keycap it pushes: sim keeps it eleven steps ahead on the loop, and there it stays when the bug bolts.
    if (shown && how.z > 0.5) {
      const cap = sim.at(vec2(i, 4))
      const kx = whole(cap.r, cap.g)
      const ky = whole(cap.b, cap.a)
      const k = keycap(how.z, x - kx + 3, y - ky + 4)
      if (k > 0.5) slot = k > 3.5 ? CREAM : INK
      else if (keycap(how.z, x - kx + 2, y - ky + 5) > 0.5) shade = 1
    }
    // Four specks of dust lie where it bolted from while a pointer is near, and for about a second after.
    const bolted = shown && state.a > 0.75 && dash > 0.05
    if (bolted && ((x == hx - 6 && y == hy - 1) || (x == hx + 5 && y == hy + 2) || (x == hx - 1 && y == hy - 6) || (x == hx + 6 && y == hy - 2))) slot = 3

    if (shown && abs(dx) < 7.5 && abs(dy) < 7.5) {
      const row = 6 - (dx * fx + dy * fy)
      const side = dx * fy - dy * fx
      // Feelers flick now and then, each side in its own time. A stag beetle with a pointer near snaps its jaws.
      const beat = grit(floor(time + i * 0.37), i * 13 + 3)
      const flick = side < 0 ? step(0.82, beat) : 1 - step(0.16, beat)
      const twitch = who.y > 1.5 && state.a > 0.5 ? step(0.5, fract(time)) : flick
      // Its legs swap every four pixels walked, feet to the ground: under one full swing a second at
      // every pace a bug walks its loop or walks home. (Edging out to peek is quicker, for eight pixels.)
      const stepping = mod(floor((bx + by) / 4), 2)
      // Bolting, it is drawn as a smear: a dark head and the rest of its shape in its shell colour,
      // with no outline, legs or markings.
      const bolting = pose.g > 0.5 && dash < 0.97
      const code = bugPixel(who.y, side, row, stepping, twitch, pose.a)
      // Its shadow: bare paving is shaded where the bug covers the pixel up and to the left of it.
      if (code < 0.5 && bugPixel(who.y, side - fy - fx, row + fx - fy, stepping, twitch, pose.a) > 0.5) shade = 1
      if (bolting && code > 0.5) {
        shade = 0
        if (code < 4.5) slot = row < (who.y < 0.5 ? 3.5 : 2.5) ? INK : who.z
      } else if (code > 0.5) {
        shade = 0
        // (A ladybird's only sheen is its lifted wings, which are orange on the red ones and the amber ones alike.)
        // Legs and feelers are ink by day and brown at dusk, where ink would vanish into the paving.
        slot = code < 1.5 ? INK : code < 2.5 ? who.z : code < 3.5 ? (who.y < 0.5 ? 10 : who.w) : code < 4.5 ? CREAM : day > 0.5 ? INK : 15
        // One glint, always from the upper left of the screen whichever way the bug is turned.
        const gx = dx + 2 * fx
        const gy = dy + 2 * fy
        if (code == 2 && ((gx == -2 && gy == 2) || (gx == -3 && gy == 1))) slot = who.w
        // And a shade along the lower right, borrowed from a darker colour of the palette.
        if (code == 2 && gx - gy > 3.5) slot = who.z == 9 ? 15 : who.z == 13 ? 10 : who.z == 11 ? 5 : who.z
      }
    }
    // Tucked under its plant it keeps watch: two pale eyes among the leaves that blink and glance
    // toward the pointers, and the tips of its feelers above them.
    if (shown && dash > 0.97) {
      const glance = seen < 0.5 ? 0 : seenX / seen - bx > 6 ? 1 : seenX / seen - bx < -6 ? -1 : 0
      if (y == by && abs(dx - glance) == 1 && fract(time * 0.37 + i * 0.31) > 0.07) watching = 1
      if (y == by + 2 && abs(dx) == 2) limb = 1
    }
    // A startled mark stands where it bolted from, and stays there as long as the dust does.
    if (bolted) {
      const ex = x - hx - 6
      const ey = y - hy - 5
      if (ex >= 0 && ex <= 2 && ey >= 0 && ey <= 6) alarm = ex == 1 && (ey == 1 || ey > 2.5) && ey < 5.5 ? 2 : 1
    }
  }

  // A shadow only darkens bare paving.
  if (shade > 0.5 && (slot < 1.5 || slot == 3)) slot = 2

  // The big plants lie over everything that walks. Now and then a drop of dew on one catches the light.
  for (let j = 0; j < LEAVES; j++) {
    const h = hides.at(j)
    const lx = x - across(h.x, h.y, W)
    const ly = y - floor(h.z * H)
    if (abs(lx) < 10.5 && abs(ly) < 10.5) {
      const code = plant(h.w, lx, ly, fract(time * 0.13 + j * 0.37) < 0.06 ? 1 : 0)
      if (code > 0.5) slot = code < 1.5 ? 4 : code < 2.5 ? 5 : code < 3.5 ? 6 : CREAM
    }
  }
  if (limb > 0.5) slot = day > 0.5 ? INK : 15
  if (watching > 0.5) slot = CREAM
  if (alarm > 0.5) slot = alarm > 1.5 ? 13 : INK

  // Two butterflies (moths, by night) flit from plant to plant in their own margin: a few seconds
  // perched with slow wings, then a hop in an arc. A pointer nearby pushes them off course.
  for (let b = 0; b < WINGS; b++) {
    const hop = time / 9 + b * 0.45
    const leg = floor(hop)
    const part = fract(hop)
    const from = hides.at(b * 5 + mod(leg, 5))
    const to = hides.at(b * 5 + mod(leg + 1, 5))
    const flight = clamp((part - 0.6) / 0.4, 0, 1)
    const glide = flight * flight * (3 - 2 * flight)
    const lift = 4 * glide * (1 - glide)
    let wx = mix(across(from.x, from.y, W), across(to.x, to.y, W), glide) + 1
    let wy = mix(floor(from.z * H), floor(to.z * H), glide) + 3 + lift * 9
    for (const finger of pointers) {
      const ax = wx - finger.at.x / PX
      const ay = wy - finger.at.y / PX
      const away = sqrt(ax * ax + ay * ay)
      // (The push eases off over the second a lifted pointer lingers, so the butterfly glides back.)
      const push = clamp(1 - finger.gone, 0, 1) * clamp(1 - away / 24, 0, 1) * 12 / max(away, 1)
      wx += ax * push
      wy += ay * push
    }
    const ux = x - floor(wx)
    const uy = y - floor(wy)
    // Wings beat quickly in flight and slowly at rest: wide open, or folded to a sliver.
    const open = fract(time * (flight > 0.001 && flight < 0.999 ? 1 : 0.6) + b * 0.3) < 0.55
    const spread = abs(ux)
    // Its shadow falls further away the higher it flies.
    const height = 2 + floor(lift * 3)
    const sx = abs(ux - height)
    const sy = uy + height
    if (sy >= -1 && sy <= 1 && (sx == 0 || (open ? sx <= 2 && !(sx == 2 && sy == -1) : sx == 1 && sy >= 0)) && (slot < 1.5 || slot == 3)) slot = 2
    if (uy >= -1 && uy <= 1) {
      if (spread == 0) slot = INK
      else if (open && spread <= 2 && !(spread == 2 && uy == -1)) slot = spread == 2 && uy == 1 ? CREAM : b < 0.5 ? 10 : 12
      else if (!open && spread == 1 && uy >= 0) slot = b < 0.5 ? 10 : 12
    }
  }

  // Six motes drift across on the air, one pixel each: fireflies at dusk, pollen by day. Each blinks out now and then.
  for (let m = 0; m < MOTES; m++) {
    const from = grit(m, 11)
    const level = grit(m, 29)
    const speed = (from - 0.5) * 3
    const mx = floor(mod(from * W + time * speed, W))
    const my = floor(level * H + abs(fract(time * 0.11 + from) - 0.5) * 12)
    if (x == mx && y == my && fract(time * 0.19 + level) < 0.72) slot = 13
  }

  const colour = mix(paint.at(slot), paint.at(slot + 16), day)
  return vec4(colour.r / 255, colour.g / 255, colour.b / 255, print)
})

// The picture: each big pixel enlarged, with edges one screen pixel soft so they stay crisp at any sharpness.
const view = picture(p => {
  const at = vec2(p.uv * draw.size)
  const cell = vec2(floor(at))
  const part = vec2(at - cell)
  const grow = PX / px
  const lean = vec2(clamp(part * grow, 0, 0.5) - 0.5 + clamp((part - 1) * grow + 0.5, 0, 0.5))
  return vec4(draw.sample(vec2((cell + 0.5 + lean) / draw.size)).rgb, 1)
})

export default shader({ fps: 60, passes: [sim, draw, view] })
