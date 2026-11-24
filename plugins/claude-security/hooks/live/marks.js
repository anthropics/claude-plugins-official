import { LENS, SEVERITY, VOTE, mix, rgb } from './palette.js'
import { LENSES } from './scan.js'
import { fit, narrow } from './words.js'
const [PING, DUST, LOCK, ARRIVAL] = [0.9, 2.4, 0.7, 0.22]
const [SLOT_W, SLOT_H, ROWS_FOR_RINGS] = [6, 3, 16]
const LENS_INK = Object.fromEntries(LENSES.map(lens => [lens, rgb(LENS[lens])]))
function circle(radius) {
 const turns = Array.from({ length: 96 }, (_, step) => (step / 96) * 2 * Math.PI)
 const dots = turns.map(t => [Math.round(5.5 + radius * Math.sin(t)), Math.round(5.5 - radius * Math.cos(t))])
 return [...new Map(dots.map(dot => [dot.join(), dot])).values()]
}
const RING = [5.6, 4.7].flatMap((radius, ring) =>
 circle(radius).map(([x, y], n, dots) => ({ x, y, turn: n / dots.length, outer: ring === 0 })),
)
export class Marks {
 #slots = new Map()
 constructor(scan, plan, canvas, inks, motion) {
  this.scan = scan
  this.plan = plan
  this.canvas = canvas
  this.inks = inks
  this.motion = motion
  this.strip = plan.rows < 3
  this.rings = plan.rows >= ROWS_FOR_RINGS
 }
 draw(now) {
  const { scan } = this
  const mapped = (path) => this.plan.atlas.find(path) !== undefined
  const since = (at) => (this.motion && at !== undefined ? now - at : Infinity)
  if (scan.reported) {
   const found = scan.findings.filter(({ file }) => mapped(file))
   return found.flatMap((finding, n) =>
    this.#finding(finding, since(scan.finished) - 0.4 - Math.min(n, 16) * ARRIVAL),
   )
  }
  const candidates = [...scan.candidates.values()].filter(({ path }) => mapped(path))
  const leads = scan.openLeads(mapped).map((lead, n) => this.#lead(lead, since(lead.at), now * 2.4 + n))
  const settledFirst = candidates.sort((a, b) => Number(a.outcome === 'testing') - Number(b.outcome === 'testing'))
  const named = settledFirst.flatMap(candidate => this.#candidate(candidate, since(candidate.settled), now))
  const touches = ([x, y], n) =>
   !this.strip && named.some(([a, b], m) => m > n && b === y && Math.abs(a - x) < 4)
  return [...leads, ...named.filter((label, n) => !touches(label, n))]
 }
 #slot(name, path, line) {
  const { plan } = this
  const [x, y] = plan.cell(path, line)
  const cell = x + ' ' + y
  const kept = this.#slots.get(name)
  if (kept?.cell === cell) return kept.slot
  this.#slots.delete(name)
  const home = plan.homes[plan.atlas.find(path) ?? -1] ?? { x: 0, y: 0, w: plan.cols, h: plan.rows }
  const ring = this.rings ? 1 : 0
  const clamp = (n, low, high) =>
   Math.max(Math.min(n, high), low)
  const near = [0, 1, -1, 2, -2].flatMap(dy =>
   [0, 3, -3, 7, -7].map(dx => [
    Math.min(clamp(x - 3 + dx, home.x + 1, home.x + home.w - 1 - SLOT_W), plan.cols - 1 - SLOT_W),
    Math.min(clamp(y - 1 + dy, home.y + ring, home.y + home.h - 3 - ring), plan.rows - SLOT_H - ring),
   ]),
  )
  const rivals = [...this.#slots].filter(([other]) => other[0] === name[0]).map(([, { slot }]) => slot)
  const apart = ([a, b]) =>
   rivals.every(([c, d]) => Math.abs(a - c) >= SLOT_W || Math.abs(b - d) >= (ring ? SLOT_H : 1))
  const slot = (this.strip ? [x - 2, y - 1] : (near.find(apart) ?? near[0]))
  this.#slots.set(name, { slot, cell })
  return slot
 }
 #ping(x, y, age, ink) {
  if (this.strip || age < 0 || age >= PING) return
  const faded = mix(ink, this.inks.paper, Math.round((4 * age) / PING) / 5)
  for (const [a, b] of circle(3 + 9 * Math.sqrt(age / PING))) this.canvas.dot(2 * x + a, 4 * y + b, faded)
 }
 #lead({ path, line }, age, phase) {
  const { inks } = this
  const [x, y] = this.plan.cell(path, line)
  this.#ping(x - 3, y - 1, age, inks.lead)
  const pulse = this.motion ? Math.round(1.5 + 1.5 * Math.sin(phase)) / 6 : 0
  return [x, y, [[this.strip ? '⣿' : '◆', mix(inks.lead, inks.peak, pulse)]]]
 }
 #candidate({ id, path, line, votes, outcome }, age, now) {
  const { inks, canvas } = this
  if (outcome === 'refuted' && age >= DUST) {
   this.#slots.delete('C' + id)
   return []
  }
  const [x, y] = this.#slot('C' + id, path, line)
  const start = x + ((SLOT_W - id.length - 1) >> 1)
  if (this.strip) {
   if (outcome === 'refuted') return []
   const mark = outcome === 'confirmed' ? ['◆', inks.chip, inks.clay] : ['◇', inks.strong]
   return [[x + 2, y + 1, [(mark)]]]
  }
  if (outcome === 'refuted') {
   this.#dust(x, y, age / DUST)
   return age < DUST / 2
    ? [[start + 1, y + 1, [[id, mix(inks.name, inks.hairline, Math.round((8 * age) / DUST) / 4)]]]]
    : []
  }
  if (outcome !== 'testing' && age > LOCK) {
   this.#ping(x, y, age - LOCK, inks.clay)
   const [ink, paper] = outcome === 'confirmed' ? [inks.chip, inks.clay] : [inks.lead, inks.raised]
   return [[start, y + 1, [[' ' + id + ' ', ink, paper]]]]
  }
  if (!this.rings) {
   const pips = LENSES.map(lens => [
    VOTE[votes[lens]],
    votes[lens] === 'pending' ? inks.faint : LENS_INK[lens],
    inks.raised,
   ])
   return [[x, y + 1, ([[id, inks.strong, inks.raised], ...pips])]]
  }
  const odd = id.length % 2
  for (let row = 0; row < SLOT_H; row++) canvas.put(x, y + row, [[' '.repeat(SLOT_W + odd), inks.faint]])
  RING.forEach((dot, n) => {
   const lens = LENSES[dot.y > 7 ? 1 : dot.x + odd > 5 ? 0 : 2]
   const vote = votes[lens]
   const sweeps = this.motion && (((3 * dot.turn - now) % 1) + 1) % 1 > 0.6
   const yes = vote === 'confirm' || vote === 'older'
   const shown = yes || (vote === 'pending' ? dot.outer || sweeps : dot.outer && n % 3 === 0)
   if (!shown) return
   const ink = LENS_INK[lens]
   const pen = yes ? ink : vote === 'pending' ? mix(ink, inks.paper, 0.4) : inks.faint
   canvas.dot(2 * x + dot.x + odd, 4 * y + dot.y, pen)
  })
  return [[start + 1, y + 1, [[id, inks.strong]]]]
 }
 #dust(x, y, share) {
  const ink = mix(this.inks.name, this.inks.hairline, Math.round(4 * share) / 4)
  RING.forEach((dot, n) => {
   const chance = (n * 0.618) % 1
   const [across, down] = [(dot.x - 5.5) * share * chance, (dot.y - 2) * share * chance + 9 * share ** 2]
   if (chance <= share * 1.1) return
   this.canvas.dot(2 * x + dot.x + Math.round(across), 4 * y + dot.y + Math.round(down), ink)
  })
 }
 #finding({ id, file, line, severity }, age) {
  if (age < 0) return []
  const { inks, plan, canvas } = this
  const ink = SEVERITY[severity] ? rgb(SEVERITY[severity]) : inks.name
  for (const { cell } of plan.strokes[plan.atlas.find(file)]) canvas.cells[3 * cell + 1] = ink
  const [x, y] = this.#slot('F' + id, file, line)
  this.#ping(x, y, age, ink)
  const name = fit(narrow(id), 4)
  if (this.strip) return [[x + 2, y + 1, [[narrow(severity).slice(0, 1), inks.chip, ink]]]]
  return [[x + ((SLOT_W - name.length - 1) >> 1), y + 1, [[' ' + name + ' ', inks.chip, ink]]]]
 }
}
