import { squarify } from './atlas.js'
import { clean } from './words.js'
export const DOT = [
 [0x01, 0x08],
 [0x02, 0x10],
 [0x04, 0x20],
 [0x40, 0x80],
]
const [UP, DOWN, LEFT, RIGHT] = [1, 2, 4, 8]
const LINES = ' │││─╯╮┤─╰╭├─┴┬┼'
const CELLS_PER_REGION = 66
const [SHORTEST_LINE, LONGEST_LINE] = [30, 96]
const [DOTS_FOR_A_NAME, WIDEST_PITCH] = [17, 4]
const [LEFT_OVER, LEFT_OVER_SHARE] = [4, 0.4]
function groupsOf(atlas, components, room) {
 const seen = new Set()
 const fresh = (i) => !seen.has(i) && seen.add(i)
 const total = (groups) => groups.reduce((sum, group) => sum + group.weight, 0)
 const group = (name, plots, scanned) =>
  plots.length ? [{ name: clean(name, 60), plots, scanned, weight: atlas.weight(plots) }] : []
 const wide = ({ paths }) => Number(paths.some(path => /^(\*|$)/.test(path)))
 const plotsOf = ({ paths, literal }) =>
  paths.flatMap(path => (literal ? (atlas.find(path) ?? []) : atlas.matching(path)))
 const named = [...components]
  .sort((a, b) => wide(a) - wide(b))
  .flatMap(part => group(part.name, plotsOf(part).filter(fresh), true))
 const left = atlas.plots.map((_, i) => i).filter(fresh)
 const rest = folders(atlas, left, named.length ? LEFT_OVER : 4 * LEFT_OVER).flatMap(([name, held]) =>
  group(name, held, false),
 )
 const damped = named.length ? Math.min((LEFT_OVER_SHARE * total(named)) / total(rest), 1) : 1
 for (const each of rest) each.weight *= damped
 const largestFirst = (groups) => groups.sort((a, b) => b.weight - a.weight)
 const ranked = largestFirst([...named, ...rest])
 const least = total(ranked) / (3 * room)
 const large = ranked.filter(each => each.weight >= least).length
 if (large === ranked.length && large <= room) return ranked
 const alone = total(ranked.slice(large)) >= least
 const more = ranked.splice(Math.max(Math.min(alone ? large : large - 1, room - 1), 0))
 const [first] = more.sort((a, b) => Number(b.scanned) - Number(a.scanned) || Number(!a.name) - Number(!b.name))
 const others = more.filter(each => each.name).length - 1
 const name = first.name + (others > 0 ? ' +' + others : '')
 return largestFirst([...ranked, { ...first, name, plots: more.flatMap(each => each.plots), weight: total(more) }])
}
function folders(atlas, plots, most) {
 let best = new Map([['', plots]])
 for (let depth = 1; depth < 5; depth++) {
  const cut = new Map()
  for (const i of plots) {
   const name = atlas.plots[i].path.split('/').slice(0, -1).slice(0, depth).join('/')
   if (!cut.has(name)) cut.set(name, [])
   cut.get(name).push(i)
  }
  if (cut.size > most) break
  best = cut
 }
 return [...best]
}
function firstAt(drawn, line) {
 let [low, high] = [0, drawn.length]
 while (low < high) {
  const middle = (low + high) >> 1
  if (drawn[middle].line < line) low = middle + 1
  else high = middle
 }
 return low
}
export class Plan {
 constructor(atlas, components, cols, rows, foot = 0) {
  this.foot = foot
  this.atlas = atlas
  this.cols = cols
  this.rows = rows
  this.masks = new Uint8Array(cols * rows)
  this.strokes = []
  this.bars = []
  this.places = []
  this.regions = []
  this.homes = []
  this.names = []
  this.borders = new Map()
  if (rows < 3) this.#strip()
  else this.#rooms(components)
 }
 dot(path, line) {
  const [plot, at] = this.atlas.locate(path, line) ?? [0, 1]
  const { x, y, w, h } = this.places[plot]
  const share = Math.min(Math.max(at - 1, 0) / Math.max(this.atlas.plots[plot].lines, 1), 0.999)
  return [x + (w >> 1), y + Math.floor(share * h)]
 }
 within([x, y]) {
  const edge = this.regions.length ? 1 : 0
  return [
   Math.min(Math.max(x >> 1, edge), this.cols - 1 - edge),
   Math.min(Math.max(y >> 2, edge), this.rows - 1 - edge),
  ]
 }
 cell(path, line) {
  return this.within(this.dot(path, line))
 }
 between(drawn, path, first, last) {
  const [plot, from] = this.atlas.locate(path, first) ?? []
  if (plot === undefined || from === undefined) return []
  const [start, end] = [firstAt(drawn[plot], from), firstAt(drawn[plot], from + last - first + 1)]
  const before = Math.max(start - 1, 0)
  return end > start ? drawn[plot].slice(start, end) : drawn[plot].slice(before, before + 1)
 }
 #strip() {
  const { plots } = this.atlas
  const scale = (2 * this.cols) / this.atlas.weight(plots.map((_, i) => i))
  let x = 0
  plots.forEach(({ lines }, i) => {
   const w = this.atlas.weight([i]) * scale
   const left = Math.min(Math.floor(x), 2 * this.cols - 1)
   const tall = Math.min(1 + Math.floor(Math.log2(1 + lines / 40)), 4 * this.rows)
   this.places[i] = { x: left, y: 4 * this.rows - tall, w: Math.max(Math.floor(x + w) - left, 1), h: tall }
   this.#fill(i, row => [0, this.places[i].w, 1 + Math.floor((row * lines) / tall)])
   x += w
  })
 }
 #rooms(components) {
  const { atlas, cols, rows } = this
  const groups = groupsOf(atlas, components, Math.max(Math.floor((cols * rows) / CELLS_PER_REGION), 1))
  const floor = { x: 0, y: 0, w: 2 * (cols - 1), h: 4 * (rows - 1) }
  const joints = new Uint8Array(cols * rows)
  const weights = groups.map(group => group.weight)
  squarify(weights, floor).forEach((at, n) => {
   const [x, y] = [Math.round(at.x / 2), Math.round(at.y / 4)]
   const box = { x, y, w: Math.round((at.x + at.w) / 2) - x + 1, h: Math.round((at.y + at.h) / 4) - y + 1 }
   groups[n].name ||= components.length ? 'other' : ''
   this.regions.push({ group: groups[n], box })
   this.#outline(box, joints)
   const inner = {
    x: 2 * (x + 1) + 1,
    y: 4 * (y + 1),
    w: Math.max(2 * (box.w - 2) - 1, 0),
    h: Math.max(4 * (box.h - 2) - this.foot, 0),
   }
   for (const [plot, tile] of atlas.layout(groups[n].plots, inner)) {
    this.homes[plot] = box
    this.#draw(plot, tile)
   }
  })
  for (const [cell, arms] of joints.entries()) if (arms) this.borders.set(cell, LINES[arms])
 }
 #outline(box, joints) {
  const [right, bottom] = [box.x + box.w - 1, box.y + box.h - 1]
  for (const y of [box.y, bottom]) {
   for (let x = box.x; x < right; x++) {
    joints[y * this.cols + x] |= RIGHT
    joints[y * this.cols + x + 1] |= LEFT
   }
  }
  for (const x of [box.x, right]) {
   for (let y = box.y; y < bottom; y++) {
    joints[y * this.cols + x] |= DOWN
    joints[(y + 1) * this.cols + x] |= UP
   }
  }
 }
 #draw(i, tile) {
  const { path, lines, outline } = this.atlas.plots[i]
  const [x, top] = [Math.round(tile.x), Math.round(tile.y)]
  const gap = (size) => (size > 2 ? size - 1 : size)
  const [wide, high] = [gap(Math.round(tile.x + tile.w) - x), gap(Math.round(tile.y + tile.h) - top)]
  const named = Math.min(wide, high) >= DOTS_FOR_A_NAME
  const [w, y] = named ? [wide - 2, 4 * ((top + 6) >> 2)] : [wide, top]
  if (named) {
   const [text, left] = [clean(path.split('/').at(-1)), (x + 1) >> 1]
   this.names.push({ plot: i, text, x: left, y: y / 4 - 1, w: ((x + wide) >> 1) - left })
  }
  const room = high - (y - top)
  const h = Math.min(Math.floor(room / lines), WIDEST_PITCH) * lines || room
  this.places[i] = { x, y, w, h }
  const grain = (row) => (this.atlas.folded ? 2 : row % 2 ? 4 : w + 1)
  if (!outline) return this.#fill(i, row => [row % 2, w, 1 + Math.floor((row * lines) / h), grain(row)])
  const count = outline.length / 2
  const lengths = outline.filter((_, n) => n % 2 === 1).sort()
  const scale = w / Math.min(Math.max(lengths[Math.floor(count * 0.8)], SHORTEST_LINE), LONGEST_LINE)
  this.#fill(i, row => {
   const [first, after] = [Math.floor((row * count) / h), Math.floor(((row + 1) * count) / h)]
   if (h >= 2 * count && after > first) return [0, 0, 0]
   let at = first
   for (let n = first + 1; n < Math.min(after, first + 3); n++) if (outline[2 * n + 1] > outline[2 * at + 1]) at = n
   const start = Math.max(Math.min(Math.floor(outline[2 * at] * scale), w - 1), 0)
   const end = outline[2 * at + 1] && Math.min(Math.max(Math.round(outline[2 * at + 1] * scale), start + 1), w)
   return [start, end, 1 + Math.floor((first * lines) / count)]
  })
 }
 #fill(i, span) {
  const { x, y, h } = this.places[i]
  this.strokes[i] = []
  this.bars[i] = []
  for (let row = 0; row < h; row++) {
   const [start, end, line, step = 1] = span(row)
   const barred = end > start && (step !== 2 || row % 2 === 0)
   if (barred) this.bars[i].push({ line, x: x + start, y: y + row, w: step > 2 ? 1 : end - start })
   for (let dot = x + start; dot < x + end; dot += step) {
    const cell = ((y + row) >> 2) * this.cols + (dot >> 1)
    this.masks[cell] |= DOT[(y + row) & 3][dot & 1]
    const last = this.strokes[i].at(-1)
    if (last?.cell === cell && last.line === line) last.dots++
    else this.strokes[i].push({ line, cell, dots: 1 })
   }
  }
 }
}
