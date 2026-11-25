import { CLAY, LENS, SEVERITY } from './palette.js'
import { Plan } from './plan.js'
import { LENSES, STAGES } from './scan.js'
import { count, filesOf, fit } from './words.js'
const [PAPER, HAIRLINE, SLATE, ASH, STONE, IVORY] = ['#141413', '#30302e', '#5e5d59', '#87867f', '#c2c0b6', '#faf9f5']
const [UNREAD, SHIMMER, SKY, AMBER] = ['#3d3d3a', '#eb9f7f', '#6a9bcc', '#d9b36c']
const READ = ['#8f8d85', '#b8b5aa', '#e3dacc']
const [LAG, SWEEP, COOL, RIPPLE, FLIGHT, REVEAL, DUST] = [1, 1, 7, 1.2, 0.7, 1.6, 2.2]
const [DOT, EDGE, RAIL, FOOT, RING] = [2.5, 14, 46, 44, 11]
const [RIPPLES, ARRIVAL, HELD] = [4, 0.22, 3.5]
const ONE_ROW = 520
const MAP_CHARS = 124_000
const SANS = 'system-ui,-apple-system,Segoe UI,sans-serif'
const MONO = 'ui-monospace,SF Mono,Menlo,Consolas,monospace'
const escaped = text => text.replace(/[&<>"]/g, ch => '&#' + ch.charCodeAt(0) + ';')
const short = n => String(Math.round(n * 100) / 100)
function tag(name, attributes, ...children) {
 const given = Object.entries(attributes).filter(([, value]) => value !== undefined)
 const spelled = given.map(
  ([key, value]) => ' ' + key + '="' + (typeof value === 'number' ? short(value) : value) + '"',
 )
 return '<' + name + spelled.join('') + '>' + children.join('') + '</' + name + '>'
}
const animate = (attributeName, values, begin, seconds) =>
 tag('animate', { attributeName, values, begin: short(begin) + 's', dur: seconds + 's', fill: 'freeze' })
const pulse = (values, seconds, at) =>
 tag('animate', {
  attributeName: 'opacity',
  values,
  dur: seconds + 's',
  begin: short(-(at % seconds)) + 's',
  repeatCount: 'indefinite',
 })
const label = (x, y, words, look) => tag('text', { x, y, ...look }, escaped(words))
function strokes(bars) {
 return bars
  .map((bar, n) => {
   const { x, y, w } = bars[n - 1] ?? { x: 0, y: 0, w: 0 }
   return 'm' + (bar.x - x - w) + ' ' + (bar.y - y) + 'h' + bar.w
  })
  .join('')
}
export class Chart {
 #plan
 #drawn = ''
 #lit = 0
 #shown = { at: -Infinity, source: '' }
 constructor(scan, atlas, width, height, motion) {
  this.scan = scan
  this.atlas = atlas
  this.width = width
  this.height = height
  this.motion = motion
 }
 fits(...given) {
  return [this.scan, this.atlas, this.width, this.height, this.motion].every((held, n) => held === given[n])
 }
 source(now) {
  if (!this.scan.running || now - this.#shown.at >= 0.9 * LAG) this.#shown = { at: now, source: this.#draw(now) }
  return this.#shown.source
 }
 #draw(now) {
  const { width } = this
  const height = RAIL + this.height + FOOT * (width < ONE_ROW ? 2 : 1) + EDGE
  return tag(
   'svg',
   {
    'xmlns': 'http://www.w3.org/2000/svg',
    width,
    height,
    'viewBox': '0 0 ' + width + ' ' + height,
    'font-family': SANS,
   },
   tag('rect', { width, height, rx: 12, fill: PAPER }),
   this.#rail(now),
   this.atlas?.plots.length ? this.#map(this.atlas, now - LAG) : '',
   this.#figures(),
  )
 }
 #rail(now) {
  const step = (this.width - 2 * EDGE + 6) / STAGES.length
  const colors = { waiting: SLATE, running: SHIMMER, done: STONE, failed: SEVERITY.CRITICAL, skipped: SLATE }
  return STAGES.map((stage, n) => {
   const state = this.scan.phases.get(stage)?.state ?? 'waiting'
   const x = EDGE + n * step
   const running = state === 'running'
   const line = {
    x,
    y: EDGE,
    width: step - 6,
    height: 2,
    rx: 1,
    fill: running ? CLAY : state === 'done' ? ASH : HAIRLINE,
   }
   const look = { 'font-size': step < 66 ? 9 : 11, 'fill': colors[state], 'font-weight': running ? 600 : 400 }
   const skipped = state === 'skipped' ? { 'text-decoration': 'line-through' } : {}
   return (
    tag('rect', line, running && this.motion ? pulse('1;.45;1', 2, now) : '') +
    label(x, EDGE + 18, stage, { ...look, ...skipped })
   )
  }).join('')
 }
 #figures() {
  const t = this.scan.totals()
  const step = (n, noun, color = IVORY) => [
   count(n),
   noun,
   n ? color : SLATE,
  ]
  const all = [
   [filesOf(t), 'files'],
   [count(t.linesRead), 'lines'],
   [count(t.agents), 'agents'],
   [count(t.tools), 'calls'],
   step(t.leads, 'leads', AMBER),
   step(t.candidates, 'candidates'),
   step(t.confirmed, 'confirmed', CLAY),
   step(t.refuted, 'refuted', STONE),
  ]
  const across = this.width < ONE_ROW ? 4 : 8
  const starts = across === 4 ? [0, 0.3, 0.56, 0.8] : [0, 0.17, 0.295, 0.42, 0.545, 0.67, 0.795, 0.92]
  return all
   .map(([figure, noun, color = IVORY], n) => {
    const x = EDGE + starts[n % across] * (this.width - 2 * EDGE)
    const y = RAIL + this.height + 24 + Math.floor(n / across) * FOOT
    const big = { 'font-size': 14, 'font-family': MONO, 'fill': color }
    const named = figure === '1' ? noun.replace(/s$/, '') : noun
    return label(x, y, figure, big) + label(x, y + 16, named, { 'font-size': 10.5, 'fill': ASH })
   })
   .join('')
 }
 #map(atlas, start) {
  const { scan, motion } = this
  const plan = this.#planFor(atlas)
  const since = (at) => at - start
  const reads = scan.touches.filter(touch => touch.kind === 'read' && atlas.find(touch.path) !== undefined)
  const live = motion && scan.running
  for (const touch of reads.filter(each => each.rev > this.#lit && (!live || since(each.at) < -FLIGHT - SWEEP))) {
   this.#develop(plan, touch.path, [[touch.first, touch.last]])
   this.#lit = touch.rev
  }
  const bars = plan.bars.flat()
  const layer = (tone, stroke) =>
   tag('path', { d: 'M0 .5' + strokes(bars.filter(bar => bar.tone === tone)), stroke })
  const at = (path, line) =>
   plan.dot(path, line).map(n => (n + 0.5) * DOT)
  const read = tag(
   'g',
   { opacity: scan.candidates.size ? 0.62 : 1 },
   ...READ.map((stroke, tone) => layer(tone, stroke)),
  )
  const code = layer(undefined, UNREAD) + read
  const readsOf = (agent) => reads.filter(touch => touch.agent === agent)
  const glints = scan.working.map(agent => this.#glint(readsOf(agent.id), LENS[agent.lens] ?? CLAY, at, start))
  const marks = scan.reported
   ? scan.findings.map((found, n) => this.#pin(found, at, since(scan.finished) + Math.min(n, 16) * ARRIVAL))
   : [...scan.candidates.values()].map(found => this.#ring(found, at, start))
  const warm = live ? reads.filter(touch => since(touch.at) > -COOL).reverse() : []
  let room = MAP_CHARS - code.length
  const fitting = (markup) => {
   if (markup.length >= room) return false
   room -= markup.length
   return true
  }
  const [regions, onTop, moving] = [
   [this.#regions(plan, since(scan.mapped))],
   [this.#leads(at, start), ...marks],
   [live ? this.#ripples(plan, start) : '', ...glints],
  ].map(parts => parts.filter(fitting))
  const held = scan.working.flatMap(agent => readsOf(agent.id).slice(-1))
  const glows = [...new Set([...held, ...warm])]
   .map(touch => this.#glow(plan, touch, held.includes(touch) ? Math.max(since(touch.at), -HELD) : since(touch.at)))
   .filter(fitting)
  const stretch = (this.width - 2 * EDGE + 3) / (2 * (plan.cols - 1) * DOT)
  return tag(
   'g',
   { transform: 'translate(' + (EDGE - DOT - 1.5) + ' ' + RAIL + ') scale(' + stretch.toFixed(4) + ' 1)' },
   tag('g', { 'transform': 'scale(' + DOT + ')', 'stroke-width': 0.56, 'fill': 'none' }, code, ...glows.reverse()),
   ...moving,
   ...regions,
   ...onTop,
  )
 }
 #planFor(atlas) {
  const drawn = atlas.rev + ' ' + this.scan.mapped
  const missed = this.scan.forgotten > this.#lit
  if (this.#plan && drawn === this.#drawn && !missed) return this.#plan
  const [cols, rows] = [Math.floor((this.width - 2 * EDGE) / DOT / 2) + 1, Math.floor(this.height / DOT / 4)]
  const plan = new Plan(atlas, this.scan.components, cols, rows, 2)
  for (const [path, { spans }] of this.scan.visits) this.#develop(plan, path, spans)
  this.#plan = plan
  this.#drawn = drawn
  this.#lit = this.scan.rev
  return plan
 }
 #develop(plan, path, spans) {
  const tone = this.#toneOf(path)
  for (const [first, last] of spans) for (const bar of plan.between(plan.bars, path, first, last)) bar.tone = tone
 }
 #toneOf(path) {
  return Math.min(this.scan.visits.get(path)?.reads ?? 1, READ.length) - 1
 }
 #glow(plan, { rev, path, first, last }, begin) {
  const bars = plan.between(plan.bars, path, first, last)
  if (!bars.length) return ''
  const place = plan.places[this.atlas?.find(path) ?? 0]
  const lit = this.motion ? begin + FLIGHT / 2 : 0
  const moves = (markup) => (this.motion ? markup : '')
  const [y, high] = [bars[0].y, (bars.at(-1)?.y ?? 0) - bars[0].y + 1]
  const box = { x: place.x - 0.4, y, width: place.w + 0.8, height: lit > 0 ? 0 : high }
  const cools = [IVORY, SHIMMER, CLAY, CLAY, READ[this.#toneOf(path)]].join(';')
  return (
   tag('clipPath', { id: 'r' + rev }, tag('rect', box, moves(animate('height', '0;' + high, lit, SWEEP)))) +
   tag(
    'g',
    { 'clip-path': 'url(#r' + rev + ')' },
    tag('path', { d: 'M0 .5' + strokes(bars), stroke: CLAY }, moves(animate('stroke', cools, lit, COOL))),
   )
  )
 }
 #regions(plan, begin) {
  const named = this.scan.components.length > 0
  const busy = new Set(this.scan.working.map(agent => this.atlas?.find(agent.path)))
  const drawing = named && this.motion && begin > -REVEAL
  const files = plan.names.map(({ plot, text, x, y, w }) =>
   label(2 * x * DOT, (4 * y + 3.2) * DOT, fit(text, w), { 'font-size': 8, 'fill': busy.has(plot) ? SHIMMER : ASH }),
  )
  return plan.regions
   .map(({ group, box }) => {
    const [x, y, width, height] = [
     (2 * box.x + 1) * DOT,
     (4 * box.y + 0.5) * DOT,
     2 * (box.w - 1) * DOT,
     4 * (box.h - 1) * DOT,
    ]
    const dashes = drawing ? { 'pathLength': 1, 'stroke-dasharray': 1, 'stroke-dashoffset': 1 } : {}
    const draws =
     animate('stroke-dashoffset', '1;0', begin, REVEAL) +
     animate('stroke', CLAY + ';' + CLAY + ';' + HAIRLINE, begin, REVEAL)
    const frame = {
     x: x + 1.5,
     y: y - 1.5,
     width: width - 3,
     height: height - 3,
     rx: 4,
     fill: 'none',
     stroke: HAIRLINE,
     ...dashes,
    }
    const fill = group.plots.some(plot => busy.has(plot)) ? SHIMMER : group.scanned ? STONE : SLATE
    const name = width > 30 && height > 24 ? fit(group.name, Math.floor((width - 8) / 5.2), !group.scanned) : ''
    return (
     (named ? tag('rect', frame, drawing ? draws : '') : '') +
     label(x + 2 * DOT, y + 7.5, name, { 'font-size': 9, fill })
    )
   })
   .concat(files)
   .join('')
 }
 #ripples(plan, start) {
  const recent = this.scan.touches.filter(touch => touch.kind === 'search' && touch.at - start > -RIPPLE)
  return recent
   .slice(-RIPPLES)
   .map(({ path, at }) => {
    const places = this.atlas?.under(path).map(plot => plan.places[plot]) ?? []
    if (!places.length) return ''
    const mean = (key, size) =>
     (places.reduce((sum, place) => sum + place[key] + place[size] / 2, 0) / places.length) * DOT
    const [cx, cy] = [mean('x', 'w'), mean('y', 'h')]
    const reach = Math.sqrt(places.reduce((sum, place) => sum + place.w * place.h, 0)) * DOT * 0.8
    const spreads =
     animate('r', '0;' + short(reach), at - start, RIPPLE) + animate('opacity', '.7;.4;0', at - start, RIPPLE)
    return tag(
     'circle',
     { cx, cy, 'r': 0, 'fill': SKY, 'fill-opacity': 0.12, 'stroke': SKY, 'opacity': 0 },
     spreads,
    )
   })
   .join('')
 }
 #leads(at, start) {
  const { scan } = this
  if (!scan.running) return ''
  const open = scan.openLeads(path => this.atlas?.find(path) !== undefined)
  const spots = open.map(({ path, line }) => at(path, line).map(short))
  const diamonds = spots.map(([x, y]) => 'M' + x + ' ' + y + 'm0-5l3.6 5l-3.6 5l-3.6-5z').join('')
  const fade = this.motion ? pulse('1;.6;1', 2.5, start) : ''
  return tag('path', { 'd': diamonds, 'fill': AMBER, 'stroke': PAPER, 'stroke-width': 1.2 }, fade)
 }
 #glint(reads, halo, at, start) {
  const last = reads.at(-1)
  if (!last) return ''
  const [[x0, y0], [x1, y1]] = [reads.at(-2) ?? last, last].map(touch => at(touch.path, touch.first))
  const spark = tag('circle', { r: 7, fill: halo, opacity: 0.34 }) + tag('circle', { r: 2.6, fill: IVORY })
  const begin = last.at - start
  const there = { transform: 'translate(' + short(x1) + ' ' + short(y1) + ')' }
  if (!this.motion || begin < -2 * FLIGHT) return tag('g', there, spark)
  const [dx, dy] = [x0 - x1, y0 - y1]
  const arc =
   'M' + short(dx) + ' ' + short(dy) + 'Q' + short(dx / 2) + ' ' + short(dy / 2 - Math.hypot(dx, dy) / 4) + ' 0 0'
  const ease = { calcMode: 'spline', keyTimes: '0;1', keySplines: '.215 .61 .355 1', keyPoints: '0;1' }
  const waits = tag('animateMotion', { path: 'M' + short(dx) + ' ' + short(dy) + 'h0', dur: '9s' })
  const flies = tag('animateMotion', {
   path: arc,
   begin: short(begin) + 's',
   dur: FLIGHT + 's',
   fill: 'freeze',
   ...ease,
  })
  const trail = {
   'd': arc,
   'fill': 'none',
   'stroke': SHIMMER,
   'pathLength': 1,
   'stroke-dasharray': 1,
   'stroke-dashoffset': 1,
   'opacity': 0,
  }
  const fades =
   animate('stroke-dashoffset', '1;.15;0;0', begin, 2 * FLIGHT) +
   animate('opacity', '.9;.6;.25;0', begin, 2 * FLIGHT)
  return tag('g', there, tag('path', trail, fades), tag('g', {}, waits, flies, spark))
 }
 #ring({ id, path, line, votes, outcome, settled = 0 }, at, start) {
  const begin = settled - start
  const gone = outcome === 'refuted'
  if (this.atlas?.find(path) === undefined || (gone && (!this.motion || begin < -DUST))) return ''
  const [x, y] = this.#inside(path, at(path, line))
  const kept = outcome === 'confirmed'
  const point = (turn) =>
   [RING * Math.sin(turn * 2 * Math.PI), -RING * Math.cos(turn * 2 * Math.PI)].map(short)
  const arcs = LENSES.map((lens, n) => {
   const d = 'M' + point(n / 3 + 0.03).join(' ') + 'A' + RING + ' ' + RING + ' 0 0 1 ' + point(n / 3 + 0.3).join(' ')
   const vote = votes[lens]
   const pending = vote === 'pending'
   const dashes = vote === 'confirm' || vote === 'older' || pending ? undefined : '1 3'
   return tag('path', {
    d,
    'stroke': pending ? SLATE : LENS[lens],
    'stroke-width': pending ? 1.2 : 2.4,
    'stroke-dasharray': dashes,
   })
  })
  const grows = tag('animateTransform', {
   attributeName: 'transform',
   type: 'scale',
   values: '1;1;1.7',
   begin: short(begin) + 's',
   dur: DUST + 's',
   fill: 'freeze',
  })
  return tag(
   'g',
   { transform: 'translate(' + short(x) + ' ' + short(y) + ')' },
   gone ? animate('opacity', '1;1;0', begin, DUST) : '',
   tag('circle', { r: RING + 2, fill: PAPER, opacity: 0.86 }),
   kept ? tag('circle', { r: RING - 2.6, fill: CLAY }) : '',
   tag('g', { 'fill': 'none', 'stroke-linecap': 'round' }, gone ? grows : '', ...arcs),
   label(0, 3, id, {
    'font-size': 8.5,
    'font-family': MONO,
    'text-anchor': 'middle',
    'font-weight': 600,
    'fill': kept ? PAPER : IVORY,
   }),
  )
 }
 #pin({ id, file, line, severity }, at, begin) {
  if (this.atlas?.find(file) === undefined) return ''
  const [x, y] = this.#inside(file, at(file, line))
  const fill = SEVERITY[severity] ?? STONE
  const arriving = this.motion && begin > -1
  const pings = animate('r', '6;34;17', begin, 1) + animate('opacity', '.6;.1;.18', begin, 1)
  const type = { 'font-size': 9.5, 'font-family': MONO, 'text-anchor': 'middle', 'font-weight': 700, 'fill': PAPER }
  return tag(
   'g',
   {},
   arriving && begin > 0 ? tag('set', { attributeName: 'opacity', to: 0, dur: short(begin) + 's' }) : '',
   tag('circle', { cx: x, cy: y, r: 17, fill, opacity: 0.18 }, arriving ? pings : ''),
   tag('rect', { x: x - 12, y: y - 8, width: 24, height: 16, rx: 4, fill, stroke: PAPER }),
   label(x, y + 3.4, fit(id, 4), type),
  )
 }
 #inside(path, [x, y]) {
  const home = this.#plan?.homes[this.atlas?.find(path) ?? -1] ?? { x: 0, y: 0, w: 1, h: 1 }
  const held = (n, low, high) =>
   low > high ? (low + high) / 2 : Math.min(Math.max(n, low), high)
  return [
   held(x, (2 * home.x + 2) * DOT + RING + 1, 2 * (home.x + home.w - 1) * DOT - RING - 1),
   held(y, (4 * home.y + 4) * DOT + RING + 1, 4 * (home.y + home.h - 1) * DOT - RING - 3),
  ]
 }
}
