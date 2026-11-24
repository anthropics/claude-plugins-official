import { DOT } from './plan.js'
const BRAILLE = 0x2800
const SPACE = 0x20
export class Canvas {
 #over = new Set()
 constructor(cols, rows, paper) {
  this.cols = cols
  this.rows = rows
  this.paper = paper
  this.cells = new Uint32Array(3 * cols * rows)
 }
 begin(masks, ink) {
  this.#over.clear()
  masks.forEach((mask, cell) => {
   this.cells[3 * cell] = mask ? BRAILLE + mask : SPACE
   this.cells[3 * cell + 1] = ink(cell)
   this.cells[3 * cell + 2] = this.paper
  })
 }
 dot(x, y, ink) {
  if (x < 0 || x >= 2 * this.cols || y < 0 || y >= 4 * this.rows) return
  const cell = (y >> 2) * this.cols + (x >> 1)
  const held = this.cells[3 * cell]
  if (held !== SPACE && held >> 8 !== BRAILLE >> 8) return
  this.cells[3 * cell] = (this.#over.has(cell) ? held : BRAILLE) | DOT[y & 3][x & 1]
  this.cells[3 * cell + 1] = ink
  this.#over.add(cell)
 }
 put(x, y, parts) {
  for (const [text, ink, paper = this.paper] of parts) {
   for (const ch of text) {
    if (x >= 0 && x < this.cols && y >= 0 && y < this.rows) {
     this.cells.set([ch.charCodeAt(0), ink, paper], 3 * (y * this.cols + x))
     this.#over.delete(y * this.cols + x)
    }
    x++
   }
  }
 }
}
export function packed(cells) {
 const bytes = new Uint8Array(cells.buffer)
 let text = ''
 for (let at = 0; at < bytes.length; at += 4096) text += String.fromCharCode(...bytes.subarray(at, at + 4096))
 return btoa(text)
}
