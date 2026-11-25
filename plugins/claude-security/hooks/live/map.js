import { Canvas } from './canvas.js'
import { Marks } from './marks.js'
import { BARE, LENS, mix, rgb } from './palette.js'
import { Plan } from './plan.js'
import { fit, narrow } from './words.js'
const [SWEEP, COOL, RIPPLE, FLIGHT, REVEAL] = [1, 7, 1.1, 0.7, 1.6]
const REPLAN = 0.4
const STEPS = 12
const RIPPLES = 4
export class CodeMap {
 #rev = 0
 #traced = -1
 #planned = -Infinity
 #components
 #plan
 #marks
 #dots = new Uint32Array()
 #lit = new Uint32Array()
 #litMasks = new Uint8Array()
 #tone = new Uint8Array()
 #shade = new Uint8Array()
 #sweeps = []
 #ripples = []
 #flights = new Map()
 #hot = new Map()
 constructor(scan, atlas, cols, rows, { inks, motion, solid, mono }) {
  this.scan = scan
  this.atlas = atlas
  this.cols = cols
  this.rows = rows
  this.inks = inks
  this.motion = motion
  this.mono = mono
  this.canvas = new Canvas(cols, rows, solid ? inks.paper : BARE)
  this.#components = scan.components
  this.#rev = scan.rev
  this.#remap()
 }
 fits(scan, atlas, cols, rows) {
  return scan === this.scan && atlas === this.atlas && cols === this.cols && rows === this.rows
 }
 draw(now) {
  this.#follow(now)
  this.#heat(now)
  if (!this.motion && !this.scan.running) this.#hot.clear()
  this.canvas.begin(this.mono ? this.#litMasks : this.#plan.masks, cell => this.#base(cell))
  this.#drawRipples(now)
  this.#drawHeat(now)
  this.#drawTrails(now)
  this.#drawAgents(now)
  const busy = new Set(this.scan.working.map(agent => this.atlas.find(agent.path)))
  this.#drawNames(busy)
  const labels = this.#marks.draw(now)
  this.#drawBorders(now, busy)
  for (const label of labels) this.canvas.put(...label)
  return this.canvas.cells
 }
 #remap() {
  this.#replan()
  this.#marks = new Marks(this.scan, this.#plan, this.canvas, this.inks, this.motion)
  for (const flight of this.#flights.values()) flight.start = flight.end
  const before = new Map(this.motion ? this.#flights : [])
  for (const touch of this.scan.touches) if (touch.rev <= this.#rev) this.#fly(touch, -Infinity)
  for (const [agent, flight] of before) {
   const { path, first, last } = this.#flights.get(agent)
   if (path === flight.path && first === flight.first && last === flight.last) this.#flights.set(agent, flight)
  }
 }
 #replan() {
  const plan = new Plan(this.atlas, this.scan.components, this.cols, this.rows)
  this.#plan = plan
  if (this.#marks) this.#marks.plan = plan
  const size = plan.masks.length
  this.#dots = new Uint32Array(size)
  this.#lit = new Uint32Array(size)
  this.#litMasks = new Uint8Array(size)
  this.#tone = new Uint8Array(size)
  this.#shade = new Uint8Array(size)
  plan.strokes.forEach((strokes, plot) => {
   for (const { cell, dots } of strokes) {
    this.#dots[cell] += dots
    this.#shade[cell] = plot % 3
   }
  })
  for (const sweep of this.#sweeps) Object.assign(sweep, { strokes: this.#strokes(sweep.touch), passed: 0 })
  for (const flight of this.#flights.values()) {
   flight.end = plan.dot(flight.path, flight.first)
   if (!this.motion) flight.start = flight.end
  }
  this.#traced = this.atlas.rev
  for (const path of this.scan.visits.keys()) this.#develop(path)
 }
 #strokes({ path, first, last }) {
  return this.#plan.between(this.#plan.strokes, path, first, last)
 }
 #develop(path) {
  const visit = this.scan.visits.get(path)
  for (const [first, last] of visit?.spans ?? []) {
   for (const stroke of this.#strokes({ path, first, last })) this.#light(stroke, this.#toneOf(path))
  }
 }
 #toneOf(path) {
  return Math.min(this.scan.visits.get(path)?.reads ?? 1, 3) - 1
 }
 #light(stroke, tone) {
  this.#tone[stroke.cell] = tone
  if (stroke.lit) return
  stroke.lit = true
  this.#lit[stroke.cell] += stroke.dots
  this.#litMasks[stroke.cell] = this.#plan.masks[stroke.cell]
 }
 #base(cell) {
  const { unread, part, read, dusk } = this.inks
  const thirds = Math.round((3 * this.#lit[cell]) / (this.#dots[cell] || 1))
  if (this.scan.candidates.size) return dusk[thirds]
  if (thirds < 3) return thirds ? part[thirds - 1] : unread[this.#shade[cell]]
  return read[this.#tone[cell]]
 }
 #follow(now) {
  const { scan } = this
  if (scan.components !== this.#components || this.atlas.plots.length !== this.#plan.places.length) {
   this.#components = scan.components
   this.#ripples = []
   this.#hot.clear()
   this.#remap()
  } else if (this.atlas.rev !== this.#traced && now - this.#planned > REPLAN) {
   this.#planned = now
   this.#replan()
  }
  if (scan.forgotten > this.#rev) for (const path of scan.visits.keys()) this.#develop(path)
  for (const touch of scan.touches.filter(each => each.rev > this.#rev)) {
   this.#fly(touch, now)
   if (touch.kind === 'search') {
    if (this.motion && this.#ripples.length < RIPPLES) this.#ripple(touch.path, now)
   } else {
    const strokes = this.#strokes(touch)
    this.#sweeps.push({ born: this.motion ? now + FLIGHT / 2 : -Infinity, touch, strokes, passed: 0 })
   }
  }
  this.#rev = scan.rev
 }
 #fly({ kind, agent, path, first, last }, now) {
  if (kind !== 'read' || this.atlas.find(path) === undefined) return
  const end = this.#plan.dot(path, first)
  const start = (this.motion && this.#flights.get(agent)?.end) || end
  this.#flights.set(agent, { born: now, start, end, path, first, last })
 }
 #along({ start: [x0, y0], end: [x1, y1] }, share) {
  const lift = this.rows < 3 ? 0 : (Math.sin(share * Math.PI) * Math.hypot(x1 - x0, y1 - y0)) / 7
  return [Math.round(x0 + (x1 - x0) * share), Math.round(y0 + (y1 - y0) * share - lift)]
 }
 #ripple(path, now) {
  const { cols } = this
  const found = [...new Set(this.atlas.under(path).flatMap(plot => this.#plan.strokes[plot].map(s => s.cell)))]
  if (!found.length) return
  const mean = (values) => values.reduce((sum, n) => sum + n, 0) / values.length
  const [x, y] = [mean(found.map(cell => cell % cols)), mean(found.map(cell => Math.floor(cell / cols)))]
  const near = found.map(cell => [Math.hypot((cell % cols) - x, 2 * (Math.floor(cell / cols) - y)), cell])
  this.#ripples.push({ born: now, near: (near) })
 }
 #drawRipples(now) {
  const { cells } = this.canvas
  this.#ripples = this.#ripples.filter(ripple => now - ripple.born < RIPPLE)
  for (const { born, near } of this.#ripples) {
   const reach = near.reduce((most, [far]) => Math.max(most, far), 0)
   const band = Math.max(reach / 3, 3)
   const front = ((now - born) / RIPPLE) * (reach + band)
   for (const [far, cell] of near) {
    if (far > front || far < front - band) continue
    const share = Math.round(4 * (1 - (front - far) / band)) / 6
    cells[3 * cell + 1] = mix(cells[3 * cell + 1], this.inks.ripple, share)
   }
  }
 }
 #heat(now) {
  for (const sweep of this.#sweeps) {
   const front = Math.ceil(sweep.strokes.length * Math.min(Math.max((now - sweep.born) / SWEEP, 0), 1))
   for (const stroke of sweep.strokes.slice(sweep.passed, front)) {
    this.#light(stroke, this.#toneOf(sweep.touch.path))
    this.#hot.set(stroke.cell, now)
   }
   sweep.passed = front
  }
  this.#sweeps = this.#sweeps.filter(sweep => sweep.passed < sweep.strokes.length)
  for (const { id } of this.scan.working) {
   const flight = this.#flights.get(id)
   if (!flight || now - flight.born < FLIGHT + SWEEP) continue
   const warm = now - COOL * (0.3 + (this.motion ? 0.06 * Math.sin(2 * now + id) : 0))
   for (const { cell } of this.#strokes(flight)) this.#hot.set(cell, Math.max(this.#hot.get(cell) ?? warm, warm))
  }
 }
 #drawHeat(now) {
  const { inks } = this
  const { cells } = this.canvas
  for (const [cell, lit] of this.#hot) {
   const share = Math.round(STEPS * Math.max(1 - (now - lit) / COOL, 0) ** 1.6) / STEPS
   if (!share) this.#hot.delete(cell)
   else if (!this.motion) cells[3 * cell + 1] = inks.clay
   else if (share > 0.85) cells[3 * cell + 1] = mix(inks.shimmer, inks.peak, (share - 0.85) / 0.15)
   else if (share > 0.55) cells[3 * cell + 1] = mix(inks.clay, inks.shimmer, (share - 0.55) / 0.3)
   else cells[3 * cell + 1] = mix(cells[3 * cell + 1], inks.clay, share / 0.55)
  }
 }
 #drawTrails(now) {
  const { inks } = this
  const { cells } = this.canvas
  for (const flight of this.#flights.values()) {
   const age = (now - flight.born) / FLIGHT
   const steps = Math.round(Math.hypot(flight.end[0] - flight.start[0], flight.end[1] - flight.start[1]))
   if (age > 1.6) continue
   for (let step = Math.max(Math.floor((age - 0.6) * steps), 0); step < Math.min(age, 1) * steps; step++) {
    const [x, y] = this.#along(flight, step / steps)
    const faded = Math.min(Math.round((age - step / steps) / 0.15) / 4, 1)
    const cell = 3 * ((y >> 2) * this.cols + (x >> 1)) + 1
    if (this.rows < 3) cells[cell] = mix(inks.shimmer, cells[cell], faded)
    else this.canvas.dot(x, y, mix(inks.shimmer, inks.hairline, faded))
   }
  }
 }
 #drawNames(busy) {
  for (const { plot, text, x, y, w } of this.#plan.names) {
   const spaced = (fit(narrow(text), w) + ' ').slice(0, w)
   this.canvas.put(x, y, [[spaced, busy.has(plot) ? this.inks.shimmer : this.inks.faint]])
  }
 }
 #drawBorders(now, busy) {
  const { cols, rows, inks, scan } = this
  const named = scan.components.length > 0
  const front = this.motion && named ? ((now - scan.mapped) / REVEAL) * (cols + 2 * rows + 8) : Infinity
  for (const [cell, glyph] of this.#plan.borders) {
   const [x, y] = [cell % cols, Math.floor(cell / cols)]
   const drawn = x > 0 && x < cols - 1 ? glyph : glyph === '│' ? ' ' : '─'
   const behind = front - x - 2 * y
   if (named && behind > 0) this.canvas.put(x, y, [[drawn, behind < 6 ? inks.clay : inks.hairline]])
   else this.canvas.put(x, y, [[y === 0 || y === rows - 1 ? '─' : ' ', inks.hairline]])
  }
  for (const { group, box } of this.#plan.regions) {
   if (!group.name || box.w < 6 || box.h < 3 || front < box.x + 2 * box.y + 8) continue
   const ink = group.plots.some(plot => busy.has(plot)) ? inks.shimmer : group.scanned ? inks.name : inks.faint
   const start = box.x ? box.x + 1 : 0
   const room = (box.x + box.w < cols ? box.x + box.w - 1 : cols) - start
   const name = fit(narrow(group.name), room, !group.scanned)
   this.canvas.put(start, box.y, [[((start && name.length < room ? ' ' : '') + name + ' ').slice(0, room), ink]])
  }
 }
 #drawAgents(now) {
  const { inks } = this
  for (const agent of this.scan.working) {
   const flight = this.#flights.get(agent.id)
   if (!flight) continue
   const [x, y] = this.#plan.within(this.#along(flight, Math.min((now - flight.born) / FLIGHT, 1)))
   if (this.#plan.borders.has(y * this.cols + x)) continue
   this.canvas.put(x, y, [['✻', LENS[agent.lens] ? rgb(LENS[agent.lens]) : inks.peak]])
  }
 }
}
