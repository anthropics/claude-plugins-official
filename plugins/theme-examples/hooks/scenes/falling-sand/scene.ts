// Falling Sand: coarse pixel-art sand on a 6 point grid. One buffer texel is one grain.
// Three small buffers at one texel a cell, then the picture. The first holds what stands in each cell. The second
// keeps the grains: a block automaton that moves things only by swapping two cells, so nothing is lost or doubled
// in motion. The third paints the pixel art. The picture only enlarges the third, so the buffers cost the same at
// any sharpness. Light and dark come from the still Svg's middle pixel.
import {
  abs, buffer, clamp, composer, dot, dt, floor, fract, first, fresh, int, max, min, mix, mod,
  picture, pointers, res, scene, shader, sin, size, sqrt, step, time, turn, unsigned, vec2, vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

const CELL = 6

// A number from 0 to 1 out of three whole numbers, for everything here that is left to chance. The mix is this file's own:
// the three are folded in one at a time, and each fold is stirred by adding a turned copy of the word to itself,
// between multiplies by odd constants.
const rnd = (a: number, b: number, c: number): number => {
  let h = int(int(a) * 58479 + 6251)
  h = int(h ^ (h << 7))
  h = int(h + int(b) * 60027)
  h = int(h + ((h << 13) | (h >>> 19)))
  h = int(h ^ (int(c) * 28355))
  h = int(h * 1419110893)
  h = int(h + ((h << 19) | (h >>> 13)))
  h = int(h * 918269209)
  h = int(h ^ (h >>> 14))
  return unsigned(h) / 4294967296
}

// Where the fixed things stand, in cells. G is the grid's size.
// Each side margin holds a broken pillar and a stair of stone shelves. Shelves hang by turns from the window's edge
// and from the pillar, so a heap on one can only spill from its free end, onto the free end of the shelf below.
// A nozzle on each pillar's inner side feeds a wooden chute that ends over the message box, a few cells in from its
// end. On the right the nozzle sits high: a short chute tips its trickle into a field of pegs above the long one.
const world = (G: vec2) => {
  const known = composer.z - composer.x > 0.02
  const half = min(61, G.x * 0.4)
  const cl = known ? floor(composer.x * G.x + 0.5) : floor(G.x * 0.5 - half)
  const cr = known ? floor(composer.z * G.x + 0.5) : floor(G.x * 0.5 + half)
  const ct = known ? floor(composer.w * G.y + 0.5) : 0
  const lt = known ? ct : floor(G.y * 0.13)
  const mL = max(cl, 0)
  const mR = max(G.x - cr, 0)
  const pL = floor(mL * 0.55)
  const eL = floor(mL * 0.31)
  const fL = eL - 3
  const a1 = floor(G.y * 0.75)
  const a2 = floor(G.y * 0.58)
  const a3 = floor(G.y * 0.41)
  const a4 = floor(G.y * 0.25)
  const topL = floor(G.y * 0.9)
  const spL = lt + 12 + max(cl + 7 - (pL + 5), 0)
  const sL = floor(mL * 0.14)
  const pR = G.x - floor(mR * 0.5) - 5
  const eR = G.x - floor(mR * 0.3)
  const fR = eR + 3
  const b1 = floor(G.y * 0.71)
  const b2 = floor(G.y * 0.5)
  const b3 = floor(G.y * 0.29)
  const topR = floor(G.y * 0.79)
  const spR = lt + 16 + max(pR - (cr - 8), 0)
  const upR = min(spR + 46, topR - 4)
  const pegRows = min(26, upR - spR - 20)
  const sR = G.x - 1 - floor(mR * 0.14)
  const dune = (x: number): number => floor(5 + 3.2 * sin(x * 0.07 + 0.6) + 1.3 * sin(x * 0.19 + 2.1))
  const slab = (y: number, top: number): boolean => y < top && y >= top - 3
  // 0 nothing, 1 outside, 2 dune, 3 message box, 4 shelf, 5 chute, 6 pillar
  const what = (x: number, y: number): number => {
    let w = 0
    if (x < 0 || x >= G.x || y < 0 || y >= G.y || (x < 0.5 && y > G.y - 1.5)) w = 1
    else if (y < dune(x)) w = 2
    else if (known && x >= cl && x < cr && y < ct) w = 3
    else if (x < pL) {
      if (x < eL && (slab(y, a1) || slab(y, a3))) w = 4
      else if (x >= fL && (slab(y, a2) || slab(y, a4))) w = 4
    } else if (x < pL + 5) {
      const d = x - pL
      if (y < topL - (d < 0.5 ? 0 : d < 1.5 ? 2 : d < 2.5 ? 1 : d < 3.5 ? 4 : 3)) w = 6
    } else if (x <= cl + 7) {
      const line = spL - 4 - (x - (pL + 5))
      if (y <= line && y > line - 2 && line > lt + 5) w = 5
    } else if (x >= pR + 5) {
      if (x >= eR && (slab(y, b1) || slab(y, b3))) w = 4
      else if (x < fR && slab(y, b2)) w = 4
    } else if (x >= pR) {
      const d = x - pR
      if (y < topR - (d < 0.5 ? 3 : d < 1.5 ? 0 : d < 2.5 ? 1 : d < 3.5 ? 2 : 5)) w = 6
    } else if (x >= cr - 8) {
      const line = spR - 4 - (pR - 1 - x)
      const high = upR - 4 - (pR - 1 - x)
      const gx = x - (cr + 3)
      const gy = y - (spR + 6)
      if (y <= line && y > line - 2 && line > lt + 5) w = 5
      else if (x >= pR - 9 && y <= high && y > high - 2) w = 5
      // a field of pegs between the two chutes: two cells of peg, two of gap, each row set off by two, so nothing
      // falls straight through
      else if (gx >= 0 && x <= pR - 3 && gy >= 0 && gy < pegRows && mod(gy, 5) < 0.5 && mod(gx + 2 * mod(floor(gy / 5), 2), 4) < 1.5) w = 4
    }
    return w
  }
  return { known, cl, cr, ct, lt, mL, mR, pL, eL, fL, a1, a2, a3, a4, topL, spL, sL, pR, eR, fR, b1, b2, b3, topR, spR, upR, sR, what, dune }
}

// What stands in each cell, worked out once a frame and read from here by the sand and the art (each of which asks
// about a dozen neighbours of every cell).
const fixed = buffer({ scale: 1 / CELL, filter: 'nearest' }, p => vec4(world(res).what(p.cell.x, p.cell.y) / 8, 0, 0, 1))
const standsAt = (G: vec2, x: number, y: number): number => (x < 0 || x >= G.x || y < 0 || y >= G.y ? 1 : floor(fixed.at(vec2(x, y)).r * 8 + 0.5))

// kinds: 0 air, 1 grain, 2 crab walking right, 3 crab walking left, 4 a mote of dust (which counts as air), 9 fixed
const air = (k: number): boolean => k < 0.5 || (k > 3.5 && k < 4.5)
const mote = (k: number): boolean => k > 3.5 && k < 4.5
const grain = (k: number): boolean => k > 0.5 && k < 1.5
const crabR = (k: number): boolean => k > 1.5 && k < 2.5
const crabL = (k: number): boolean => k > 2.5 && k < 3.5
const heavy = (k: number): boolean => k > 0.5 && k < 3.5

// Sixty steps a second, so speeds do not depend on the frame rate: one step a frame at 60 frames a second, two at
// 30, three at 20. The buffer runs three times a frame, and a run with no step due hands every cell back as it was.
// A cell holds: r the kind, g a grain's colour (or a crab's own number), b how lately it moved, a a life or a mark.
const sand: Buffer = buffer({ scale: 1 / CELL, filter: 'nearest', repeat: 3 }, (p): vec4 => {
  const G = res
  const W = world(G)
  const cx = p.cell.x
  const cy = p.cell.y
  // The top left texel is the clock. It counts the steps itself (lane a is the step in four, lane g the fours), so
  // the automaton never depends on how large the frame number has grown. Lane b carries the part of a step left
  // over from the last frame, in sixteenths, so the steps keep to sixty a second at any frame rate, and one bit for
  // the crab arrival it last saw, so none is missed on a frame that takes no step.
  const clock = sand.at(vec2(0, G.y - 1))
  const beat = floor(clock.a * 4 + 0.5)
  const tick = floor(clock.g * 255 + 0.5) * 4 + beat
  const stamp = tick * 8 + 8192 * mod(floor(time / 34), 512)
  const banked = floor(clock.b * 32 + 0.5)
  const carry = mod(banked, 16)
  const seenSlot = floor(banked / 16)
  const owed = carry + floor(dt * 960 + 0.5)
  const due = min(floor(owed / 16), 3)
  const isClock = cx < 0.5 && cy > G.y - 1.5
  if (turn > due - 0.5 && !(first || fresh)) {
    // no step is due on this run: every cell stays as it is, and on the frame's last run the clock banks the remainder
    const kept = sand.at(vec2(cx, cy))
    return isClock && turn > 1.5 ? vec4(kept.r, kept.g, (min(owed - due * 16, 15) + 16 * seenSlot) / 32, kept.a) : kept
  }
  // four block offsets in turn, so that every pair of neighbours shares a block at some step
  const oy = mod(beat, 2)
  const ox = floor(beat / 2)
  const bx = floor((cx + ox) / 2) * 2 - ox
  const by = floor((cy + oy) / 2) * 2 - oy
  const qx = cx - bx
  const qy = cy - by
  const kindOf = (x: number, y: number, v: vec4): number => (standsAt(G, x, y) > 0.5 ? 9 : floor(v.r * 5 + 0.5))
  const vBL = sand.at(vec2(bx, by))
  const vBR = sand.at(vec2(bx + 1, by))
  const vTL = sand.at(vec2(bx, by + 1))
  const vTR = sand.at(vec2(bx + 1, by + 1))
  const kBL = kindOf(bx, by, vBL)
  const kBR = kindOf(bx + 1, by, vBR)
  const kTL = kindOf(bx, by + 1, vTL)
  const kTR = kindOf(bx + 1, by + 1, vTR)
  // cells beside and below the block: read to decide, never written from here
  const beyond = (ix: number, iy: number): number => kindOf(bx + ix, by + iy, sand.at(vec2(bx + ix, by + iy)))
  const eW0 = beyond(-1, 0)
  const eE0 = beyond(2, 0)
  const eW1 = beyond(-1, 1)
  const eE1 = beyond(2, 1)
  const eWd = beyond(-1, -1)
  const eD0 = beyond(0, -1)
  const eD1 = beyond(1, -1)
  const eEd = beyond(2, -1)
  const r1 = rnd(bx, by, stamp + 1)
  const r2 = rnd(bx, by, stamp + 2)
  const cellPts = size.x / G.x

  // A hovering pointer parts falling sand: near it a lone grain steps aside, away from the pointer.
  // A pressed pointer on bare backdrop scares the crabs under and beside it: they turn away and run (scare is -1 for
  // run left, 1 for run right).
  let jitL = 0.04
  let jitR = 0.04
  let scare = 0
  for (const f of pointers) {
    const hx = f.at.x / cellPts - (bx + 1)
    const hy = f.at.y / cellPts - (by + 1)
    if (f.down < 0.5 && f.gone < 0.001 && hx * hx + hy * hy < 60) {
      jitL = hx < 0 ? 0.8 : 0
      jitR = hx < 0 ? 0 : 0.8
    }
    if (f.down > 0.5 && f.over < 0.5 && f.gone < 0.001 && abs(hx) < 16 && hy > -3) scare = hx < 0 ? 1 : -1
  }

  const fallL0 = heavy(kTL) && air(kBL)
  const fallR0 = heavy(kTR) && air(kBR)
  const jL = fallL0 && grain(kTL) && air(kTR) && air(kBR) && r1 < jitL
  const jR = fallR0 && grain(kTR) && air(kTL) && air(kBL) && r1 < jitR
  const dLR0 = jL || (grain(kTL) && !air(kBL) && air(kTR) && air(kBR))
  const dRL0 = jR || (grain(kTR) && !air(kBR) && air(kTL) && air(kBL))
  const flat = !air(kBL) && !air(kBR)
  const under = !air(eD0) && !air(eD1)
  const open = air(kTL) && air(kTR)
  const creep = 0.65
  const cTop0 = (grain(kTL) && air(kTR) && flat && air(eE0) && r2 < creep) || (grain(kTR) && air(kTL) && flat && air(eW0) && r2 < creep)
  const cBot0 = (grain(kBL) && air(kBR) && open && under && air(eEd) && r2 < creep) || (grain(kBR) && air(kBL) && open && under && air(eWd) && r2 < creep)

  // Crabs walk in short bursts, and only in a block where no grain moves this step. Each crab rests now and then
  // for a couple of seconds, by its own number.
  const quiet = !(fallL0 || fallR0 || dLR0 || dRL0 || cTop0 || cBot0)
  const walking = mod(tick, 24) < (abs(scare) > 0.5 ? 16 : 4) && quiet
  const isCrab = (k: number): boolean => k > 1.5 && k < 3.5
  const ownNumber = isCrab(kBL) ? vBL.g : isCrab(kBR) ? vBR.g : isCrab(kTL) ? vTL.g : vTR.g
  const awake = walking && (abs(scare) > 0.5 || rnd(ownNumber * 255, floor(time / 2.5), 31) < 0.72)
  // a right walker, by where it stands in the block
  const rBL = crabR(kBL) && awake
  const rTL = crabR(kTL) && awake
  const rBR = crabR(kBR) && awake
  const rWalkBot = rBL && air(kBR)
  const rClimb = rBL && !air(kBR) && open
  const rDigL = rBL && !air(kBR) && grain(kTL)
  const rDown = rTL && !air(kBL) && air(kTR) && air(kBR)
  const rWalkTop = rTL && air(kTR) && !air(kBR)
  const rHop = rBR && !air(eE0) && air(eE1) && air(kTR)
  const rTurn = (rBR && !air(eE0) && !air(eE1)) || (rBL && !air(kBR) && !air(kTR) && !grain(kTL))
  const rActs = rWalkBot || rClimb || rDigL || rDown || rWalkTop || rHop
  // a left walker, mirrored
  const lBR = crabL(kBR) && awake && !rActs
  const lTR = crabL(kTR) && awake && !rActs
  const lBL = crabL(kBL) && awake && !rActs
  const lWalkBot = lBR && air(kBL)
  const lClimb = lBR && !air(kBL) && open
  const lDigR = lBR && !air(kBL) && grain(kTR)
  const lDown = lTR && !air(kBR) && air(kTL) && air(kBL)
  const lWalkTop = lTR && air(kTL) && !air(kBL)
  const lHop = lBL && !air(eW0) && air(eW1) && air(kTL)
  const lTurn = (lBL && !air(eW0) && !air(eW1)) || (lBR && !air(kBL) && !air(kTL) && !grain(kTR))

  // dust drifts on the wind where nothing else moves: mostly sideways, sometimes up
  const calm = quiet && !(rActs || lWalkBot || lClimb || lDigR || lDown || lWalkTop || lHop)
  const gust = 0.18 + 0.15 * sin(time * 0.13)
  const dTop = calm && r1 < gust && mote(kTL) && kTR < 0.5
  const dBot = calm && r1 < gust && mote(kBL) && kBR < 0.5 && !dTop
  const dUpL = calm && r1 > 0.9 && mote(kBL) && kTL < 0.5
  const dUpR = calm && r1 > 0.9 && mote(kBR) && kTR < 0.5

  // a crab in mid air steps onto the ledge beside it instead of falling back
  const fallL = fallL0 && !jL && !(rWalkTop && crabR(kTL))
  const fallR = fallR0 && !jR && !(lWalkTop && crabL(kTR))
  const upL = rDigL || lHop || dUpL
  const upR = lDigR || rHop || dUpR
  const dLR = dLR0 || rDown || lClimb
  const dRL = dRL0 || lDown || rClimb
  const cTop = cTop0 || rWalkTop || lWalkTop || dTop
  const cBot = cBot0 || rWalkBot || lWalkBot || dBot

  const vert = (qx < 0.5 && (fallL || upL)) || (qx > 0.5 && (fallR || upR))
  const diag = (dLR && abs(qx - qy) > 0.5) || (dRL && abs(qx - qy) < 0.5)
  const hori = (cTop && qy > 0.5) || (cBot && qy < 0.5)
  let sx = qx
  let sy = qy
  if (vert) sy = 1 - sy
  else if (diag) {
    sx = 1 - sx
    sy = 1 - sy
  } else if (hori) sx = 1 - sx
  const moved = vert || diag || hori
  const lo = sx < 0.5 ? vBL : vBR
  const hi = sx < 0.5 ? vTL : vTR
  const src = sy < 0.5 ? lo : hi
  const kLo = sx < 0.5 ? kBL : kBR
  const kHi = sx < 0.5 ? kTL : kTR
  let k = sy < 0.5 ? kLo : kHi
  // Lane b remembers motion: 1 for a fall, a little less for a slide, fading over about a tenth of a second. The art
  // draws a grain in motion in a quiet tone, so sand on the move never makes a cell blink.
  const stir = moved && grain(k) ? (vert || jL || jR ? 1 : 0.85) : max(src.b - 0.12, 0)
  let oR = src.r
  let oG = src.g
  let oB = stir
  let oA = src.a

  // a crab turns round where it stands
  const turnHere = (rTurn && ((qx > 0.5 && qy < 0.5 && crabR(kBR)) || (qx < 0.5 && qy < 0.5 && crabR(kBL)))) || (lTurn && ((qx < 0.5 && qy < 0.5 && crabL(kBL)) || (qx > 0.5 && qy < 0.5 && crabL(kBR))))
  const kHere = qy < 0.5 ? (qx < 0.5 ? kBL : kBR) : qx < 0.5 ? kTL : kTR
  const flee = (crabR(kHere) && scare < -0.5) || (crabL(kHere) && scare > 0.5)
  if ((turnHere || flee) && !moved) {
    k = 5 - k
    oR = k * 0.2
  }
  // crabs leave at the window's sides and tire after a few minutes
  if (k > 1.5 && k < 3.5) {
    if (mod(tick, 64) < 0.5) oA = oA - 0.004
    if (cx < 0.5 || cx > G.x - 1.5 || oA < 0.01) k = 0
  }

  const me = standsAt(G, cx, cy)
  if (me > 0) k = 9

  // Wind takes resting grains from the top of a heap, so the page returns to calm: hardly at all up among the
  // shelves, slowly on the message box, faster over the dunes the higher a mound stands, and much more slowly for
  // sand a person poured (lane a is 0.5 for it).
  const kUp = qx < 0.5 ? kTL : kTR
  if (qy < 0.5 && !moved && grain(k) && air(kUp) && rnd(cx, cy, stamp + 5) < (cy >= (cx < G.x * 0.5 ? W.a4 : W.b3) - 4 ? 0.0004 : oA < 0.75 ? 0.001 : W.known && cx >= W.cl && cx < W.cr ? 0.003 : 0.006 * (1 + (cy - W.dune(cx)) / 5))) {
    k = 4
    oR = 0.8
    oB = 0
    oA = 1
  }
  // a mote thins out and is gone in a few seconds
  if (mote(k)) {
    oA = oA - 0.006
    if (oA < 0.02) k = 0
  }

  if (k < 0.5 || k > 8) {
    oR = 0
    oG = 0
    oB = 0
    oA = 0
  }

  // New things. Grains and dust are born on every second step (the two falls of sand on every fourth): from the falls,
  // the nozzles and pressed pointers, and as puffs. A crab comes in at a side every seven seconds.
  if (k < 0.5) {
    const even = mod(beat, 2) < 0.5
    const r3 = rnd(cx, cy, stamp + 3)
    const r4 = rnd(cx, cy, stamp + 4)
    const flowL = clamp(0.6 + 0.55 * sin(time * 0.21) + 0.25 * sin(time * 0.53 + 1), 0, 1)
    const flowR = clamp(0.6 + 0.55 * sin(time * 0.17 + 2) + 0.25 * sin(time * 0.47 + 4), 0, 1)
    let born = 0
    let poured = 0
    let hue = time * 0.09
    if (abs(cy - (G.y - 2)) < 0.5 && beat < 0.5) {
      if (abs(cx - W.sL) < 0.5 && r3 < flowL) born = 1
      if (abs(cx - W.sR) < 0.5 && r3 < flowR) born = 1
    }
    // the nozzles trickle
    if (even && abs(cx - (W.pL + 5)) < 0.5 && abs(cy - W.spL) < 0.5 && r3 < 0.06 + 0.2 * flowR) born = 1
    if (even && abs(cx - (W.pR - 1)) < 0.5 && abs(cy - W.upR) < 0.5 && r3 < 0.06 + 0.2 * flowL) born = 1
    for (const f of pointers) {
      const w = even ? f.down * (1 - f.over) * (f.gone > 0 ? 0 : 1) : 0
      // The stroke the pointer drew since the last frame, in cells: where it began, how long it is, which way it heads.
      // This cell is then some way along the stroke and some way off to its side.
      const fromX = f.was.x / cellPts
      const fromY = f.was.y / cellPts
      const runX = f.at.x / cellPts - fromX
      const runY = f.at.y / cellPts - fromY
      const reach = sqrt(runX * runX + runY * runY)
      const perCell = 1 / max(reach, 0.01)
      const offX = cx + 0.5 - fromX
      const offY = cy + 0.5 - fromY
      const along = (offX * runX + offY * runY) * perCell
      const aside = abs(offX * runY - offY * runX) * perCell
      const past = max(max(-along, along - reach), 0)
      // a pointer that has not moved is a dot, not a stroke
      const away = reach < 0.01 ? sqrt(offX * offX + offY * offY) : sqrt(aside * aside + past * past)
      // the faster the stroke, the less it pours: a hard scrub only scatters a few grains
      const chance = (w * (away < 0.8 ? 0.6 : 0.2)) / (1 + 0.35 * reach * reach)
      if (away < 1.6 && r3 < chance) {
        born = 1
        poured = 1
        hue = time * 0.3 + (time - f.age) * 0.77
      }
    }
    // a crab comes in from a side now and then
    const slot = floor((time + 3) / 7)
    const pick = rnd(slot, 5, 41)
    if (abs(mod(slot, 2) - seenSlot) > 0.5) {
      if (pick < 0.5 && abs(cx - 1) < 0.5 && abs(cy - W.dune(1) - 1) < 0.5) born = 2
      if (pick > 0.5 && abs(cx - (G.x - 2)) < 0.5 && abs(cy - W.dune(G.x - 2) - 1) < 0.5) born = 3
    }
    // a puff of dust beside a grain that has just come to rest
    const nL = sand.at(vec2(cx - 1, cy))
    const nR = sand.at(vec2(cx + 1, cy))
    const landedL = nL.r > 0.1 && nL.r < 0.3 && nL.b > 0.93 && !air(kindOf(cx - 1, cy - 1, sand.at(vec2(cx - 1, cy - 1))))
    const landedR = nR.r > 0.1 && nR.r < 0.3 && nR.b > 0.93 && !air(kindOf(cx + 1, cy - 1, sand.at(vec2(cx + 1, cy - 1))))
    if (even && born < 0.5 && (landedL || landedR) && r4 > 0.9) {
      born = 4
      hue = landedL ? nL.g : nR.g
    }
    if (born > 0.5) {
      oR = born * 0.2
      oG = born < 1.5 ? (floor(mod(hue, 4)) + r4) / 4 : born > 3.5 ? hue : r4
      oB = born < 1.5 ? 1 : 0
      oA = born > 3.5 ? 0.6 : born < 1.5 && poured > 0.5 ? 0.5 : 1
    }
  }

  if (first || fresh) {
    oR = 0
    oG = 0
    oB = 0
    oA = 0
    const r5 = rnd(cx, cy, 77)
    const strata = (floor(mod(cy * 0.5 + cx * 0.13 + r5 * 0.8, 4)) + r5) / 4
    const on = (top: number, h: number): boolean => cy >= top && cy < top + h
    let heap = false
    if (cx < W.pL) {
      const hE = min(10, floor((W.eL - 1 - cx) / 2))
      const hP = floor((cx - W.fL) / 2)
      heap = (cx < W.eL && (on(W.a1, hE) || on(W.a3, hE))) || (cx >= W.fL && (on(W.a2, hP) || on(W.a4, hP)))
    } else if (cx >= W.pR + 5) {
      const hE = min(10, floor((cx - W.eR) / 2))
      const hP = floor((W.fR - 1 - cx) / 2)
      heap = (cx >= W.eR && (on(W.b1, hE) || on(W.b3, hE))) || (cx < W.fR && on(W.b2, hP))
    }
    if (me < 1 && heap) {
      oR = 0.2
      oG = strata
      oA = 1
    }
    // two crabs on each side to begin with, one grown and one young, all walking inward
    const crabAt = (at: number, kind: number, size: number) => {
      if (abs(cx - at) < 0.5 && abs(cy - W.dune(at)) < 0.5) {
        oR = kind * 0.2
        oG = size
        oA = 1
      }
    }
    crabAt(floor(W.mL * 0.22), 2, 0.8)
    crabAt(floor(W.mL * 0.07) + 1, 2, 0.2)
    crabAt(G.x - floor(W.mR * 0.24), 3, 0.7)
    crabAt(G.x - floor(W.mR * 0.06) - 2, 3, 0.3)
  }
  if (isClock) {
    const fresh0 = first || fresh
    oR = 0
    const nowSlot = mod(floor((time + 3) / 7), 2)
    oB = fresh0 ? 0 : ((turn > 1.5 ? owed - 48 : carry) + 16 * nowSlot) / 32
    oA = fresh0 ? 0 : mod(beat + 1, 4) / 4
    oG = fresh0 ? 0 : mod(floor(clock.g * 255 + 0.5) + (beat > 2.5 ? 1 : 0), 256) / 255
  }
  return vec4(oR, oG, oB, oA)
})

// A hand-made 4 by 4 threshold order that fills along diagonals, so shading comes out as a slanted hatch.
const hatch = (x: number, y: number): number => {
  const u = mod(x - y, 4)
  const a = u < 0.5 ? 0 : u < 1.5 ? 8 : u < 2.5 ? 12 : 4
  return (a + mod(y, 4) + 0.5) / 16
}

// The crab, 9 by 6, two bits a cell: 1 shell, 2 dark, 3 light. Rows from the feet up, two poses.
const crabRow = (j: number, pose: number): number => {
  const a = j < 0.5 ? 139298 : j < 1.5 ? 38232 : j < 2.5 ? 21844 : j < 3.5 ? 87381 : j < 4.5 ? 73761 : 12336
  const b = j < 0.5 ? 34952 : j < 1.5 ? 38232 : j < 2.5 ? 87381 : j < 3.5 ? 87381 : j < 4.5 ? 8224 : 12336
  return pose < 0.5 ? a : b
}
// A young crab, 5 by 3 inside the same 9 columns.
const smallRow = (j: number, pose: number): number => {
  const a = j < 0.5 ? 2176 : j < 1.5 ? 5456 : j < 2.5 ? 3264 : 0
  const b = j < 0.5 ? 8736 : j < 1.5 ? 5456 : j < 2.5 ? 3264 : 0
  return pose < 0.5 ? a : b
}

// The gecko on the right pillar, 5 by 9, tail first, two poses.
const geckoRow = (j: number, pose: number): number => {
  const a = j < 0.5 ? 64 : j < 1.5 ? 16 : j < 2.5 ? 530 : j < 3.5 ? 152 : j < 4.5 ? 84 : j < 5.5 ? 152 : j < 6.5 ? 530 : j < 7.5 ? 220 : 84
  const b = j < 0.5 ? 4 : j < 1.5 ? 16 : j < 2.5 ? 152 : j < 3.5 ? 530 : j < 4.5 ? 84 : j < 5.5 ? 530 : j < 6.5 ? 152 : j < 7.5 ? 220 : 84
  return pose < 0.5 ? a : b
}

const art = buffer({ scale: 1 / CELL, filter: 'linear' }, p => {
  const G = res
  const W = world(G)
  const x = p.cell.x
  const y = p.cell.y
  // light or dark: the Svg's middle is bare sky in the shown mode
  const m = step(0.45, dot(scene.sample(vec2(0.5, 0.5)).rgb, vec3(0.3, 0.6, 0.1)))
  const ink = (d: number, l: number): number => mix(d, l, m)
  const v = sand.at(vec2(x, y))
  const k = floor(v.r * 5 + 0.5)
  const w = standsAt(G, x, y)
  const th = hatch(x, y)

  // sky: two flat tones meeting in a hatched seam, a far line of dunes, a few specks
  const seam = G.y * 0.34
  let col = ink(vec3(0.11, 0.08, 0.14), vec3(0.96, 0.92, 0.84))
  if (th < clamp((seam - y) / 16, 0, 1)) col = ink(vec3(0.15, 0.1, 0.17), vec3(0.94, 0.88, 0.78))
  const far = 13 + 5 * sin(x * 0.045 + 2) + 2 * sin(x * 0.11)
  if (y < far - 1 || (y < far && th < 0.5)) col = ink(vec3(0.19, 0.12, 0.18), vec3(0.92, 0.85, 0.74))
  if (y > seam && rnd(x, y, 9) < 0.004) col = ink(vec3(0.33, 0.27, 0.36), vec3(0.9, 0.83, 0.71))

  // a big quiet disc between the left pillar and the text, three quarters of the way up: the moon by night, the sun by day
  const discR = min(12, (W.cl - W.pL - 5) * 0.42)
  const dxs = x + 0.5 - (W.pL + 5 + (W.cl - W.pL - 5) * 0.5)
  const dys = y + 0.5 - G.y * 0.72
  const dd = dxs * dxs + dys * dys
  if (dd < discR * discR && (dd < (discR - 1.5) * (discR - 1.5) || th < 0.5) && (dxs - dys < discR * 0.35 || th < 0.6)) col = ink(vec3(0.2, 0.15, 0.23), vec3(0.99, 0.96, 0.9))

  // stone: the pillars and the shelves, a quiet tone near the sky's, lit from the upper left
  const stone = ink(vec3(0.23, 0.17, 0.24), vec3(0.84, 0.76, 0.66))
  const stoneLit = ink(vec3(0.31, 0.24, 0.31), vec3(0.9, 0.83, 0.74))
  const stoneDim = ink(vec3(0.16, 0.11, 0.17), vec3(0.75, 0.66, 0.56))
  if (w > 5.5) {
    const d = x < G.x * 0.5 ? x - W.pL : x - W.pR
    col = d < 0.5 ? stoneLit : d > 3.5 ? stoneDim : stone
    // drum joints, a chipped top, a few pits, and a sign carved into most drums (3 by 5 shapes of its own)
    const drum = floor(y / 11)
    const inDrum = y - drum * 11
    if (inDrum < 0.5 || standsAt(G, x, y + 1) < 5.5) col = d > 3.5 ? stone : stoneDim
    if (rnd(x, y, 13) < 0.03 && d > 0.5) col = stoneDim
    const sign = floor(rnd(drum, 1, x < G.x * 0.5 ? 51 : 52) * 9)
    const carved = sign < 0.5 ? 25814 : sign < 1.5 ? 13715 : sign < 2.5 ? 17492 : sign < 3.5 ? 5393 : sign < 4.5 ? 18569 : sign < 5.5 ? 3640 : sign < 6.5 ? 1041 : 0
    if (d > 0.5 && d < 3.5 && inDrum > 2.5 && inDrum < 7.5 && unsigned(int((int(carved) >>> int((inDrum - 3) * 3 + d - 1)) & 1)) > 0.5) col = stoneDim
  }
  if (w > 3.5 && w < 4.5) {
    col = stone
    const roof = standsAt(G, x, y + 1) < 3.5 || standsAt(G, x, y + 1) > 4.5
    const foot = standsAt(G, x, y - 1) < 3.5 || standsAt(G, x, y - 1) > 4.5
    if (roof && foot) col = ink(vec3(0.5, 0.36, 0.24), vec3(0.72, 0.56, 0.4))
    else if (roof) col = stoneLit
    else if (standsAt(G, x, y - 1) < 3.5 || standsAt(G, x, y - 1) > 4.5 || mod(x * 3 + y * 5, 11) < 0.5) col = stoneDim
  }
  // stone brackets under the shelves (drawn only)
  if (w < 0.5) {
    const under = (top: number): number => (y < top - 3 && y >= top - 6 ? top - 3 - y : 9)
    const eL = min(under(W.a1), under(W.a3))
    const iL = min(under(W.a2), under(W.a4))
    const eR = min(under(W.b1), under(W.b3))
    const iR = under(W.b2)
    if ((x < 4 - eL && x < W.eL) || (x >= W.pL - 4 + iL && x < W.pL && x >= W.fL) || (x >= G.x - 4 + eR && x >= W.eR) || (x < W.pR + 9 - iR && x >= W.pR + 5 && x < W.fR)) col = stoneDim
  }
  // wooden chutes, and the nozzles that feed them
  if (w > 4.5 && w < 5.5) {
    col = ink(vec3(0.36, 0.24, 0.2), vec3(0.66, 0.5, 0.37))
    if (standsAt(G, x, y + 1) > 4.5 || mod(x, 6) < 0.5) col = ink(vec3(0.24, 0.16, 0.16), vec3(0.52, 0.38, 0.29))
  }
  const nozzleL = abs(x - (W.pL + 5)) < 0.5 && abs(y - W.spL - 1) < 1
  const nozzleR = abs(x - (W.pR - 1)) < 0.5 && abs(y - W.upR - 1) < 1
  if ((nozzleL || nozzleR) && w < 0.5) col = y > (nozzleL ? W.spL : W.upR) + 0.5 ? stoneLit : stoneDim

  // the dunes along the bottom: old sand, hatched darker with depth, a lit crest
  if (w > 1.5 && w < 2.5) {
    const depth = W.dune(x) - 1 - y
    col = ink(vec3(0.45, 0.29, 0.19), vec3(0.86, 0.72, 0.52))
    if (depth < 0.5) col = ink(vec3(0.62, 0.42, 0.22), vec3(0.92, 0.8, 0.61))
    else if (th < clamp((depth - 1) / 7, 0, 0.85)) col = ink(vec3(0.34, 0.21, 0.16), vec3(0.78, 0.62, 0.42))
  }

  // things that grow, drawn only on bare sky: vines hang under the shelves and sway a cell, a cactus stands on each side
  if (w < 0.5) {
    const green = ink(vec3(0.22, 0.3, 0.24), vec3(0.55, 0.6, 0.42))
    // how far this cell hangs under a shelf, and which shelf (its top row tells the vines of one shelf from another's)
    let hang = 99
    let shelf = 0
    const under = (top: number, spans: boolean) => {
      if (spans && y < top - 3 && y >= top - 13) {
        hang = top - 3 - y
        shelf = top
      }
    }
    under(W.a1, x < W.eL)
    under(W.a3, x < W.eL)
    under(W.a2, x >= W.fL && x < W.pL)
    under(W.a4, x >= W.fL && x < W.pL)
    under(W.b1, x >= W.eR)
    under(W.b3, x >= W.eR)
    under(W.b2, x >= W.pR + 5 && x < W.fR)
    if (hang < 50) {
      for (const s of [-1, 0, 1]) {
        const root = x - s
        const len = 2 + floor(9 * rnd(root, shelf, 23))
        const lean = floor(0.5 + 0.9 * sin(time * 0.7 + root * 1.7) * (hang / 9))
        if (rnd(root, shelf, 29) < 0.16 && hang <= len && abs(lean - s) < 0.5) col = mod(hang + root, 3) < 0.5 ? ink(vec3(0.3, 0.4, 0.3), vec3(0.44, 0.52, 0.36)) : green
      }
    }
    const cxl = floor(W.pL * 0.78)
    const cxr = G.x - 5
    const plantAt = x < G.x * 0.5 ? cxl : cxr
    const px = x - plantAt + 2
    const py = y - W.dune(plantAt)
    const prow = py < 0.5 ? 16 : py < 1.5 ? 16 : py < 2.5 ? 21 : py < 3.5 ? 337 : py < 4.5 ? 273 : py < 5.5 ? 272 : 16
    if (px > -0.5 && px < 4.5 && py > -0.5 && py < 6.5 && unsigned(int((int(prow) >>> int(px * 2)) & 3)) > 0.5) col = px > 2.5 ? ink(vec3(0.17, 0.24, 0.2), vec3(0.45, 0.5, 0.35)) : green
  }

  // dry tufts on the dune crests (drawn only, sand buries them)
  const crest = W.dune(x)
  if (w < 0.5 && rnd(x, 2, 17) < 0.07 && y >= crest && y < crest + 1 + floor(2 * rnd(x, 4, 17))) col = ink(vec3(0.3, 0.24, 0.16), vec3(0.66, 0.56, 0.38))

  // a gecko goes up and down the right pillar, a cell at a time, and rests at each end
  const lap = fract(time / 64)
  const climb = clamp(abs(lap * 2 - 1) * 1.5 - 0.25, 0, 1)
  const gLow = W.spR + 6
  const gAt = floor(gLow + (W.topR - 16 - gLow) * climb)
  const gx = x - W.pR
  const gy0 = y - gAt
  const gy = lap < 0.5 ? 8 - gy0 : gy0
  let gecko = 0
  if (gx > -0.5 && gx < 4.5 && gy0 > -0.5 && gy0 < 8.5) gecko = unsigned(int((int(geckoRow(gy, mod(gAt + floor(time * 0.4), 2))) >>> int(gx * 2)) & 3))

  // grains
  const kAt = (ix: number, iy: number): number => {
    const n = sand.at(vec2(x + ix, y + iy))
    return standsAt(G, x + ix, y + iy) > 0 ? 9 : floor(n.r * 5 + 0.5)
  }
  const tone = (g: number): number => {
    const ci = floor(g * 4)
    const d = ci < 0.5 ? vec3(0.89, 0.65, 0.29) : ci < 1.5 ? vec3(0.79, 0.52, 0.23) : ci < 2.5 ? vec3(0.65, 0.35, 0.2) : vec3(0.95, 0.86, 0.68)
    const l = ci < 0.5 ? vec3(0.77, 0.44, 0.24) : ci < 1.5 ? vec3(0.83, 0.6, 0.25) : ci < 2.5 ? vec3(0.56, 0.35, 0.24) : vec3(0.86, 0.66, 0.51)
    return ink(d, l)
  }
  // A grain in motion wears a quiet tone of its colour: close to the sky in brightness (about 0.15 of linear
  // luminance away, whatever the colour), and told from it by hue. It takes its full colour once it has lain still
  // for a moment. That keeps every fall, pour and slide from making the cells it crosses blink.
  const quiet = (g: number): number => {
    const ci = floor(g * 4)
    const d = ci < 0.5 ? vec3(0.62, 0.38, 0.1) : ci < 1.5 ? vec3(0.58, 0.4, 0.14) : ci < 2.5 ? vec3(0.58, 0.32, 0.18) : vec3(0.5, 0.43, 0.28)
    const l = ci < 0.5 ? vec3(1, 0.81, 0.64) : ci < 1.5 ? vec3(0.98, 0.84, 0.5) : ci < 2.5 ? vec3(0.94, 0.82, 0.76) : vec3(1, 0.8, 0.74)
    return ink(d, l)
  }
  const ground = col
  const below = sand.at(vec2(x, y - 1))
  if (w < 0.5 && grain(k)) {
    const base = tone(v.g)
    const up = kAt(0, 1)
    const lf = kAt(-1, 0)
    const rt = kAt(1, 0)
    const up2 = kAt(0, 2)
    const glint = ink(vec3(1, 0.93, 0.76), vec3(1, 0.95, 0.85))
    const murk = ink(vec3(0.2, 0.1, 0.12), vec3(0.42, 0.24, 0.18))
    col = mix(murk, base, 0.95)
    if (v.b > 0.3) col = quiet(v.g)
    else if (air(up)) col = ink(mix(base, glint, 0.38), mix(murk, base, 0.86))
    else if (air(lf)) col = ink(mix(base, glint, 0.2), mix(murk, base, 0.8))
    else if (air(rt)) col = mix(murk, base, ink(0.74, 0.62))
    else if (fract(v.g * 4) > 0.97) col = mix(base, glint, ink(0.45, 0.3))
    else if (!air(up2) && th < 0.19) col = mix(murk, base, 0.86)
  } else if (w < 0.5 && mote(k)) {
    col = mix(ground, quiet(v.g), v.a > 0.5 ? 0.8 : 0.45)
  } else if (w < 0.5 && air(k)) {
    // the tail of a falling grain, so a steady pour reads as a ribbon and not as blinking dots
    const low = sand.at(vec2(x, y - 2))
    const lower = sand.at(vec2(x, y - 3))
    if (below.r > 0.1 && below.r < 0.3 && below.b > 0.93) col = mix(ground, quiet(below.g), 0.85)
    else if (low.r > 0.1 && low.r < 0.3 && low.b > 0.93 && below.r < 0.1) col = mix(ground, quiet(low.g), 0.65)
    else if (lower.r > 0.1 && lower.r < 0.3 && lower.b > 0.93 && below.r < 0.1 && low.r < 0.1) col = mix(ground, quiet(lower.g), 0.45)
  }

  if (gecko > 0.5 && !grain(k)) col = gecko < 1.5 ? ink(vec3(0.2, 0.6, 0.55), vec3(0.13, 0.48, 0.45)) : gecko < 2.5 ? ink(vec3(0.09, 0.33, 0.35), vec3(0.08, 0.3, 0.3)) : ink(vec3(0.95, 0.86, 0.68), vec3(1, 0.96, 0.88))

  // crabs, drawn over everything: look for a crab's foot cell under and beside this cell
  // (two crabs may stand close enough for their pictures to overlap, so two are remembered)
  let kindA = 0
  let acrossA = 0
  let rowA = 0
  let ownA = 0
  let kindB = 0
  let acrossB = 0
  let rowB = 0
  let ownB = 0
  for (let j = 0; j < 6; j++) {
    // (a read below the grid gives the bottom row again, so a crab standing on the bottom row would be found once
    // more for every row read below it; rows below the grid are not counted)
    const inGrid = y - j >= 0
    for (let i = 0; i < 9; i++) {
      const n = sand.at(vec2(x + i - 4, y - j))
      const nk = floor(n.r * 5 + 0.5)
      if (inGrid && nk > 1.5 && nk < 3.5) {
        if (kindA < 0.5) {
          kindA = nk
          acrossA = i
          rowA = j
          ownA = n.g
        } else {
          kindB = nk
          acrossB = i
          rowB = j
          ownB = n.g
        }
      }
    }
  }
  // which cell of a crab's picture this is: a right walker's is mirrored, and the legs change with each step
  const crabCell = (kind: number, across: number, row: number, own: number): number => {
    const pose = mod(x + across - 4 + floor(time * 1.5), 2)
    const col9 = kind < 2.5 ? 8 - across : across
    return kind > 0.5 ? unsigned(int((int(own < 0.4 ? smallRow(row, pose) : crabRow(row, pose)) >>> int(col9 * 2)) & 3)) : 0
  }
  const cellA = crabCell(kindA, acrossA, rowA, ownA)
  const cellB = crabCell(kindB, acrossB, rowB, ownB)
  const code = cellB > 0.5 ? cellB : cellA
  const hitRow = cellB > 0.5 ? rowB : rowA
  if (code > 0.5) {
    col = code < 1.5 ? ink(vec3(0.25, 0.72, 0.66), vec3(0.16, 0.57, 0.53)) : code < 2.5 ? ink(vec3(0.07, 0.27, 0.3), vec3(0.07, 0.23, 0.24)) : ink(vec3(0.95, 0.86, 0.68), vec3(1, 0.96, 0.88))
    if (code < 1.5 && hitRow < 1.5) col = ink(vec3(0.16, 0.55, 0.52), vec3(0.11, 0.44, 0.42))
  }
  return vec4(col, 1)
})

const view = picture(p => {
  // Enlarge the art with crisp cell edges. A pixel reads the middle of its cell, which is that cell's pure colour,
  // except within half a picture pixel of the cell's edge, where it slides toward the neighbour so the edge is one
  // picture pixel soft at any sharpness.
  const spot = p.uv * art.size
  const cell = floor(spot)
  const inCell = spot - cell
  const crisp = size.x / (art.size.x * p.px)
  const towardLow = clamp(inCell * crisp - 0.5, -0.5, 0)
  const towardHigh = clamp((inCell - 1) * crisp + 0.5, 0, 0.5)
  return vec4(art.sample((cell + 0.5 + towardLow + towardHigh) / art.size).rgb, 1)
})

export default shader({ fps: 60, passes: [fixed, sand, art, view] })
