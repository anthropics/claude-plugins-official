/**
 * Packing for the terminal's `Raster` element: a grid of cells, each a glyph
 * with a foreground and a background colour, as the base64 the element takes
 * (`columns * rows` little-endian u32 triplets `[codePoint, fg, bg]`).
 */

export type Cell = { glyph: string; fg: number; bg: number }

/** The terminal's own default colour, as `RasterProps` spells it. */
export const DEFAULT_COLOR = 0x01000000

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

/** Standard padded base64 of bytes, with no dependence on `btoa` or `Uint8Array.toBase64`. */
export function base64Of(bytes: Uint8Array): string {
  let out = ''

  for (let index = 0; index < bytes.length; index += 3) {
    const a = bytes[index] ?? 0
    const b = bytes[index + 1] ?? 0
    const c = bytes[index + 2] ?? 0
    const has2 = index + 1 < bytes.length
    const has3 = index + 2 < bytes.length

    out +=
      (B64[a >> 2] ?? '') +
      (B64[((a & 3) << 4) | (b >> 4)] ?? '') +
      (has2 ? (B64[((b & 15) << 2) | (c >> 6)] ?? '') : '=') +
      (has3 ? (B64[c & 63] ?? '') : '=')
  }

  return out
}

/** A printable width-1 BMP code point for `glyph`, or a space when it is not one. */
export function codePointOf(glyph: string): number {
  const point = glyph.codePointAt(0) ?? 0x20

  const isPrintable =
    point >= 0x20 &&
    point <= 0xffff &&
    point !== 0x7f &&
    !(point >= 0x80 && point < 0xa0) &&
    !(point >= 0xd800 && point <= 0xdfff) &&
    // East Asian wide and fullwidth ranges draw two cells.
    !(point >= 0x1100 && point <= 0x115f) &&
    !(point >= 0x2e80 && point <= 0xa4cf) &&
    !(point >= 0xac00 && point <= 0xd7a3) &&
    !(point >= 0xf900 && point <= 0xfaff) &&
    !(point >= 0xfe30 && point <= 0xfe6f) &&
    !(point >= 0xff00 && point <= 0xff60) &&
    !(point >= 0xffe0 && point <= 0xffe6)

  return isPrintable ? point : 0x20
}

/** Packs row-major `cells` (`columns * rows` of them) for a `Raster`'s `cells` prop. */
export function packCells(cells: readonly Cell[]): string {
  const bytes = new Uint8Array(cells.length * 12)
  const view = new DataView(bytes.buffer)

  cells.forEach((cell, index) => {
    view.setUint32(index * 12, codePointOf(cell.glyph), true)
    view.setUint32(index * 12 + 4, cell.fg >>> 0, true)
    view.setUint32(index * 12 + 8, cell.bg >>> 0, true)
  })

  return base64Of(bytes)
}

/** `0x00RRGGBB` from three 0-255 channels. */
export const rgb = (r: number, g: number, b: number): number =>
  ((Math.max(0, Math.min(255, Math.round(r))) << 16) |
    (Math.max(0, Math.min(255, Math.round(g))) << 8) |
    Math.max(0, Math.min(255, Math.round(b)))) >>>
  0

/** `a` moved `t` of the way (0 to 1) toward `b`, channel by channel. */
export function mix(a: number, b: number, t: number): number {
  const k = Math.max(0, Math.min(1, t))
  const ch = (c: number, shift: number) => (c >> shift) & 0xff

  return rgb(
    ch(a, 16) + (ch(b, 16) - ch(a, 16)) * k,
    ch(a, 8) + (ch(b, 8) - ch(a, 8)) * k,
    ch(a, 0) + (ch(b, 0) - ch(a, 0)) * k,
  )
}

/** Perceived brightness, 0 to 255. */
export const luma = (color: number): number =>
  0.299 * ((color >> 16) & 0xff) + 0.587 * ((color >> 8) & 0xff) + 0.114 * (color & 0xff)
