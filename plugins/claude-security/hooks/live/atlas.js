const MAX_PLOTS = 1600
const MAX_ROWS = 160
const PATH_CHARS = 1024
export const LAST_SLASHES = /(?<!\/)\/+$/
export const BYTES_PER_LINE = 40
const AREA_EXPONENT = 0.7
const plotOf = ([path, bytes]) => ({ path, bytes, lines: Math.ceil(bytes / BYTES_PER_LINE) })
export class Atlas {
 #sizes
 constructor(files) {
  this.#sizes = new Map(files)
  const unique = [...this.#sizes]
  this.folded = unique.length > MAX_PLOTS
  this.plots = (this.folded ? folders(unique) : unique).map(plotOf)
  this.index = new Map(this.plots.map((plot, i) => [plot.path, i]))
  this.grows = false
  this.rev = 0
 }
 add(path, bytes) {
  const plot = plotOf([path, bytes])
  this.#sizes.set(path, bytes)
  this.index.set(path, this.plots.push(plot) - 1)
  this.grows = this.plots.length < MAX_PLOTS
  this.rev++
  return plot
 }
 find(path) {
  for (let end = path.length; end > 0; end = path.lastIndexOf('/', Math.min(end - 1, PATH_CHARS))) {
   const found = this.index.get(path.slice(0, end))
   if (found !== undefined) return found
  }
  return undefined
 }
 under(path) {
  const stem = path.split('*')[0].replace(LAST_SLASHES, '')
  const exact = this.index.get(stem)
  if (exact !== undefined) return [exact]
  const prefix = stem + '/'
  const below = this.plots.flatMap((plot, i) => (!stem || plot.path.startsWith(prefix) ? [i] : []))
  const holder = this.find(stem)
  return below.length || holder === undefined ? below : [holder]
 }
 matching(path) {
  const [start] = path.split('*')
  if (start === path || start.endsWith('/')) return this.under(path)
  const found = this.plots.flatMap((plot, i) => (plot.path.startsWith(start) ? [i] : []))
  return found.length ? found : this.under(path)
 }
 locate(path, line) {
  const plot = this.find(path)
  if (plot === undefined) return undefined
  const { lines } = this.plots[plot]
  if (this.plots[plot].path === path) return [plot, Math.min(line, lines)]
  const hash = [...path].reduce((sum, ch) => (sum * 31 + ch.charCodeAt(0)) >>> 0, 7)
  return [plot, (hash % Math.max(lines, 1)) + line]
 }
 linesOf(path) {
  const bytes = this.#sizes.get(path)
  if (bytes === undefined) return 0
  return Math.max(this.plots[this.index.get(path) ?? -1]?.lines ?? Math.ceil(bytes / BYTES_PER_LINE), 1)
 }
 trace(plot, text) {
  const lines = text.replace(/\n$/, '').split('\n')
  const rows = Math.min(lines.length, MAX_ROWS)
  plot.lines = lines.length
  plot.outline = new Uint8Array(2 * rows)
  for (let row = 0; row < rows; row++) {
   const line = lines[Math.floor((row * lines.length) / rows)].replaceAll('\t', '    ').trimEnd()
   plot.outline.set([Math.min(line.length - line.trimStart().length, 255), Math.min(line.length, 255)], 2 * row)
  }
  this.rev++
 }
 weight(plots) {
  return plots.reduce((sum, i) => sum + Math.max(this.plots[i].bytes / BYTES_PER_LINE, 4) ** AREA_EXPONENT, 0)
 }
 layout(plots, box) {
  const root = { weight: 0 }
  for (const i of plots) {
   const weight = this.weight([i])
   let node = root
   for (const name of (this.plots[i].path + '\0').split('/')) {
    node.children ??= new Map()
    const next = node.children.get(name) ?? { weight: 0 }
    node.children.set(name, next)
    node = next
    node.weight += weight
   }
   node.plot = i
  }
  const tiles = new Map()
  const place = (node, at) => {
   if (node.plot !== undefined) {
    tiles.set(node.plot, at)
    return
   }
   const children = [...(node.children?.values() ?? [])].sort((a, b) => b.weight - a.weight)
   squarify(
    children.map(child => child.weight),
    at,
   ).forEach((part, n) => place(children[n], part))
  }
  place(root, box)
  return tiles
 }
}
function folders(files) {
 let best = new Map()
 for (let depth = 1; depth < 12; depth++) {
  const cut = new Map()
  for (const [path, bytes] of files) {
   const name = path.split('/', depth).join('/')
   cut.set(name, (cut.get(name) ?? 0) + bytes)
  }
  if (best.size && cut.size > MAX_PLOTS) break
  best = cut
 }
 return [...best].slice(0, MAX_PLOTS)
}
export function squarify(weights, box) {
 const total = weights.reduce((sum, weight) => sum + weight, 0)
 const areas = weights.map(weight => (total ? (weight * box.w * box.h) / total : 0))
 const out = []
 let { x, y, w, h } = box
 for (let start = 0, end = 1; start < areas.length; start = end++) {
  const side = Math.min(w, h)
  const worst = (sum, least) =>
   sum && side && least
    ? Math.max((side * side * areas[start]) / (sum * sum), (sum * sum) / (side * side * least))
    : 0
  let sum = areas[start]
  while (end < areas.length && worst(sum + areas[end], areas[end]) <= worst(sum, areas[end - 1])) sum += areas[end++]
  const depth = side ? sum / side : 0
  let offset = 0
  for (const area of areas.slice(start, end)) {
   const length = depth ? area / depth : 0
   out.push(w >= h ? { x, y: y + offset, w: depth, h: length } : { x: x + offset, y, w: length, h: depth })
   offset += length
  }
  if (w >= h) [x, w] = [x + depth, w - depth]
  else [y, h] = [y + depth, h - depth]
 }
 return out
}
