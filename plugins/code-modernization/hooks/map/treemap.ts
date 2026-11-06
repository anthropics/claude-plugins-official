/**
 * A squarified treemap over a grid of terminal cells, two levels deep:
 * groups (domains) first, then each group's items (modules) inside its
 * rectangle. Pure: sizes in, integer cell rectangles out.
 *
 * A terminal cell is about twice as tall as it is wide, so the layout works
 * in a space where each row counts double and rounds back to whole cells.
 */

export type Rect = { x: number; y: number; w: number; h: number }

export type Sized<T> = { item: T; size: number }

export type Placed<T> = { item: T; rect: Rect }

/** How much taller than wide one cell is; rows are weighted by it when judging squareness. */
const CELL_ASPECT = 2

const worst = (row: number[], side: number, scale: number): number => {
  const sum = row.reduce((a, b) => a + b, 0)

  if (sum === 0 || side === 0) {
    return Infinity
  }

  const max = Math.max(...row)
  const min = Math.min(...row)
  const s2 = sum * sum
  const side2 = side * side * scale

  return Math.max((side2 * max) / s2, s2 / (side2 * min))
}

/**
 * Squarified layout of `sizes` (already scaled so they sum to the area of
 * `rect`) into fractional rectangles, in the order given.
 */
function squarify(sizes: number[], rect: Rect): Rect[] {
  const out: Rect[] = []
  let { x, y, w, h } = rect
  let index = 0

  while (index < sizes.length) {
    // Lay rows along the visually shorter side.
    const isWide = w >= h * CELL_ASPECT
    const side = isWide ? h : w
    const scale = isWide ? CELL_ASPECT : 1 / CELL_ASPECT
    const row: number[] = []

    while (index < sizes.length) {
      const next = sizes[index] ?? 0
      const grown = [...row, next]

      if (row.length > 0 && worst(grown, side, scale) > worst(row, side, scale)) {
        break
      }

      row.push(next)
      index += 1
    }

    const sum = row.reduce((a, b) => a + b, 0)
    const thick = side > 0 ? sum / side : 0
    let offset = 0

    for (const size of row) {
      const length = thick > 0 ? size / thick : 0

      out.push(
        isWide
          ? { x, y: y + offset, w: thick, h: length }
          : { x: x + offset, y, w: length, h: thick },
      )

      offset += length
    }

    if (isWide) {
      x += thick
      w -= thick
    } else {
      y += thick
      h -= thick
    }

    if (w <= 0 || h <= 0) {
      // Out of room: whatever is left collapses onto the last edge.
      while (index < sizes.length) {
        out.push({ x: rect.x + rect.w, y: rect.y + rect.h, w: 0, h: 0 })
        index += 1
      }
    }
  }

  return out
}

/** Rounds fractional rectangles to whole cells without gaps or overlaps on shared edges. */
function snap(rects: Rect[], bounds: Rect): Rect[] {
  const clampX = (v: number) => Math.min(bounds.x + bounds.w, Math.max(bounds.x, Math.round(v)))
  const clampY = (v: number) => Math.min(bounds.y + bounds.h, Math.max(bounds.y, Math.round(v)))

  return rects.map(rect => {
    const x0 = clampX(rect.x)
    const y0 = clampY(rect.y)
    const x1 = clampX(rect.x + rect.w)
    const y1 = clampY(rect.y + rect.h)

    return { x: x0, y: y0, w: Math.max(0, x1 - x0), h: Math.max(0, y1 - y0) }
  })
}

/** Lays `entries` out in `rect`, largest first, each given at least `floor` of the mean size. */
export function layout<T>(entries: Sized<T>[], rect: Rect, floor = 0.35): Placed<T>[] {
  if (entries.length === 0 || rect.w <= 0 || rect.h <= 0) {
    return []
  }

  const positive = entries.map(entry => ({ ...entry, size: Math.max(0, entry.size) }))
  const mean = positive.reduce((sum, entry) => sum + entry.size, 0) / positive.length || 1

  // A tiny item next to a huge one would round to zero cells: lift it to a floor.
  const lifted = positive
    .map(entry => ({ ...entry, size: Math.max(entry.size, mean * floor) }))
    .sort((a, b) => b.size - a.size)

  const total = lifted.reduce((sum, entry) => sum + entry.size, 0)
  const area = rect.w * rect.h
  const scaled = lifted.map(entry => (entry.size / total) * area)
  const snapped = snap(squarify(scaled, rect), rect)

  return lifted.map((entry, index) => ({
    item: entry.item,
    rect: snapped[index] ?? { x: rect.x, y: rect.y, w: 0, h: 0 },
  }))
}

export type Group<T> = { name: string; items: Sized<T>[] }

export type PlacedGroup<T> = { name: string; rect: Rect; items: Placed<T>[] }

/** Two-level layout: groups by their items' total size, then items within each group. */
export function layoutGroups<T>(groups: Group<T>[], rect: Rect): PlacedGroup<T>[] {
  const sized = groups
    .filter(group => group.items.length > 0)
    .map(group => ({
      item: group,
      size: group.items.reduce((sum, entry) => sum + Math.max(0, entry.size), 0),
    }))

  return layout(sized, rect, 0.2).map(placed => ({
    name: placed.item.name,
    rect: placed.rect,
    items: layout(placed.item.items, placed.rect),
  }))
}
