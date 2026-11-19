// Koi Pond: a pond seen from above, with real travelling ripples, koi that each steer themselves, and feeding.
import {
  abs, atan, buffer, clamp, composer, cos, dot, dt, exp, first, floor, fract, frame, int, length, max, min, mix,
  mod, normalize, PI, picture, pointers, pow, px, res, scene, shader, shapes, sin, size, smoothstep, sqrt, step,
  time, unsigned, values, vec2, vec3, vec4,
} from 'claude-code/shader'
import type { Buffer } from 'claude-code/shader'

// One layout unit: a point in a 1512x945 window, smaller in a smaller one, so the pond keeps its proportions.
const unitOf = () => sqrt(size.x * size.y) / 1195

// Integer mixing of a lattice point and a seed: three odd multipliers folded in, then two rounds of
// xor-shift and multiply, and a last xor-shift. The constants and shifts give an even, unstreaked grain.
const mixI = (x: number, y: number, k: number) => {
  let h = int(int(x) * 0x43e2d1dd + int(y) * 0x6d2a9e3b + int(k) * 0x2c7f0a8d)
  h = int(h ^ (h >>> 14))
  h = int(h * 0x4e9d3a67)
  h = int(h ^ (h >>> 11))
  h = int(h * 0x35a6c2d9)
  h = int(h ^ (h >>> 17))
  return h
}
// Four numbers from 0 to 1 out of one mixed int, a byte each.
const four = (h: int): vec4 => vec4(vec4(unsigned(h & 255), unsigned((h >>> 8) & 255), unsigned((h >>> 16) & 255), unsigned(h >>> 24)) / 256)
const one = (x: number, y: number, k: number): number => unsigned(mixI(x, y, k)) / 4294967296

// Smooth lattice noise, 0 to 1.
const lattice = (at: vec2, seed: number): number => {
  const corner = vec2(floor(at))
  const ease = vec2(smoothstep(0, 1, vec2(at - corner)))
  const low = mix(one(corner.x, corner.y, seed), one(corner.x + 1, corner.y, seed), ease.x)
  const high = mix(one(corner.x, corner.y + 1, seed), one(corner.x + 1, corner.y + 1, seed), ease.x)
  return mix(low, high, ease.y)
}
// Three sizes of it laid over each other, for mottling.
const layered = (at: vec2, seed: number): number => lattice(at, seed) * 0.5 + lattice(vec2(at * 2.03 + 17), seed + 1) * 0.3 + lattice(vec2(at * 4.1 + 31), seed + 2) * 0.2

const SUN = vec2(-0.55, 0.83)

// How far a point is from the stroke that runs from a to b: its offset across the stroke, and how far it
// overshoots either end along it.
const strokeAway = (pt: vec2, a: vec2, b: vec2): number => {
  const run = vec2(b - a)
  const len = length(run)
  const along = vec2(run / max(len, 0.001))
  const rel = vec2(pt - a)
  const t = dot(rel, along)
  const across = rel.x * along.y - rel.y * along.x
  const past = max(max(-t, t - len), 0)
  return sqrt(across * across + past * past)
}

// Where the bottom rises into shallow shelves: 1 on the shelves beside the text, 0 in the deep middle.
const shelfOf = (uv: vec2, wob: number): number => {
  const l = 1 - smoothstep(0.1, 0.36, uv.x + wob - 0.05 * uv.y)
  const r = 1 - smoothstep(0.08, 0.34, 1 - uv.x + wob - 0.08 * (1 - uv.y))
  return max(l, r)
}

// Light and dark reach the shader only through the Svg under this picture, a still drawing of the same pond:
// its middle is plain water in the mode's own tone.
const modeBuf = buffer({ size: [1, 1], once: true }, p => {
  const c = scene.sample(vec2(0.5, 0.5))
  const lum = dot(c.rgb, vec3(0.3, 0.6, 0.1))
  return vec4(smoothstep(0.15, 0.23, lum), 0, 0, 1)
})

// The bottom, painted once: silt, three sizes of stone, sunken maple leaves. Alpha holds the depth.
const STONE = [vec3(0.46, 0.46, 0.43), vec3(0.5, 0.44, 0.33), vec3(0.43, 0.32, 0.24), vec3(0.34, 0.38, 0.4), vec3(0.58, 0.55, 0.46), vec3(0.27, 0.27, 0.26)]
const stoneLayer = (col: vec3, q: vec2, cell: number, seed: number, u: number, thin: number): vec3 => {
  const g = vec2(q / cell)
  const gi = floor(g)
  let best = 4
  let bd = vec2(1, 0)
  let bp = vec4(0)
  for (let j = -1; j <= 1; j++) {
    for (let i = -1; i <= 1; i++) {
      const cx = gi.x + i
      const cy = gi.y + j
      const r = four(mixI(cx, cy, seed))
      const c = vec2(cx + 0.25 + 0.5 * r.x, cy + 0.25 + 0.5 * r.y)
      const dens = max(shelfOf(vec2(c * cell * u / size), 0.03 * sin(c.y * 1.7)), 0.13) * thin
      const d = vec2(g - c)
      const a = r.z * 3.1
      const ca = cos(a)
      const sa = sin(a)
      const e = vec2(ca * d.x + sa * d.y, (ca * d.y - sa * d.x) * (1.1 + 0.5 * r.w))
      const rad = 0.2 + 0.3 * r.w
      const gone = step(dens, fract(r.x * 13.7 + r.y * 5.3))
      const t = length(e) / rad + gone * 9
      if (t < best) {
        best = t
        bd = d
        bp = r
      }
    }
  }
  // No stone is an ellipse: its outline is pushed in and out, and its foot lies under the silt.
  const grain = lattice(vec2(q / (cell * 0.06)), seed + 5)
  const fuzz = lattice(vec2(q / (cell * 0.3)), seed + 7)
  const rim = best + (fuzz - 0.5) * 0.34
  const inside = smoothstep(1, 0.8, rim)
  const dn = normalize(bd)
  const lam = dot(dn, SUN) * min(best, 1.6)
  const dome = sqrt(max(0, 1 - best * best))
  const idx = floor(bp.w * 5.99)
  const pal = idx < 1 ? STONE[0]! : idx < 2 ? STONE[1]! : idx < 3 ? STONE[2]! : idx < 4 ? STONE[3]! : idx < 5 ? STONE[4]! : STONE[5]!
  let sc = vec3(pal * (0.84 + 0.1 * dome + 0.15 * lam) * (0.86 + 0.28 * grain))
  // Green fuzz furs the tops; silt buries the edges.
  sc = mix(sc, vec3(vec3(0.29, 0.35, 0.19) * (0.75 + 0.5 * grain)), smoothstep(0.42, 0.8, fuzz) * 0.6)
  sc = mix(sc, col, smoothstep(0.45, 1, rim) * 0.7)
  const cast = smoothstep(1.5, 1, best) * (1 - inside) * clamp(0.5 - 0.6 * lam, 0, 1)
  return vec3(mix(col * (1 - 0.34 * cast), sc, inside))
}
const sunkLeaf = (col: vec3, q: vec2, seed: number): vec3 => {
  const cell = 190
  const g = vec2(q / cell)
  const gi = floor(g)
  let out = col
  for (let j = -1; j <= 0; j++) {
    for (let i = -1; i <= 0; i++) {
      const cx = gi.x + i + step(0.5, g.x - gi.x)
      const cy = gi.y + j + step(0.5, g.y - gi.y)
      const r = four(mixI(cx, cy, seed))
      const c = vec2(cx + 0.2 + 0.6 * r.x, cy + 0.2 + 0.6 * r.y)
      const d = vec2((g - c) * cell)
      const R = 15 + 12 * r.z
      const rr = length(d)
      const a = atan(d.y, d.x) - r.w * 6.3
      const lobe = abs(cos(a * 2.5))
      const edge = R * (0.3 + 0.7 * pow(lobe, 1.1)) * (0.62 + 0.38 * cos(a))
      const m = smoothstep(edge, edge - 1.5, rr) * step(fract(r.z * 9.1 + r.w * 3.3), 0.62)
      const vein = pow(lobe, 20) * smoothstep(0.1, 0.5, rr / R)
      const tone = mix(vec3(0.36, 0.23, 0.13), vec3(0.5, 0.36, 0.15), r.x)
      const lc = vec3(tone * (0.85 + 0.3 * lattice(vec2(d / 5 + r.w * 40), 19)) + vein * 0.07)
      const sh = smoothstep(edge + 4, edge - 1, length(vec2(d - vec2(1.5, -2)))) * 0.22
      out = vec3(mix(out * (1 - sh * (1 - m)), lc, m * 0.9))
    }
  }
  return out
}
const bed = buffer({ scale: 0.7, once: true, filter: 'mipmap' }, p => {
  const u = unitOf()
  const q = vec2(p.point / u)
  const n0 = layered(vec2(q / 260), 11)
  const sh = shelfOf(p.uv, (n0 - 0.5) * 0.14)
  const n1 = layered(vec2(q / 64), 23)
  const n2 = lattice(vec2(q / 7), 31)
  let col = mix(vec3(0.3, 0.29, 0.21), vec3(0.41, 0.37, 0.26), n1)
  col = mix(col, vec3(0.24, 0.29, 0.21), smoothstep(0.45, 0.8, n0) * 0.55)
  col = vec3(col * (0.9 + 0.2 * n2) * (0.84 + 0.32 * n0))
  // Grit: pale and dark specks too small to be stones.
  const grit = one(floor(q.x / 2.6), floor(q.y / 2.6), 37)
  col = vec3(col * (1 + 0.2 * step(0.9, grit) - 0.2 * step(grit, 0.08)))
  col = stoneLayer(col, q, 22, 3, u, 1.25)
  col = stoneLayer(col, q, 58, 5, u, 0.8)
  col = sunkLeaf(col, q, 7)
  col = stoneLayer(col, q, 150, 9, u, 0.42)
  // A dusting of silt settles over everything and ties the stones to the bottom.
  col = mix(col, vec3(0.36, 0.34, 0.25), 0.12 + 0.2 * smoothstep(0.4, 0.9, n1) * (1 - sh))
  return vec4(col, clamp(0.76 - 0.56 * sh + 0.16 * (n0 - 0.5), 0, 1))
})

// What lies on or over the surface, painted once, premultiplied: bank stones, pads, two lilies, reeds,
// duckweed, a maple bough. The picture lights it and drops its shadow into the water.
const over = (acc: vec4, rgb: vec3, a: number): vec4 => vec4(acc.rgb * (1 - a) + rgb * a, acc.a * (1 - a) + a)
const dim = (acc: vec4, k: number): vec4 => vec4(acc.rgb * (1 - k), acc.a)

const pad = (acc: vec4, pt: vec2, c: vec2, r: number, notch: number, beads: number, u: number): vec4 => {
  // Each pad has a character of its own, 0 to 1, which sets its squeeze, its green, its age and its notch.
  const k = one(r, notch * 10, 7)
  // No pad is a circle: each is squeezed a little one way or the other.
  const d0 = vec2((pt - c) / u)
  const d = vec2(d0.x / (1 - 0.2 * k), d0.y / (0.8 + 0.2 * k))
  const rr = length(d)
  let out = acc
  if (rr < r + 9) {
    const ang = atan(d.y, d.x)
    const da = abs(mod(ang - notch + PI, 2 * PI) - PI)
    const rough = lattice(vec2(d / 9 + k * 23), 47)
    const edge = r * (1 + 0.06 * sin(ang * 3 + k * 9) + 0.03 * sin(ang * 5 + k * 4) + 0.07 * (rough - 0.5))
    const slit = 1 - (1 - smoothstep(0.04 + 0.1 * k, 0.1 + 0.2 * k, da - 0.6 / (rr + 4))) * smoothstep(0.05 * r, 0.12 * r, rr)
    // Something has had a bite out of the rim.
    const off = abs(mod(ang - notch - 2.3 - k * 4 + PI, 2 * PI) - PI)
    const nib = smoothstep(0.11 * r, 0.11 * r + 2.2, length(vec2(rr - 1.03 * r, off * r)))
    const m = smoothstep(edge, edge - 2.2, rr) * slit * nib
    const rel = rr / r
    const vv = abs(sin((ang - notch) * 8))
    const vw = 7 / (rr + 6)
    const vein = (1 - smoothstep(vw * 0.5, vw * 1.5, vv)) * smoothstep(1, 0.78, rel) * smoothstep(0.04, 0.2, rel)
    const n = lattice(vec2(d / 22 + k * 31), 41)
    const n2 = lattice(vec2(d / 5 + k * 17), 43)
    const dn = normalize(d)
    let g = mix(vec3(0.16, 0.31, 0.14), vec3(0.31, 0.43, 0.17), k)
    g = vec3(g * (0.78 + 0.44 * n) * (1.08 - 0.2 * smoothstep(0.55, 1, rel)))
    // An older leaf yellows and browns from the rim inward, and never evenly.
    const old = smoothstep(0.55, 1.05, rel + 0.5 * (n - 0.5) + 0.35 * (k - 0.5))
    g = mix(g, vec3(0.47, 0.45, 0.17), old * 0.55)
    g = mix(g, vec3(0.43, 0.53, 0.25), vein * 0.26)
    g = mix(g, vec3(0.36, 0.27, 0.13), smoothstep(0.72, 0.86, n2) * 0.6)
    g = mix(g, vec3(0.33, 0.22, 0.12), smoothstep(edge - 3.4, edge - 1, rr) * 0.3 * (0.4 + 1.2 * n))
    // The waxy top takes a broad soft shine from the sky on its sunward side.
    const shine = smoothstep(1.1, 0.1, length(vec2(d / r - SUN * 0.4))) * (0.5 + 0.5 * rough)
    g = vec3(g + vec3(0.13, 0.16, 0.15) * shine)
    g = vec3(g + 0.1 * smoothstep(edge - 3, edge - 1.2, rr) * max(0, dot(dn, SUN)))
    // Beads of water sit on some pads, one or two: a lens with a bright point and a dark foot.
    for (const s of [1, -1]) {
      if (beads >= 1.5 - 0.5 * s) {
        const o = vec2(cos(notch + 1.9 * s + k * 3) * 0.5 * r, sin(notch + 1.9 * s + k * 3) * 0.46 * r)
        const dd = length(vec2(d - o))
        const br = 2.6 + k * 1.6
        g = mix(g, vec3(g * 1.18 + 0.05), smoothstep(br, br - 0.8, dd))
        g = vec3(g * (1 - 0.35 * smoothstep(br + 0.9, br - 0.2, length(vec2(d - o - vec2(0.9, -1.2)))) * smoothstep(br - 0.9, br, dd)))
        g = vec3(g + 0.75 * smoothstep(1.1, 0.3, length(vec2(d - o - vec2(-0.9, 1)))))
      }
    }
    out = over(dim(out, smoothstep(edge + 6, edge - 1, length(vec2(d - vec2(2, -3)))) * 0.3 * (1 - m)), g, m)
  }
  return out
}

const lily = (acc: vec4, pt: vec2, c: vec2, R: number, rot: number, pink: number, u: number): vec4 => {
  const d = vec2((pt - c) / u)
  const rr = length(d) / R
  let out = acc
  if (rr < 1.3) {
    const ang = atan(d.y, d.x)
    out = dim(out, 0.4 * smoothstep(1.25, 0.7, length(vec2(d - vec2(3, -4.5))) / R))
    for (const k of [0, 1, 2, 3]) {
      const Rk = 1 - 0.23 * k
      const pa = ang + rot + k * 0.41
      const cs = abs(cos(pa * (4 - 0.5 * k)))
      const edge = Rk * (0.56 + 0.44 * pow(cs, 0.34))
      const m = smoothstep(edge, edge - 0.06, rr)
      const t = rr / edge
      const blush = mix(vec3(0.96, 0.62, 0.74), vec3(0.99, 0.96, 0.93), smoothstep(0.15, 0.8 - 0.5 * pink, t))
      const petal = vec3(blush * (0.8 + 0.2 * cs) * (0.84 + 0.16 * t) * (1 - 0.2 * smoothstep(0.84, 1, t)))
      out = over(dim(out, 0.25 * smoothstep(edge + 0.12, edge, rr) * (1 - m)), petal, m)
    }
    const heart = smoothstep(0.26, 0.19, rr)
    const dots = 0.8 + 0.2 * sin(ang * 14) * smoothstep(0.05, 0.15, rr)
    out = over(out, vec3(vec3(0.97, 0.72, 0.15) * dots), heart)
  }
  return out
}

const blade = (acc: vec4, pt: vec2, b: vec2, tip: vec2, bend: number, w: number, k: number): vec4 => {
  const ax = vec2(tip - b)
  const len = length(ax)
  const dir = vec2(ax / len)
  const r = vec2(pt - b)
  const a = dot(r, dir) / len
  const cr = r.x * dir.y - r.y * dir.x
  let out = acc
  if (a > -0.02 && a < 1.02) {
    const off = bend * len * a * a
    const hw = w * pow(max(1 - a, 0), 0.6) * min(1, 0.35 + a * 6)
    const dd = abs(cr - off) - hw
    const m = smoothstep(1.6, -1.6, dd) * step(0, a) * step(a, 1)
    const mid = smoothstep(hw * 0.3, 0, abs(cr - off))
    const g0 = mix(vec3(0.2, 0.34, 0.13), vec3(0.45, 0.47, 0.18), a * a * (0.4 + 0.6 * k))
    const g = vec3(g0 * (0.84 + 0.26 * mid) * (0.88 + 0.24 * k) * (0.7 + 0.4 * a))
    out = over(dim(out, smoothstep(6, 0, abs(cr - off - 2.5) - hw) * 0.2 * (1 - m) * step(0, a) * step(a, 1)), g, m)
  }
  return out
}

const mapleLeaf = (acc: vec4, pt: vec2, c: vec2, R: number, rot: number, hue: number, u: number): vec4 => {
  const d = vec2((pt - c) / u)
  const rr = length(d)
  let out = acc
  if (rr < R * 1.25) {
    const a = atan(d.y, d.x) - rot
    const lobe = abs(cos(a * 2.5))
    const edge = R * (0.3 + 0.7 * pow(lobe, 0.8 + hue)) * (0.62 + 0.38 * cos(a)) * (1 + 0.05 * sin(a * 24)) * (1 - 0.16 * hue * sin(a + hue * 9))
    const m = smoothstep(edge, edge - 2.6, rr)
    const vein = pow(lobe, 26) * smoothstep(0.08, 0.4, rr / R)
    const warm = mix(mix(vec3(0.74, 0.15, 0.1), vec3(0.9, 0.4, 0.1), smoothstep(0, 0.5, hue)), vec3(0.93, 0.68, 0.18), smoothstep(0.5, 1, hue))
    const worn = vec3(mix(warm, vec3(0.45, 0.33, 0.2), 0.45) * (0.84 + 0.26 * sin(a)))
    const g = vec3(worn * (0.8 + 0.34 * lattice(vec2(d / 6 + rot * 7), 51)) * (1.06 - 0.26 * rr / R) * (1 + 0.3 * vein))
    out = over(dim(out, 0.28 * smoothstep(edge + 5, edge - 1, length(vec2(d - vec2(2, -3)))) * (1 - m)), g, m)
  }
  return out
}

const rock = (acc: vec4, pt: vec2, c: vec2, rx: number, ry: number, rot: number, k: number, u: number): vec4 => {
  const d0 = vec2((pt - c) / u)
  const ca = cos(rot)
  const sa = sin(rot)
  const e = vec2((ca * d0.x + sa * d0.y) / rx, (ca * d0.y - sa * d0.x) / ry)
  const t0 = length(e)
  let out = acc
  if (t0 < 1.3) {
    const n = layered(vec2(d0 / 38 + k * 13), 61)
    const t = t0 + (n - 0.5) * 0.24
    const m = smoothstep(1, 0.97, t)
    const dome = sqrt(max(0, 1 - t * t))
    const lam = dot(normalize(d0), SUN) * min(t, 1)
    const sp = lattice(vec2(d0 / 3.5), 63)
    let g = vec3(mix(vec3(0.34, 0.34, 0.33), vec3(0.43, 0.41, 0.37), k) * (0.62 + 0.3 * dome + 0.3 * lam) * (0.88 + 0.24 * sp))
    const moss = smoothstep(0.46, 0.7, layered(vec2(d0 / 26 + 5 + k * 7), 67)) * smoothstep(0.98, 0.5, t)
    g = mix(g, vec3(vec3(0.25, 0.36, 0.14) * (0.75 + 0.5 * sp)), moss * 0.85)
    g = mix(g, vec3(g * 0.5), smoothstep(0.84, 1, t))
    out = over(out, g, m)
  }
  return out
}

const top = buffer({ scale: 0.8, once: true, filter: 'mipmap' }, p => {
  const u = unitOf()
  const pt = p.point
  const q = vec2(pt / u)
  const at = (ax: number, ay: number, dx: number, dy: number): vec2 => vec2(ax * size.x + dx * u, ay * size.y + dy * u)
  let acc = vec4(0)

  // Duckweed: tiny leaves packed into ragged mats along the banks and against the pad clusters; each
  // frond is the nearest of a loose scatter and has a size and a green of its own, so no grid shows.
  const ragged = layered(vec2(q / 70), 73)
  const bank = smoothstep(0.09, 0.035, min(p.uv.x, 1 - p.uv.x) + 0.03 * sin(p.uv.y * 11))
  const byPads = max(smoothstep(215, 120, length(vec2(pt - at(0, 1, 170, -225))) / u), smoothstep(215, 120, length(vec2(pt - at(1, 0, -200, 235))) / u))
  const raft = smoothstep(0.46, 0.6, ragged) * max(bank, byPads * smoothstep(0.5, 0.62, ragged))
  const wq = vec2(q / 5)
  const wi = floor(wq)
  let nearest = 9
  let frond = vec4(0)
  for (let j = -1; j <= 1; j++) {
    for (let i = -1; i <= 1; i++) {
      const r = four(mixI(wi.x + i, wi.y + j, 71))
      const away = length(vec2(wq - wi - vec2(i, j) - 0.1 - 0.8 * r.xy)) / (0.24 + 0.34 * r.z)
      if (away < nearest) {
        nearest = away
        frond = r
      }
    }
  }
  const speck = smoothstep(1, 0.72, nearest) * step(fract(frond.w * 7.7 + frond.z * 3.1), raft)
  acc = over(acc, vec3(mix(vec3(0.24, 0.35, 0.14), vec3(0.4, 0.46, 0.2), frond.w) * (0.78 + 0.4 * frond.z)), speck)

  // Pollen and dust lie on the water in a thin scatter, thicker toward the banks.
  const fq = vec2(q / 15)
  const fc = floor(fq)
  const fr = four(mixI(fc.x, fc.y, 111))
  const dust = smoothstep(0.1 + 0.06 * fr.z, 0.04, length(vec2(fq - fc - 0.2 - 0.6 * fr.xy))) * step(fr.w, 0.015 + 0.3 * smoothstep(0.3, 0.95, shelfOf(p.uv, 0)))
  acc = over(acc, vec3(0.8, 0.78, 0.6), dust * 0.3)

  // Lily pads, upper left and lower right, and two strays.
  acc = pad(acc, pt, at(0, 1, 150, -175), 74, 0.6, 1, u)
  acc = pad(acc, pt, at(0, 1, 92, -318), 58, 2.4, 0, u)
  acc = pad(acc, pt, at(0, 1, 268, -118), 52, 4.1, 2, u)
  acc = pad(acc, pt, at(0, 1, 222, -272), 40, 5.4, 0, u)
  acc = lily(acc, pt, at(0, 1, 214, -196), 31, 0.3, 0.35, u)
  acc = pad(acc, pt, at(1, 0, -145, 172), 80, 3.6, 1, u)
  acc = pad(acc, pt, at(1, 0, -92, 330), 55, 5.9, 0, u)
  acc = pad(acc, pt, at(1, 0, -278, 128), 49, 0.9, 1, u)
  acc = pad(acc, pt, at(1, 0, -236, 262), 37, 2.2, 0, u)
  acc = lily(acc, pt, at(1, 0, -212, 200), 25, 1.1, 0.9, u)
  acc = pad(acc, pt, at(0, 0, 262, 196), 33, 1.9, 0, u)
  acc = pad(acc, pt, at(1, 1, -300, -96), 41, 3.1, 1, u)

  // Bank stones in two corners.
  acc = rock(acc, pt, at(0, 0, 196, -14), 92, 62, 0.3, 0.2, u)
  acc = rock(acc, pt, at(0, 0, 22, 52), 118, 96, -0.4, 0.8, u)
  acc = rock(acc, pt, at(1, 1, -212, 24), 84, 58, 0.2, 0.6, u)
  acc = rock(acc, pt, at(1, 1, -28, -36), 112, 92, 0.5, 0.1, u)

  // Reeds lean out from the lower left bank.
  acc = blade(acc, pt, at(0, 0, 62, 96), at(0, 0, 238, 318), 0.16, 5.5 * u, 0.2)
  acc = blade(acc, pt, at(0, 0, 38, 120), at(0, 0, 118, 402), -0.12, 6 * u, 0.7)
  acc = blade(acc, pt, at(0, 0, 96, 78), at(0, 0, 322, 226), 0.2, 5 * u, 0.5)
  acc = blade(acc, pt, at(0, 0, 20, 134), at(0, 0, 44, 372), 0.1, 5 * u, 0.9)
  acc = blade(acc, pt, at(0, 0, 118, 54), at(0, 0, 356, 132), -0.14, 4.6 * u, 0.35)
  acc = blade(acc, pt, at(0, 0, 74, 110), at(0, 0, 176, 352), 0.05, 4.4 * u, 1)
  acc = blade(acc, pt, at(0, 0, 140, 40), at(0, 0, 300, 60), 0.25, 4 * u, 0.6)

  // A maple bough reaches in over the upper right corner.
  const b0 = at(1, 1, -40, -70)
  const b1 = at(1, 1, -330, -208)
  const bx = vec2(b1 - b0)
  const bl = length(bx)
  const bdir = vec2(bx / bl)
  const br = vec2(pt - b0)
  const ba = clamp(dot(br, bdir) / bl, 0, 1)
  const bcr = abs(br.x * bdir.y - br.y * bdir.x - sin(ba * 5) * 9 * u) - (7 - 4.5 * ba) * u
  acc = over(acc, vec3(0.17, 0.13, 0.1), smoothstep(3.5 * u, -3.5 * u, bcr) * step(dot(br, bdir), bl) * 0.9)
  const LEAVES = [
    [-86, -120, 38, 0.5, 0.2], [-150, -150, 24, 3.6, 0.05], [-196, -118, 32, 1.2, 0.8], [-256, -146, 20, 2.9, 0.15],
    [-276, -206, 36, 0.2, 0.65], [-336, -236, 26, 3.9, 0.95], [-104, -176, 18, 5.7, 0.45], [-236, -228, 28, 2.5, 0.7],
    [-388, -262, 22, 0.9, 0.6],
  ]
  for (const l of LEAVES) {
    acc = mapleLeaf(acc, pt, at(1, 1, l[0]!, l[1]!), l[2]!, l[3]!, l[4]!, u)
  }
  return acc
})

// The session: what a mod may tell the pond about the session it sits behind, as the `values` of its Shader
// element. A few slow states; a Shader element given none reads every one as 0, and the pond is as it always is.
// busy: a turn is running. pace: how busy it is, 0 to 4 (the pond answers up to 3). waiting: the person is being
// waited for. making: something has just been written. trouble: something failed and is not yet mended.
// helpers: how many helpers are at work, up to 4.
const session = values({ busy: [0, 1], pace: [0, 4], waiting: [0, 1], making: [0, 1], trouble: [0, 1], helpers: [0, 4] })

// What the pond keeps of the session from frame to frame, in two texels.
// Texel 0. x: was a turn running a frame ago. y: seconds since a turn last ended. z: a clock that ticks once
// for each midge that touches the water, faster as the pace rises. w: a clock that ticks once for each leaf
// that falls from the bough while something is being written.
// Texel 1. x: was there trouble a frame ago. y: seconds since trouble last cleared.
const mood: Buffer = buffer({ size: [2, 1], float: 32, filter: 'nearest' }, (p): vec4 => {
  const m = mood.at(vec2(0, 0))
  const t = mood.at(vec2(1, 0))
  const isBusy = step(0.5, session.busy)
  const inTrouble = step(0.5, session.trouble)
  let since = m.x > 0.5 && isBusy < 0.5 ? 0 : min(m.y + dt, 99)
  let mended = t.x > 0.5 && inTrouble < 0.5 ? 0 : min(t.y + dt, 99)
  // Work goes on while a turn runs and while helpers are at work. (The pace lingers after a turn ends, so it
  // only says how lively the work is, not whether there is any.)
  const working = max(isBusy, step(0.5, session.helpers))
  let midge = mod(m.z + dt * working * (0.16 + 0.18 * min(session.pace, 3)), 4096)
  let leaf = mod(m.w + dt * 0.2 * step(0.5, session.making), 4096)
  if (first) {
    since = 99
    mended = 99
    midge = 0
    leaf = 0
  }
  return p.cell.x < 0.5 ? vec4(isBusy, since, midge, leaf) : vec4(inTrouble, mended, 0, 0)
})

// The koi steer themselves: a tiny buffer holds each one's place, heading, speed and mood from frame to frame.
const pick7 = <T>(l: readonly T[], i: number): T => (i < 0.5 ? l[0]! : i < 1.5 ? l[1]! : i < 2.5 ? l[2]! : i < 3.5 ? l[3]! : i < 4.5 ? l[4]! : i < 5.5 ? l[5]! : l[6]!)
const K_LEN = [235, 205, 180, 165, 150, 135, 105]
const K_CRUISE = [30, 34, 38, 40, 42, 44, 50]
const K_HOME = [vec2(0.15, 0.42), vec2(0.86, 0.6), vec2(0.5, 0.5), vec2(0.2, 0.64), vec2(0.81, 0.36), vec2(0.5, 0.44), vec2(0.5, 0.56)]
const K_AMP = [vec2(0.09, 0.3), vec2(0.08, 0.28), vec2(0.42, 0.3), vec2(0.13, 0.25), vec2(0.12, 0.25), vec2(0.4, 0.32), vec2(0.44, 0.36)]
// Where each starts (as shares of the window) and which way it faces: the same poses the still Svg shows.
const K_INIT = [vec3(0.16, 0.42, 1.2), vec3(0.86, 0.62, -1.9), vec3(0.7, 0.27, 2.8), vec3(0.25, 0.72, 0.3), vec3(0.79, 0.36, 2.4), vec3(0.33, 0.2, 0.5), vec3(0.63, 0.8, 3.4)]
// How fast a ring travels, in layout units a second: unhurried water. Each push on it sends a single ring,
// not a train.
const SPEED_C = 84

const fish: Buffer = buffer({ size: [8, 4], float: 32, filter: 'nearest' }, (p): vec4 => {
  const u = unitOf()
  const i = p.cell.x
  const s0 = fish.at(vec2(i, 0))
  const s1 = fish.at(vec2(i, 1))
  const L = pick7(K_LEN, i) * u
  let pos = vec2(s0.x, s0.y)
  let th = s0.z
  let v = s0.w
  let ph = s1.x
  let trn = s1.y
  let gulp = s1.z
  let rise = s1.w
  // The message box, and this koi's place at it (used when the person is waited for). The app's text lies
  // over the middle of the pond like frosted glass, so the four koi that keep to the banks take places in
  // the open water at the two sides of it, and the three roamers a fan above the box itself. All of them
  // face the box.
  const known = step(0.001, composer.z - composer.x)
  const boxL = mix(0.257, composer.x, known) * size.x
  const boxR = mix(0.743, composer.z, known) * size.x
  const boxTop = mix(0.13, composer.w, known) * size.y
  const boxMid = vec2((boxL + boxR) * 0.5, boxTop)
  const fanR = (boxR - boxL) * 0.3
  const slotAt = pick7(
    [
      vec2(boxL - 34 * u, boxTop + 165 * u),
      vec2(boxR + 34 * u, boxTop + 205 * u),
      vec2(boxMid + vec2(0, fanR)),
      vec2(boxL - 22 * u, boxTop + 330 * u),
      vec2(boxR + 22 * u, boxTop + 365 * u),
      vec2(boxMid + vec2(0.5, 0.8) * fanR),
      vec2(boxMid + vec2(-0.5, 0.8) * fanR),
    ],
    i,
  )
  const faceBox = vec2(normalize(vec2(boxMid - slotAt)))
  if (first) {
    // A start in the middle of a wait (the engine starts a scene afresh now and then) begins with the koi
    // already at the box, so nothing is seen to jump.
    const init = pick7(K_INIT, i)
    const atBox = step(0.5, session.waiting)
    pos = vec2(mix(vec2(init.xy * size), vec2(slotAt - faceBox * L * 0.33), atBox))
    th = mix(init.z, atan(faceBox.y, faceBox.x), atBox)
    v = 8 * u
    ph = i * 1.3
    trn = 0
    gulp = 0
    rise = pick7([0.62, 0.3, 0.7, 0.78, 0.5, 0.2, 0.84], i)
  }
  const dir = vec2(cos(th), sin(th))
  const mouth = vec2(pos + dir * L * 0.33)
  // A slow waypoint on a closed path of its own; the koi follows it, and idles when it has caught up.
  const home = pick7(K_HOME, i)
  const amp = pick7(K_AMP, i)
  const idleWp = vec2(home + amp * vec2(sin(time * (0.043 + 0.009 * i) + i * 1.7), sin(time * (0.061 + 0.007 * i) + i * 2.9)))
  // While work goes on the koi have somewhere to be: they string out nose to tail on one slow circuit of the pond.
  const round = time * 0.11 - i * 0.62
  const working = max(step(0.5, session.busy), step(0.5, session.helpers))
  const wp = vec2(mix(idleWp, vec2(0.5 + 0.37 * cos(round), 0.5 + 0.35 * sin(round)), working) * size)
  let goal = wp
  let want = pick7(K_CRUISE, i) * u * (1 + 0.15 * working) * smoothstep(30 * u, 230 * u, length(vec2(wp - pos))) + 6 * u
  // Food: each koi fancies a pellet by how near it is, with a taste of its own so they do not all pick the same one.
  let bestD = 90000
  let foodAt = vec2(0)
  let hasFood = 0
  let bite = 0
  for (let k = 0; k < 15; k++) {
    const f = food.at(vec2(k, 0))
    // A pellet is 1. A midge a koi would take is 0.9, and it is worth only a short swim; one at 0.8 will fly off.
    // The koi take it in turns to go for food: four of the seven at a time, and while work goes on only two
    // or three leave the circuit. Seven at one spot is a scrum, and a scrum flickers.
    const alive = step(0.85, f.w) * mix(step(mod(i + floor(time / 9), 7), 3.5), step(mod(i + floor(time / 7), 3), 0.5), working)
    const dm = length(vec2(f.xy - mouth))
    // While work goes on, the koi that keep to a bank do not leave the circuit to cross the pond for
    // food; the roamers still go anywhere for it.
    const reach = pick7([300, 300, 760, 380, 380, 760, 760], i) * u
    const d = dm + one(i, k, 5) * 170 * u + (1 - alive) * 90000 + step(f.w, 0.95) * step(420 * u, dm) * 90000 + step(reach, dm) * 90000 * working
    bite = max(bite, step(0.25, f.w) * step(dm, 15 * u))
    if (d < bestD) {
      bestD = d
      foodAt = f.xy
      hasFood = alive
    }
  }
  const dFood = length(vec2(foodAt - mouth))
  if (hasFood > 0.5) {
    goal = vec2(foodAt - dir * L * 0.3)
    want = mix(18, mix(60, 52, working), smoothstep(15 * u, 190 * u, dFood)) * u
  }
  // The session. The message box is the bank where a person stands. When the person is waited for, every koi
  // comes and hovers in a fan round the box, facing it, mouths up, as pond koi do for someone at the edge.
  // Food still comes first.
  const called = step(0.5, session.waiting) * (1 - hasFood)
  const toSlot = length(vec2(slotAt - mouth))
  const there = called * smoothstep(90 * u, 25 * u, toSlot)
  goal = mix(goal, vec2(slotAt - dir * L * 0.3), called)
  want = mix(want, 95 * u * smoothstep(12 * u, 260 * u, toSlot), called)
  // When a turn ends, the gold one rolls at the surface, and then they all glide off from the box for a while.
  const since = mood.at(vec2(0, 0)).y
  const roll = (i > 1.5 && i < 2.5 ? 1 : 0) * step(since, 1.3) * sin(PI * clamp(since / 1.3, 0, 1))
  const leaving = smoothstep(0.9, 1.6, since) * smoothstep(7, 4, since) * (1 - hasFood)
  const fromBox = vec2(pos - boxMid)
  goal = vec2(goal + (fromBox / max(length(fromBox), 1)) * 300 * u * leaving)
  want = want + 26 * u * leaving
  // A fast hovering pointer makes a near koi shy away.
  let flee = vec2(0)
  for (const f of pointers) {
    const live = (1 - step(0.0001, f.gone)) * (1 - f.down)
    const sp = length(vec2(f.at - f.was)) / max(dt, 0.004)
    const away = vec2(pos - f.at)
    const dd = length(away)
    const k = live * smoothstep(150, 800, sp) * smoothstep(200 * u, 70 * u, dd)
    flee = vec2(flee + (away / max(dd, 1)) * k)
  }
  const fear = min(length(flee), 1)
  // Keep a little room from the others, less so at the food.
  let sep = vec2(0)
  for (let j = 0; j < 7; j++) {
    const o = fish.at(vec2(j, 0))
    const dv = vec2(pos - o.xy)
    const dd = length(dv)
    const reach = (L + pick7(K_LEN, j) * u) * 0.32
    const k = smoothstep(reach, reach * 0.3, dd) * step(0.5, abs(j - i))
    sep = vec2(sep + (dv / max(dd, 1)) * k)
  }
  const mrg = 30 * u
  const inward = vec2(
    smoothstep(mrg, -mrg, pos.x) - smoothstep(size.x - mrg, size.x + mrg, pos.x),
    smoothstep(mrg, -mrg, pos.y) - smoothstep(size.y - mrg, size.y + mrg, pos.y),
  )
  const to = vec2(goal - pos)
  const toBox = vec2(boxMid - pos)
  const toN = vec2(mix(vec2(to / max(length(to), 1)), vec2(toBox / max(length(toBox), 1)), there))
  // A lazy swerve so that no path is a straight line.
  const wa = (0.6 * sin(time * 0.21 + i * 2.3) + 0.35 * sin(time * 0.37 + i * 4.1)) * (1 - hasFood) * (1 - called)
  const cw = cos(wa)
  const sw = sin(wa)
  const des = vec2(vec2(toN.x * cw - toN.y * sw, toN.x * sw + toN.y * cw) + sep * (1.1 - mix(0.4, 0.1, working) * hasFood) + flee * 2.5 + inward * 3)
  const err = atan(dir.x * des.y - dir.y * des.x, dot(dir, des))
  // A koi going for food turns no faster than one at ease: a big fish that swings half round on the spot sweeps its
  // markings across the water faster than is kind to the eye.
  const maxT = (0.8 + 1.4 * fear) * (0.6 + (70 * u) / L)
  const tgt = clamp(err * 2, -maxT, maxT)
  trn = trn + (tgt - trn) * (1 - exp(-dt * 3.5))
  th = mod(th + trn * dt + PI, 2 * PI) - PI
  const down = step(0.5, session.trouble) * (1 - hasFood)
  want = (want + fear * 70 * u) * (1 - 0.6 * down)
  v = v + (want * (0.8 + 0.2 * sin(ph * 0.5)) - v) * (1 - exp(-dt * 1.3))
  pos = vec2(pos + dir * v * dt)
  // A slow beat: big koi are languid, and a tail that sweeps less often is also kinder to the eye.
  ph = mod(ph + dt * (1.8 + (v / u) * 0.018), 4 * PI)
  // A waiting koi opens its mouth at the box now and then.
  const beg = there * step(0.992, sin(time * 0.7 + i * 2.4))
  // Trouble sends every koi down, dim and slow. When it is mended they come up one after another, and each
  // takes a gulp of air at the top: a line of rings across the pond.
  const mended = mood.at(vec2(1, 0)).y
  const cheer = step(0.25 + 0.16 * i, mended) * step(mended, 0.4 + 0.16 * i)
  gulp = max(gulp - dt / 0.8, max(bite, max(beg, cheer)))
  const calm = pick7([0.62, 0.3, 0.7, 0.78, 0.5, 0.2, 0.84], i) + 0.14 * sin(time * 0.13 + i * 1.9)
  const up = step(mended, 1.8)
  const riseTo = mix(mix(mix(calm, 1, hasFood * smoothstep(210 * u, 60 * u, dFood)), 1, max(max(there * 0.9, roll), up)), 0.04, down)
  // Going down for trouble and coming up from it are slow, so trouble that comes and goes quickly barely shows.
  rise = rise + (riseTo - rise) * (1 - exp(-dt * mix(1.4, 0.45, max(down, up))))
  // Row 2, for the water: where the mouth is now, the kick of a gulp, and the push of a back breaking the surface.
  const splash = 24 * step(0.5, roll + step(since, 0.45) * (i > 1.5 && i < 2.5 ? 1 : 0)) * step(since, 0.45) * sin(since * 7)
  const lips = vec4(pos + vec2(cos(th), sin(th)) * L * 0.34, 9 * step(0.8, gulp) + splash, (1.3 * smoothstep(0.6, 1, rise) * v) / (90 * u))
  // Row 3: how far through its roll, and whether it has reached its place at the box.
  return p.cell.y < 0.5 ? vec4(pos, th, v) : p.cell.y < 1.5 ? vec4(ph, trn, gulp, rise) : p.cell.y < 2.5 ? lips : vec4(roll, there, 0, 0)
})

// Food: fifteen slots in a ring (x, y, age, state) and a counter in the last texel.
// State 1 is a pellet afloat, 0.5 is one being swallowed, 0 is gone. While work goes on, midges touch the water
// in the margins and take slots too: 0.9 is one a koi will rise to, 0.8 is one that flies off again.
const food: Buffer = buffer({ size: [16, 1], float: 32, filter: 'nearest' }, (p): vec4 => {
  const u = unitOf()
  const k = p.cell.x
  const f = food.at(vec2(k, 0))
  const cnt = food.at(vec2(15, 0)).x
  let pos = vec2(f.x, f.y)
  let age = f.z + dt
  let state = f.w
  let spawned = 0
  const tick = floor(mood.at(vec2(0, 0)).z)
  const newMidge = step(0.5, tick - food.at(vec2(15, 0)).y)
  for (const fg of pointers) {
    const live = (1 - step(0.0001, fg.gone)) * fg.down * (1 - fg.over)
    const n0 = floor(fg.age / 0.7)
    const n1 = floor((fg.age - dt) / 0.7)
    const many = live * step(0.5, n0 - n1) * (n0 < 0.5 ? 3 : 1)
    const rel = mod(k - cnt - spawned, 15)
    if (rel < many - 0.5 && k < 14.5) {
      const jit = vec2(one(frame, k, 3) - 0.5, one(frame, k, 4) - 0.5)
      pos = vec2(fg.at + jit * 46 * u * step(0.5, rel) + jit * 8 * u)
      age = 0
      state = 1
    }
    spawned = spawned + many
  }
  const relM = mod(k - cnt - spawned, 15)
  if (relM < newMidge - 0.5 && k < 14.5) {
    const side = one(tick, 1, 61)
    pos = vec2(vec2(side < 0.5 ? 0.04 + 0.4 * side : 1.16 - 0.4 * side, 0.14 + 0.72 * one(tick, 2, 61)) * size)
    age = 0
    state = one(tick, 3, 61) < 0.55 ? 0.9 : 0.8
  }
  spawned = spawned + newMidge
  // A midge does not stay: it is taken within a few seconds or it is gone.
  if (state > 0.75 && state < 0.95 && age > 4.5) {
    state = 0
  }
  // A pellet near a mouth is taken; it lingers half a second as it goes down.
  let taken = 0
  for (let j = 0; j < 7; j++) {
    const s = fish.at(vec2(j, 0))
    const mouth = vec2(s.xy + vec2(cos(s.z), sin(s.z)) * pick7(K_LEN, j) * u * 0.33)
    taken = max(taken, step(length(vec2(mouth - pos)), 12 * u))
  }
  if (state > 0.85 && (taken > 0.5 || age > 45)) {
    state = 0.5
    age = 0
  }
  if (state < 0.75 && state > 0.25 && age > 0.45) {
    state = 0
  }
  // Pellets ride the ripples a little and drift with a slow eddy.
  const uvp = vec2(pos / size)
  const e = vec2(1.5 / wave.size.x, 1.5 / wave.size.y)
  const gx = wave.sample(vec2(uvp + vec2(e.x, 0))).r - wave.sample(vec2(uvp - vec2(e.x, 0))).r
  const gy = wave.sample(vec2(uvp + vec2(0, e.y))).r - wave.sample(vec2(uvp - vec2(0, e.y))).r
  const eddy = vec2(sin(pos.y / (140 * u) + time * 0.11), cos(pos.x / (170 * u) - time * 0.09))
  pos = vec2(pos + (eddy * 2.2 * u - vec2(gx, gy) * 26 * u) * dt)
  return k > 14.5 ? vec4(mod(cnt + spawned, 15), tick, 0, 0) : vec4(pos, age, state)
})

// The small players are placed once a frame in a strip of texels: two water striders (x, y, kick) and five
// fireflies (x, y, glow). A strider skates from one spot to the next in short hops; a firefly drifts on a slow
// loop of its own and glows and fades.
const FLY = [vec3(0.1, 0.42, 1), vec3(0.2, 0.72, 2.3), vec3(0.84, 0.24, 3.9), vec3(0.9, 0.7, 5.1), vec3(0.27, 0.2, 0.4)]
const cast = buffer({ size: [8, 1], float: 32, filter: 'nearest' }, p => {
  const u = unitOf()
  const k = p.cell.x
  const every = 4.3 + 1.8 * k
  const beat = time / every + 0.37 * k
  const n = floor(beat)
  const fr = (beat - n) * every
  const from = vec2(one(n, 1, 43 + k), one(n, 2, 43 + k))
  const to = vec2(one(n + 1, 1, 43 + k), one(n + 1, 2, 43 + k))
  const a = vec2(mix(from, to, smoothstep(0, 0.45, fr)))
  // Keep striders to the margins: fold the width out to the two sides.
  const x = a.x < 0.5 ? a.x * 0.44 + 0.02 : 1 - (1 - a.x) * 0.44 - 0.02
  const strider = vec4(vec2(x, 0.1 + 0.8 * a.y) * size, step(fr, 0.1) + step(0.45, fr) * step(fr, 0.55), 0)
  const f = k < 2.5 ? FLY[0]! : k < 3.5 ? FLY[1]! : k < 4.5 ? FLY[2]! : k < 5.5 ? FLY[3]! : FLY[4]!
  const at = vec2(vec2(f.x, f.y) * size + vec2(sin(time * 0.23 + f.z * 3), cos(time * 0.17 + f.z * 5)) * 46 * u)
  const fly = vec4(at, smoothstep(-0.2, 0.9, sin(time * 0.9 + f.z * 2.1)), 0)
  return k < 1.5 ? strider : fly
})
// Where and when the last four presses began (x, y, time, strength), and a counter in the last texel. A
// press is a plop at the place it began, and its rings leave that place whether the pointer stays or lifts.
const plops: Buffer = buffer({ size: [5, 1], float: 32, filter: 'nearest' }, (p): vec4 => {
  const k = p.cell.x
  const old = plops.at(vec2(k, 0))
  const cnt = plops.at(vec2(4, 0)).x
  let made = 0
  let out = first ? vec4(0, 0, -99, 0) : old
  for (const f of pointers) {
    const live = (1 - step(0.0001, f.gone)) * f.down
    // A pointer is new from the moment it presses: its age is 0 on the frame of the press and on no later one.
    const began = live * (1 - step(0.5 * dt, f.age))
    // A pressed pointer that leaves the circle of 45 units round its own press (the press as old as the
    // pointer) is dragging, and that press sends nothing more: what is left of its plop, and its two later
    // echoes (see stir), are dropped. A pointer that was never inside the circle drops nothing, and neither
    // does one that came down more than 0.08 seconds before or after the press. Two that come down together
    // cannot be told apart: either drops the other's press too if it leaves that press's circle.
    const reach = 45 * unitOf()
    if (live > 0.5 && began < 0.5 && abs(time - f.age - out.z) < 0.08 && length(vec2(f.was - out.xy)) <= reach && length(vec2(f.at - out.xy)) > reach && time - out.z < 2.2) {
      out = vec4(out.xy, out.z, 0)
    }
    if (began > 0.5 && abs(mod(cnt + made, 4) - k) < 0.5) {
      out = vec4(f.at, time, 1 - 0.5 * f.over)
    }
    made = made + began
  }
  return k > 3.5 ? vec4(first ? 0 : mod(cnt + made, 4), 0, 0, 0) : out
})

// What stirs the water this frame, gathered once: pointers, mouths, the striders' feet.
const stir = buffer({ scale: 0.2, float: 16, filter: 'nearest' }, p => {
  const u = unitOf()
  let push = 0
  for (const f of pointers) {
    const live = 1 - step(0.0001, f.gone)
    const ds = strokeAway(p.point, f.was, f.at) / (22 * u)
    const sp = length(vec2(f.at - f.was)) / max(dt, 0.004)
    const soft = 1 - 0.5 * f.over
    // A steady, gentle push, so a drag leaves one wake and no train of rings.
    push = push - 6.5 * smoothstep(20, 500, sp) * live * soft * exp(-ds * ds)
  }
  // A press is a plop and two echoes of it, each weaker and nine tenths of a second after the last: three
  // rings leave the spot, stately, with clear water between them. Each lifts as much water as it presses
  // down, so no bowl stays.
  for (const k of [0, 1, 2, 3]) {
    const pl = plops.at(vec2(k, 0))
    const age = time - pl.z
    const beat = step(age, 0.32) * sin(age * 9.8) + 0.6 * step(0.9, age) * step(age, 1.22) * sin((age - 0.9) * 9.8) + 0.36 * step(1.8, age) * step(age, 2.12) * sin((age - 1.8) * 9.8)
    const d0 = length(vec2(p.point - pl.xy)) / (21 * u)
    push = push - 68 * pl.w * beat * (1 - d0 * d0) * exp(-d0 * d0)
  }
  for (let j = 0; j < 7; j++) {
    const lips = fish.at(vec2(j, 2))
    const dm = length(vec2(p.point - lips.xy)) / (20 * u)
    push = push - (lips.z * (1 - dm * dm) + lips.w) * exp(-dm * dm)
  }
  for (const k of [0, 1]) {
    const s = cast.at(vec2(k, 0))
    const dd = length(vec2(p.point - s.xy)) / (17 * u)
    push = push - 2 * s.z * exp(-dd * dd)
  }
  // A midge's touch: a small clean ring where the newest one has just landed.
  const newest = food.at(vec2(mod(food.at(vec2(15, 0)).x + 14, 15), 0))
  const dn = length(vec2(p.point - newest.xy)) / (16 * u)
  push = push - 16 * step(newest.z, 0.1) * step(0.75, newest.w) * step(newest.w, 0.95) * (1 - dn * dn) * exp(-dn * dn)
  // A leaf that has just dropped from the bough.
  const lk = mod(floor(mood.at(vec2(0, 0)).w), 4)
  const dl = length(vec2(p.point - afloat.at(vec2(lk, 0)).xy)) / (20 * u)
  push = push - 18 * step(afloat.at(vec2(lk, 1)).z, 0.12) * (1 - dl * dl) * exp(-dl * dl)
  return vec4(push, 0, 0, 1)
})

// The water: the wave equation on a grid of five-point cells. r is height, g is its speed, b and a its slope.
const wave: Buffer = buffer({ scale: 0.2, float: 16, filter: 'linear', repeat: 2 }, (p): vec4 => {
  const u = unitOf()
  const c = wave.at(p.cell)
  const l = wave.at(vec2(p.cell - vec2(1, 0))).r
  const r = wave.at(vec2(p.cell + vec2(1, 0))).r
  const d = wave.at(vec2(p.cell - vec2(0, 1))).r
  const t = wave.at(vec2(p.cell + vec2(0, 1))).r
  const tl = wave.at(vec2(p.cell + vec2(-1, 1))).r
  const tr = wave.at(vec2(p.cell + vec2(1, 1))).r
  const bl = wave.at(vec2(p.cell + vec2(-1, -1))).r
  const br = wave.at(vec2(p.cell + vec2(1, -1))).r
  // All eight neighbours, the four nearest weighing four times the corners: rings come out round, not square.
  const lap = (4 * (l + r + d + t) + tl + tr + bl + br - 20 * c.r) / 6
  const cs = SPEED_C * u
  // Half a frame a turn, never more than the grid can carry, so a slow frame slows the water and cannot break it.
  const tau = min(dt / 2, (0.62 * px) / cs)
  const k2 = (cs * cs) / (px * px)
  const ed = min(min(p.cell.x, res.x - 1 - p.cell.x), min(p.cell.y, res.y - 1 - p.cell.y))
  const soak = 1 - smoothstep(0, 9, ed)
  let vel = (c.g + k2 * lap * tau) * exp(-tau * (0.4 + 7 * soak))
  const push = stir.at(p.cell).r
  const h = clamp(c.r + (vel + push) * tau + 1.5 * tau * lap, -1.5, 1.5)
  // b and a carry the slope across and up, taken over all eight neighbours so that it turns smoothly; the
  // picture reads the slope from here.
  return vec4(h, vel, (2 * (r - l) + tr - tl + br - bl) / 4, (2 * (t - d) + tl - bl + tr - br) / 4)
})

// Fallen leaves afloat: four maple leaves that drift on a slow eddy, slide down the face of a ripple,
// and are carried off when a pointer stirs the water beside them. Row 0 is place and speed; row 1 is
// turn, spin, seconds since it landed, and the last tick of the leaf clock it saw.
const pick4 = <T>(l: readonly T[], i: number): T => (i < 0.5 ? l[0]! : i < 1.5 ? l[1]! : i < 2.5 ? l[2]! : l[3]!)
const LEAF_AT = [vec3(0.7, 0.65, 2.2), vec3(0.92, 0.54, 4.9), vec3(0.09, 0.44, 0.7), vec3(0.27, 0.12, 3.3)]
const afloat: Buffer = buffer({ size: [4, 2], float: 32, filter: 'nearest' }, (p): vec4 => {
  const u = unitOf()
  const k = p.cell.x
  const s = afloat.at(vec2(k, 0))
  const r = afloat.at(vec2(k, 1))
  let pos = vec2(s.x, s.y)
  let vel = vec2(s.z, s.w)
  let ang = r.x
  let spin = r.y
  let landed = r.z + dt
  if (first) {
    const init = pick4(LEAF_AT, k)
    pos = vec2(init.xy * size)
    vel = vec2(0)
    ang = init.z
    spin = 0
    landed = 99
  }
  // While something is being written, a leaf lets go of the bough now and then: the four take it in turn to
  // be that leaf, and land on the water under it.
  const fall = floor(mood.at(vec2(0, 0)).w)
  if (fall > r.w + 0.5 && abs(mod(fall, 4) - k) < 0.5) {
    pos = vec2(vec2(0.76 + 0.18 * one(fall, 1, 67), 0.66 + 0.2 * one(fall, 2, 67)) * size)
    vel = vec2(0)
    landed = 0
  }
  const uvp = vec2(pos / size)
  const e = vec2(1.5 / wave.size.x, 1.5 / wave.size.y)
  const gx = wave.sample(vec2(uvp + vec2(e.x, 0))).r - wave.sample(vec2(uvp - vec2(e.x, 0))).r
  const gy = wave.sample(vec2(uvp + vec2(0, e.y))).r - wave.sample(vec2(uvp - vec2(0, e.y))).r
  const eddy = vec2(sin(pos.y / (150 * u) + time * 0.07 + k), cos(pos.x / (180 * u) - time * 0.06 + k * 2))
  vel = vec2(vel + (eddy * 3 * u - vel) * (1 - exp(-dt * 0.5)) - vec2(gx, gy) * 420 * u * dt)
  for (const f of pointers) {
    const live = 1 - step(0.0001, f.gone)
    const mv = vec2((f.at - f.was) / max(dt, 0.004))
    const sp = length(mv)
    const near = live * smoothstep(80 * u, 25 * u, length(vec2(pos - f.at)))
    const carry = vec2((mv / max(sp, 1)) * min(sp, 260) * 0.4)
    vel = vec2(vel + (carry - vel) * near * (1 - exp(-dt * 9)))
    spin = spin + near * min(sp, 400) * 0.004 * (k < 1.5 ? 1 : -1) * dt * 30
  }
  // Stay on the water: a soft push back from the edges.
  const mrg = 40 * u
  vel = vec2(vel + vec2(smoothstep(mrg, 0, pos.x) - smoothstep(size.x - mrg, size.x, pos.x), smoothstep(mrg, 0, pos.y) - smoothstep(size.y - mrg, size.y, pos.y)) * 30 * u * dt)
  pos = vec2(pos + vel * dt)
  spin = clamp(spin, -2, 2) * exp(-dt * 0.8)
  ang = mod(ang + (spin + 0.03) * dt, 2 * PI)
  return p.cell.y < 0.5 ? vec4(pos, vel) : vec4(ang, spin, min(landed, 99), fall)
})

// The koi, drawn as one quad each into a layer of their own, so the picture can bend them through the
// surface and drop their shadows. Local frame: x runs along the body in body lengths (nose at 0.35), y across.
const pick6 = <T>(l: readonly T[], i: number): T => (i < 0.5 ? l[0]! : i < 1.5 ? l[1]! : i < 2.5 ? l[2]! : i < 3.5 ? l[3]! : i < 4.5 ? l[4]! : l[5]!)
const WHITE = vec3(0.89, 0.88, 0.81)
const RED = vec3(0.9, 0.3, 0.11)
const INK = vec3(0.1, 0.1, 0.12)
const GOLD = vec3(0.96, 0.74, 0.22)
const SLATE = vec3(0.42, 0.53, 0.64)
const ORANGE = vec3(0.95, 0.47, 0.12)
// The seven koi by variety, in order: kohaku, showa, ogon, sanke, tancho, asagi, hi
const K_BASE = [WHITE, INK, GOLD, WHITE, WHITE, SLATE, ORANGE]
const K_PATCH = [RED, RED, vec3(1, 0.86, 0.42), RED, WHITE, SLATE, vec3(0.98, 0.62, 0.2)]
const K_THR = [0.47, 0.5, 0.45, 0.56, 2, 2, 0.5]
const K_INKT = [2, 2, 2, 0.66, 2, 2, 2]
const K_FIN = [WHITE, vec3(0.8, 0.8, 0.8), vec3(1, 0.86, 0.45), WHITE, WHITE, vec3(0.95, 0.55, 0.2), vec3(1, 0.66, 0.3)]
const K_FINLEN = [1, 1, 1.5, 1, 1.1, 1, 1.15]

const koiLayer = buffer({ filter: 'mipmap' })

// One paired fin: a rayed teardrop hinged at (s0, y0), swept back by the angle beta.
const fin = (sN: number, ay: number, s0: number, y0: number, beta: number, len: number, wid: number, aa: number): number => {
  const rx = sN - s0
  const ry = ay - y0
  const cb = cos(beta)
  const sb = sin(beta)
  const al = rx * cb + ry * sb
  const ac = ry * cb - rx * sb
  const t = clamp(al / len, 0, 1)
  const hw = wid * sqrt(t) * sqrt(1.12 - t)
  const m = smoothstep(aa, -aa, abs(ac) - hw) * step(0, al) * smoothstep(1, 0.9, al / len)
  const rays = 0.5 + 0.5 * cos((ac / (al + 0.03)) * 26)
  return m * (0.36 + 0.16 * rays) * (1 - 0.6 * t)
}

const koi = shapes(
  { count: 6, instances: 7, cover: 0.26, draw: 'triangles', into: koiLayer, clear: true },
  (v, i) => {
    const u = unitOf()
    const s0 = fish.at(vec2(i, 0))
    const s1 = fish.at(vec2(i, 1))
    const L = pick7(K_LEN, i) * u
    const sx = pick6([0, 1, 0, 1, 1, 0], v)
    const sy = pick6([-1, -1, 1, -1, 1, 1], v)
    const fl = pick7(K_FINLEN, i)
    // The quad leans with the turn: its tail end is shifted sideways by the bend there, so a turning fish stays
    // inside a narrow quad. (The draw is charged by the area it may cover, and is dropped whole if it covers more.)
    const lx = mix(-0.65 - 0.36 * fl, 0.38, sx)
    const lean = clamp(s1.y, -1.5, 1.5) * 0.11 * pow(0.78 + 0.36 * fl, 2) * (1 - sx)
    // A koi rolling at the surface is seen edge on for a moment.
    const roll = fish.at(vec2(i, 3)).x
    const ly = sy * (0.37 + 0.16 * (fl - 1)) * (1 - 0.62 * roll) + lean
    const dir = vec2(cos(s0.z), sin(s0.z))
    const w = vec2(s0.xy + dir * lx * L + vec2(-dir.y, dir.x) * ly * L)
    // The roll rides with the koi's number, as a fraction under a half.
    return { at: vec2((w / size) * 2 - 1), a: vec4(lx, ly, i + 0.45 * roll, s1.x), b: vec4(s1.y, s1.z, s1.w, dir.x * SUN.y - dir.y * SUN.x) }
  },
  s => {
    const u = unitOf()
    const id = floor(s.a.z + 0.5)
    const L = pick7(K_LEN, id) * u
    // A fish lower in the water is seen less sharply.
    const aa = ((0.8 * s.px) / L) * (1 + 1.6 * (1 - s.b.z)) + 0.005 + 0.014 * (1 - s.b.z)
    const ph = s.a.w
    const trn = s.b.x
    const gulp = s.b.y
    const rise = s.b.z
    const fl = pick7(K_FINLEN, id)
    const sN = 0.35 - s.a.x
    // The spine: a travelling wave that grows toward the tail, and a bend into the turn.
    const env = 0.05 + 0.95 * min(sN * sN, 1.6)
    const bendAt = max(sN - 0.22, 0)
    const yc = 0.05 * env * sin(ph - 5.2 * sN) + clamp(trn, -1.5, 1.5) * 0.13 * bendAt * bendAt
    const y = s.a.y - yc
    const ay = abs(y)
    const nose = max(0.3 - sN, 0) / 0.3
    const hw = 0.148 * pow(clamp(1 - nose * nose, 0, 1), 0.62) * mix(1, 0.2, smoothstep(0.3, 1, sN))
    const body0 = smoothstep(aa, -aa, ay - hw) * step(0, sN) * smoothstep(1.02, 0.97, sN)
    const vN = clamp(y / max(hw, 0.004), -1, 1)
    const eyeAt = length(vec2(sN - 0.1, ay - 0.088))
    const body = max(body0, smoothstep(0.012 + aa, 0.012 - aa * 0.5, eyeAt) * 0.85)

    // Pattern: patches that belong to this one fish.
    // Each is a few slow waves laid over each other, bent a little so that no border runs straight.
    const own = id * 2.4 + 1
    const sW = sN + 0.025 * sin(vN * 6 + own * 5)
    const vW = vN + 0.16 * sin(sN * 21 + own * 3)
    const pn = 0.5 + 0.27 * (sin(sW * 7.5 + own * 1.7) * cos(vW * 1.9 + own) + 0.7 * sin(sW * 12.3 - vW * 2.6 + own * 2.9))
    const pn2 = 0.5 + 0.3 * (sin(sW * 19 + own * 3.1) * sin(vW * 4.3 + own * 1.3) + 0.6 * cos(sW * 31 - vW * 3 + own))
    const base = pick7(K_BASE, id)
    const thr = pick7(K_THR, id)
    const su = sN / 0.03
    const row = floor(su)
    const sv = y / 0.026 + 0.5 * mod(row, 2)
    let c = mix(base, pick7(K_PATCH, id), smoothstep(thr - 0.1, thr + 0.1, pn))
    // Showa: white breaks through the ink. Sanke: small ink marks. Tancho: one red cap. Asagi: orange flanks.
    c = mix(c, WHITE, (id > 0.5 && id < 1.5 ? 1 : 0) * smoothstep(0.54, 0.72, pn2))
    const inkAt = pick7(K_INKT, id)
    c = mix(c, INK, smoothstep(inkAt - 0.03, inkAt + 0.1, pn2))
    c = mix(c, RED, (id > 3.5 && id < 4.5 ? 1 : 0) * smoothstep(0.075, 0.045, length(vec2(sN - 0.16, y)) + 0.05 * (pn - 0.5)))
    const asagi = id > 4.5 && id < 5.5 ? 1 : 0
    c = mix(c, ORANGE, asagi * max(smoothstep(0.5, 0.86, abs(vN)), smoothstep(0.2, 0.1, sN) * 0.7))
    // Scales: offset rows of arcs, faint except on the asagi; mostly they show in the wet shine.
    const arc = length(vec2(su - row - 0.2, sv - floor(sv) - 0.5))
    const net = smoothstep(0.34, 0.52, arc) * smoothstep(0.2, 0.28, sN) * (1 - 0.5 * vN * vN)
    c = vec3(c * (1 - net * (0.085 + 0.07 * asagi)) * (1 - 0.09 * exp(-pow((sN - 0.225 - 0.05 * vN * vN) / 0.016, 2))))
    // Volume: a rounded back lit from the sun's side, with a wet streak.
    const sunSide = s.b.w
    const z = sqrt(max(1 - vN * vN, 0))
    // The back is round and a little brighter along the sun's side of the spine, with a thin wet line there on
    // a fish near the surface; its flanks fall away, and the rest of the light on it is the net of light's,
    // laid on in the picture pass.
    const back = exp(-pow((vN - 0.3 * sunSide) / 0.38, 2)) * z
    const wetLine = pow(back, 12) * (1 - 0.5 * net)
    c = vec3(c * (0.44 + 0.56 * z + 0.26 * sunSide * vN) * (0.93 + 0.14 * pn2) * (1 + 0.1 * back) + 0.14 * wetLine * smoothstep(0.35, 0.8, rise))
    // Head: eyes, and a mouth that opens for food.
    // Eyes: small dark half-bulges on the edge of the head.
    c = mix(c, vec3(0.06, 0.06, 0.07), smoothstep(0.028 + aa, 0.008, eyeAt) * 0.9)
    const open = smoothstep(0.1, 0.6, gulp)
    const lips = length(vec2((sN - 0.012) * 1.3, y))
    c = mix(c, vec3(0.98, 0.88, 0.84), open * smoothstep(0.034 + aa, 0.034, lips))
    c = mix(c, vec3(0.3, 0.1, 0.1), open * smoothstep(0.02 + aa, 0.02, lips))

    // Fins under the body: pectoral and pelvic pairs that scull, and a forked tail that fans with the stroke.
    const scull = 0.25 * sin(ph * 0.5 + id)
    const fp = fin(sN, ay, 0.26, 0.09, 1.02 + scull, 0.26 * fl, 0.095 * fl, aa)
    const fv = fin(sN, ay, 0.56, 0.07, 1.1 + 0.5 * scull, 0.1 * fl, 0.036 * fl, aa)
    const tN = (sN - 0.96) / (0.36 * fl)
    const spread = (0.8 + 0.2 * abs(cos(ph - 5.2))) * fl
    const tw = 0.026 + 0.15 * spread * pow(clamp(tN, 0, 1), 0.8)
    const fork = 1 - 0.3 * pow(clamp(1 - ay / max(tw, 0.004), 0, 1), 1.5)
    const tail = smoothstep(aa, -aa, ay - tw) * step(0, tN) * smoothstep(fork, fork - 0.1, tN)
    const trays = 0.5 + 0.5 * cos((y / max(tw, 0.004)) * 17)
    const ft = tail * (0.36 + 0.14 * trays) * (1 - 0.6 * clamp(tN, 0, 1))
    const fa = max(max(fp, fv), ft)
    const finC = pick7(K_FIN, id)
    // The dorsal fin: a narrow ridge along the back.
    const dt2 = clamp((sN - 0.36) / 0.36, 0, 1)
    const dors = smoothstep(aa, -aa, abs(y) - 0.05 * dt2 * (1 - dt2)) * step(0.36, sN) * step(sN, 0.72)
    c = vec3(c * (1 - 0.14 * dors))
    // Barbels: two pale whiskers at the mouth.
    // They are drawn only where the fish is seen sharply enough to show them.
    const barb = smoothstep(0.0045 + aa, 0.0045, strokeAway(vec2(sN, ay), vec2(0.012, 0.028), vec2(0.052, 0.078))) * smoothstep(0.014, 0.007, aa)

    // The water takes a fish's color by how deep it lies, red first, and gives back its own green; the tail
    // hangs a little lower than the head, and the flanks turn away into the water.
    const down = (1 - rise) * (0.75 + 0.5 * smoothstep(0.3, 1.2, sN))
    const water = vec3(0.26, 0.42, 0.38)
    const kept = vec3(exp(-0.62 * down), exp(-0.3 * down), exp(-0.27 * down))
    const veil = 1 - exp(-0.55 * down)
    // A koi rolling at the surface shows its pale belly.
    const rolled = clamp((s.a.z - id - 0.01) / 0.44, 0, 1)
    const bodyC = mix(vec3(mix(mix(c, vec3(0.93, 0.9, 0.8), 0.7 * rolled), water, 0.26 * abs(vN * vN * vN)) * kept), water, veil)
    const finA = fa * (0.7 + 0.3 * rise) * (1 - body)
    const finRGB = mix(vec3(finC * kept), water, min(veil + 0.12, 1))
    const barbA = barb * (1 - body) * (1 - finA) * 0.8
    // A thin soft shadow hugs the body, so a fish reads as lying over its own fins and over a fish beneath it.
    const hug = smoothstep(0.04, 0, ay - hw) * (1 - body) * 0.3 * step(0, sN) * smoothstep(1.02, 0.97, sN)
    const under = vec3(finRGB * finA + vec3(0.95, 0.82, 0.74) * barbA)
    // A tail flung wide in a hard turn fades out at the quad's edge instead of being cut.
    const lean = clamp(trn, -1.5, 1.5) * 0.11 * pow(0.78 + 0.36 * fl, 2) * (0.38 - s.a.x) / (1.03 + 0.36 * fl)
    const keep = smoothstep(1, 0.86, abs(s.a.y - lean) / (0.37 + 0.16 * (fl - 1)))
    return vec4(vec4(bodyC * body + under * (1 - hug), body + (finA + barbA) * (1 - hug) + hug) * keep)
  },
)

// Helpers. Each helper at work brings a school of three fry, which keeps to a loop of its own in open
// water. They are drawn into the koi's layer, so the water bends, lights and shades them as it does the koi.
const fry = shapes(
  { count: 1, instances: 12, cover: 0.012, draw: 'points', into: koiLayer },
  (v, i) => {
    const u = unitOf()
    const school = floor(i / 3)
    const shown = clamp(session.helpers - school, 0, 1)
    const own = i * 2.1
    const mid = pick4([vec2(0.3, 0.3), vec2(0.72, 0.7), vec2(0.3, 0.64), vec2(0.7, 0.34)], school)
    const t = time * 0.5 + school * 1.7
    const at = vec2(mid * size + (vec2(cos(t), sin(t * 1.3)) * 60 + vec2(cos(t * 2.3 + own), sin(t * 1.9 + own)) * 16) * u)
    const going = normalize(vec2(-sin(t) * 30 - sin(t * 2.3 + own) * 18.4, cos(t * 1.3) * 39 + cos(t * 1.9 + own) * 15.2))
    return { at: vec2((at / size) * 2 - 1), size: clamp((26 * u) / px, 1, 64), a: vec4(going, shown, 0), hide: shown < 0.02 }
  },
  s => {
    const local = vec2((s.coord.x - 0.5) * 26, (0.5 - s.coord.y) * 26)
    const along = local.x * s.a.x + local.y * s.a.y
    const across = local.y * s.a.x - local.x * s.a.y
    const body = smoothstep(1, 0.6, length(vec2(along / 10, across / (1.1 + 1.7 * smoothstep(-10, 3, along)))))
    return vec4(vec3(0.5, 0.54, 0.46) * body * s.a.z * 0.9, body * s.a.z * 0.9)
  },
)

// Pellets and midges: one point each.
const pellets = shapes(
  { count: 1, instances: 15, cover: 0.03, draw: 'points' },
  (v, i) => {
    const u = unitOf()
    const f = food.at(vec2(i, 0))
    const grow = smoothstep(0, 0.2, f.z)
    const k = f.w > 0.75 ? 0.6 + 0.4 * grow : 1 - smoothstep(0, 0.4, f.z)
    return { at: vec2((f.xy / size) * 2 - 1), size: clamp((22 * u) / px, 1, 64), a: vec4(k, f.w, i, 0), hide: f.w < 0.25 }
  },
  s => {
    const m = modeBuf.at(vec2(0, 0)).r
    const d = vec2((s.coord - 0.5) * 2)
    const r = length(d)
    const k = s.a.x
    const midge = step(0.75, s.a.y) * step(s.a.y, 0.95)
    const rad = mix(0.36 * k, 0.1, midge)
    const body = smoothstep(rad + 0.12, rad - 0.05, r)
    const lit = 0.75 + 0.4 * dot(d, vec2(-0.55, -0.83)) / max(rad, 0.05)
    const c = vec3(mix(vec3(0.8, 0.58, 0.3), vec3(0.1, 0.08, 0.06), midge) * clamp(lit, 0.45, 1.3) * mix(0.5, 1, m))
    // The dimple the pellet presses into the surface: a soft dark foot round it.
    const ring = smoothstep(0.98, 0.7, r) * smoothstep(rad - 0.05, rad + 0.25, r) * k
    const a = body + (1 - body) * ring * 0.22
    return vec4(c * body, a)
  },
)

// The resting swell: two sets of slow sine trains from all round the compass, one long and one short (the short
// set is the long one turned a quarter turn and drawn finer).
// Each gives the surface a curvature, which focuses the light on the bottom: threads of light lie where the
// sheet of light folds, which is where the determinant below passes through zero. The net is the finer of the
// two sets' folds, the short set a little fainter, so a bold net carries a faint one inside its cells. The long
// set also gives the slope that bends what is seen. All of it is worked once a frame on a coarse grid: slope
// in r and g, the net broadly in b and as fine threads in a.
const swell = (lambda: number, deg: number, speed: number, focus: number) => {
  const k = (2 * PI) / lambda
  const a = (deg * PI) / 180
  return { kx: k * cos(a), ky: k * sin(a), om: k * speed, tilt: (focus * lambda * lambda) / (6400 * PI), fold: focus / (k * k) }
}
const LONG = [swell(205, 17, 13, 0.78), swell(164, 71, 11, 0.72), swell(232, 133, 12, 0.78), swell(150, 186, 9, 0.7), swell(190, 247, 10, 0.74), swell(138, 309, 8, 0.66)]
const glim = buffer({ scale: 0.3, filter: 'linear' }, p => {
  const u = unitOf()
  const q = vec2(p.point / u)
  let gx = 0
  let gy = 0
  let hxx = 0
  let hxy = 0
  let hyy = 0
  let sxx = 0
  let sxy = 0
  let syy = 0
  for (const w of LONG) {
    const th = q.x * w.kx + q.y * w.ky - time * w.om
    const sn = sin(th) * w.fold
    const cs = cos(th) * w.tilt
    gx += w.kx * cs
    gy += w.ky * cs
    hxx -= w.kx * w.kx * sn
    hxy -= w.kx * w.ky * sn
    hyy -= w.ky * w.ky * sn
    // The short set: the same trains turned a quarter turn, 1.62 times as fine and a little slower.
    const s2 = sin((q.y * w.kx - q.x * w.ky) * 1.62 - time * w.om * 0.8) * w.fold * 0.92
    sxx -= w.ky * w.ky * s2
    sxy += w.kx * w.ky * s2
    syy -= w.kx * w.kx * s2
  }
  const det = min(abs((1 + hxx) * (1 + hyy) - hxy * hxy), abs((1 + sxx) * (1 + syy) - sxy * sxy) + 0.12)
  return vec4(gx * 2 + 0.5, gy * 2 + 0.5, clamp(0.3 / (det + 0.3), 0, 1), clamp(0.125 / (det + 0.07), 0, 1))
})
const MOON_AT = vec2(0.942, 0.58)

// What hangs over the pond, painted once and small. r: what the surface mirrors, which is open sky (1)
// over the middle of the pond and the dark of boughs (0) over its banks, with a ragged leafy border
// between. g: the shade the boughs throw, which the sun carries off to one side of them in broad soft
// patches. b: cloud, which makes the sky's brightness uneven. a: roughly how deep the water is there.
const overhead = buffer({ scale: 0.25, once: true, filter: 'linear' }, p => {
  const q = vec2(p.point / unitOf())
  const ragged = layered(vec2(q / 230), 101) - 0.5
  const leafy = lattice(vec2(q / 26), 103) - 0.5
  const mid = 1 - abs(p.uv.x - 0.5) * 2
  const sky = smoothstep(0.2, 0.62, mid + ragged * 0.8 + leafy * 0.22)
  const shade = layered(vec2(q / 340 + 9), 107) - 0.3 * (p.uv.x + p.uv.y - 1)
  const deep = clamp(0.76 - 0.56 * shelfOf(p.uv, (layered(vec2(q / 260), 11) - 0.5) * 0.14), 0, 1)
  return vec4(sky, smoothstep(0.48, 0.74, shade), layered(vec2(q / 420 + 5), 113), deep)
})

// Film grain: one small tile of scatter, laid over the picture and never changed.
const grain = buffer({ size: [128, 128], once: true, filter: 'nearest', wrap: 'repeat' }, p => vec4(one(p.cell.x, p.cell.y, 131), 0, 0, 1))

// The picture: bottom, light, koi and surface put together through the moving water.
const view = picture(p => {
  const u = unitOf()
  const m = modeBuf.at(vec2(0, 0)).r
  const rest = glim.sample(p.uv)
  const gx = (rest.r - 0.5) * 0.5
  const gy = (rest.g - 0.5) * 0.5
  // The net of light: wide dim cells, thin bright threads, and knots where threads cross.
  const net = 0.8 + 0.3 * clamp(rest.b * 2 - 0.4, 0, 1.5) + 0.5 * clamp(rest.a * 2.4 - 0.65, 0, 1.6)
  // The live ripples from the wave buffer: height and slope.
  // Two reads half a cell apart, averaged, so the slope turns smoothly across the grid's cells.
  const half = vec2(0.5 / wave.size.x, 0.5 / wave.size.y)
  const ripple = vec4((wave.sample(vec2(p.uv + half)) + wave.sample(vec2(p.uv - half))) * 0.5)
  const live = vec2(clamp(ripple.b, -3, 3) * 0.8, clamp(ripple.a, -3, 3) * 0.8)
  const g0 = vec2(vec2(gx, gy) + live * 5)
  // The clamp changes nothing (the quotient cannot pass 0.22); it tells the validator's cost count how near the reads stay.
  const g = clamp(vec2(g0 / (1 + 4.5 * length(g0))), -0.22, 0.22)
  // Refraction: everything under the surface is seen shifted by the slope above it, deeper things more.
  const bend = vec2((g * u) / size)
  // The bottom blurs a little with depth: a coarser level of its picture is read where the water is deeper.
  const up = vec2(p.uv + g * 0.12)
  const over2 = overhead.sample(up)
  const b = bed.sample(vec2(p.uv + bend * 58), over2.a * 1.1)
  const depth = b.a
  // The koi lie nearer the surface than the bottom does, so even the steepest ripple moves the sight of them only
  // about five units.
  const ko = koiLayer.sample(vec2(p.uv + bend * 48 * min(1, 0.1 / max(length(g), 0.001))))
  // One sun. Shadows fall away from it onto the bottom, farther and softer the deeper the bottom lies:
  // down and right by day, down and left under the moon. Pads throw the crisp ones, koi the soft ones.
  const fall = vec2((mix(vec2(-30, -40), vec2(38, -52), m) * u) / size)
  const kSh = koiLayer.sample(vec2(p.uv + bend * 58 - fall * (0.7 + depth)), 1.5 + 2.4 * depth).a
  // What floats is not nailed down: a passing slope carries pads and leaves a few points with it.
  const tp = top.sample(vec2(p.uv + bend * 16))
  const tSh = top.sample(vec2(p.uv + bend * 42 - fall * (0.3 + 1.1 * depth)), 1.4 + 2 * depth).a
  const shadow = 1 - (1 - 0.72 * (1 - 0.45 * depth) * kSh) * (1 - 0.8 * tSh)
  // The boughs overhead shade the water in broad soft patches; the sun and its net of light fail there.
  const shade = over2.g
  const sunlit = (1 - shadow) * (1 - 0.86 * shade)
  // By night a lantern on the left bank throws a warm pool across the water; beyond it there is only the moon.
  const toLamp = vec2((p.point - vec2(-0.03, 0.52) * size) / (400 * u))
  const lamp = (1 - m) / (1 + dot(toLamp, toLamp) * 1.6)
  // Caustics: light gathers where the surface curves like a lens. Only the slow swell draws the net, so a
  // pointer moved hard to and fro cannot make it flicker.
  const causAt = 1 + (net - 1) * max(1.5 - 1.7 * depth, 0.14) * mix(0.15, 1, m)
  // Sun is warm and about two stops over the cool shade.
  const sun = vec3(mix(vec3(0.2, 0.25, 0.4), vec3(1.02, 0.9, 0.68), m) + vec3(1, 0.6, 0.26) * lamp)
  const amb = vec3(mix(vec3(0.07, 0.095, 0.16), vec3(0.3, 0.37, 0.43), m) * (1 - 0.2 * shade))
  const light = vec3(amb + sun * causAt * sunlit)
  const clear = exp(-depth * mix(2.3, 1.75, m))
  const murk = vec3(mix(vec3(0.012, 0.03, 0.055), vec3(0.045, 0.13, 0.095), m) * (0.62 + 0.38 * sunlit) * (0.94 + 0.06 * net))
  let col = mix(murk, vec3(b.rgb * light), clear)
  // Koi, lit from above, with the net of light playing over their backs and the shade of pads and boughs on them.
  const koiLight = vec3((amb * 1.15 + sun * (0.3 + 0.7 * causAt) * (1 - 0.6 * tSh) * (1 - 0.7 * shade)) * mix(0.8, 1, m))
  col = vec3(col * (1 - ko.a) + ko.rgb * koiLight)
  // The surface itself is seen only by what it mirrors, and from straight above calm water mirrors little:
  // a faint pale sky over the middle of the pond, broken by cloud, and the dark of boughs by the banks. A
  // slope mirrors far more, so every ripple carries a band of sky. The mirror is looked up only a little way
  // along the slope and its borders are broad, so a pointer moved hard to and fro cannot swing any spot's
  // brightness far.
  const open = over2.r
  const sky = vec3(mix(vec3(0.13, 0.18, 0.3), vec3(0.66, 0.8, 0.93), m) * (0.78 + 0.44 * over2.b))
  const boughs = mix(vec3(0.015, 0.025, 0.045), vec3(0.07, 0.11, 0.07), m)
  // The slope's share is signed: the flank of a ripple that faces the light carries sky, the other is clear.
  const facing = max(dot(g, SUN), 0)
  const wet = (1 - tp.a) * clamp(0.02 + 0.07 * open * (0.3 + over2.b) + 0.85 * facing, 0, 0.26)
  col = vec3(col * (1 - 0.5 * wet) + mix(boughs, sky, open) * wet)
  // Each ripple also has a face toward the light and a face away from it.
  const tilt = dot(live, SUN) * 18
  const flank = (tilt / (1 + abs(tilt))) * (1 - tp.a)
  col = vec3(col + mix(vec3(0.03, 0.038, 0.06), vec3(0.03, 0.033, 0.03), m) * flank * (1.15 - col.g))
  // Pads, reeds, stones and leaves sit on top, in the air; by night they lose most of their color.
  const topLight = vec3(amb * 1.25 + sun * 0.8 * (1 - 0.82 * shade))
  const topC = mix(vec3(dot(tp.rgb, vec3(0.3, 0.6, 0.1))), tp.rgb, mix(0.45, 1, m))
  col = vec3(col * (1 - tp.a) + topC * topLight)
  // The camera: light falls off away from the sun's side and toward the corners, color is a little spent,
  // and a fixed fine grain lies over everything.
  const off = vec2(p.uv - 0.5)
  col = vec3(col * (1 + 0.09 * dot(off, SUN) - 0.1 * dot(off, off)))
  col = mix(vec3(dot(col, vec3(0.3, 0.6, 0.1))), col, 0.9)
  // A soft shoulder, as film has: sunlit stones and white koi come close to clipping and do not clip.
  col = clamp(vec3((col * 1.36) / (1 + 0.38 * col)), 0, 1)
  // Then a gentle S, so deep water and the shade under pads go near black and sunlit things stand out.
  col = mix(col, vec3(col * col * (3 - 2 * col)), 0.28)
  col = vec3(col + (grain.sample(vec2(p.pixel / 128)).r - 0.5) * 0.028)
  return vec4(col, 1)
})

// The floating leaves, one quad each, turned in the vertex stage.
const leaves = shapes(
  { count: 6, instances: 4, cover: 0.03, draw: 'triangles' },
  (v, i) => {
    const u = unitOf()
    const s = afloat.at(vec2(i, 0))
    const r = afloat.at(vec2(i, 1))
    const sx = pick6([-1, 1, -1, 1, 1, -1], v)
    const sy = pick6([-1, -1, 1, -1, 1, 1], v)
    const half = 26 * u * (0.25 + 0.75 * smoothstep(0, 0.4, r.z))
    const ca = cos(r.x)
    const sa = sin(r.x)
    const w = vec2(s.xy + vec2(sx * ca - sy * sa, sx * sa + sy * ca) * half)
    return { at: vec2((w / size) * 2 - 1), a: vec4(sx * 26, sy * 26, i, 0) }
  },
  s => {
    const m = modeBuf.at(vec2(0, 0)).r
    const id = floor(s.a.z + 0.5)
    const d = vec2(s.a.x, s.a.y)
    const R = 17 - id
    const rr = length(d)
    const a = atan(d.y, d.x)
    const lobe = abs(cos(a * 2.5))
    const edge = R * (0.3 + 0.7 * pow(lobe, 1.1)) * (0.62 + 0.38 * cos(a)) * (1 + 0.05 * sin(a * 24))
    const mk = smoothstep(edge, edge - 1.3, rr)
    const vein = pow(lobe, 26) * smoothstep(0.08, 0.4, rr / R)
    const hue = pick4([0.5, 0.15, 0.85, 0.3], id)
    const warm = mix(mix(vec3(0.74, 0.15, 0.1), vec3(0.9, 0.4, 0.1), smoothstep(0, 0.5, hue)), vec3(0.93, 0.68, 0.18), smoothstep(0.5, 1, hue))
    const lit = mix(vec3(0.3, 0.4, 0.62), vec3(1, 1, 1), m)
    const c = vec3(mix(warm, vec3(0.45, 0.33, 0.2), 0.4) * (0.8 + 0.34 * lattice(vec2(d / 6 + id * 7), 51)) * (1.06 - 0.26 * rr / R) * (1 + 0.3 * vein) * lit)
    // The leaf dents the water: a soft dark foot all round it.
    const foot = smoothstep(edge + 6, edge - 1, rr) * 0.25 * (1 - mk)
    return vec4(c * mk, mk + foot)
  },
)

// By night two lights lie on the water as broken columns of glitter: the moon's, cool, on the right, and
// the lantern's, warm, reaching out from the left bank. The swell breaks them into soft moving glints.
// One quad each, so the rest of the picture does not pay for them.
const lights = shapes(
  { count: 6, instances: 2, cover: 0.13, draw: 'triangles', blend: 'add' },
  (v, i) => {
    const u = unitOf()
    const sx = pick6([-1, 1, -1, 1, 1, -1], v)
    const sy = pick6([-1, -1, 1, -1, 1, 1], v)
    const half = i < 0.5 ? vec2(64, 230) : vec2(260, 52)
    const mid = i < 0.5 ? vec2(MOON_AT * size) : vec2(vec2(0.07, 0.52) * size)
    const w = vec2(mid + vec2(sx * half.x, sy * half.y) * u)
    const night = 1 - modeBuf.at(vec2(0, 0)).r
    return { at: vec2((w / size) * 2 - 1), a: vec4(sx * half.x, sy * half.y, i, night), hide: night < 0.5 }
  },
  s => {
    // A glint shows wherever the swell tilts the water just so toward the light, so the glints are soft
    // patches that come and go and drift with the swell.
    const rest = glim.sample(s.uv)
    const tiltA = vec2(vec2(rest.r - 0.5, rest.g - 0.5) * 0.5 - vec2(0.03, 0.045))
    const tiltB = vec2(vec2(rest.r - 0.5, rest.g - 0.5) * 0.5 + vec2(0.05, -0.015))
    const threads = exp(-dot(tiltA, tiltA) * 1400) + exp(-dot(tiltB, tiltB) * 1400)
    const isMoon = s.a.z < 0.5 ? 1 : 0
    const along = mix(s.a.x, s.a.y, isMoon)
    const across = mix(s.a.y, s.a.x, isMoon)
    const glow = exp(-pow(across / mix(30, 34, isMoon), 2) - pow(along / mix(130, 115, isMoon), 2)) * (0.12 + 0.75 * threads) * mix(1, 1.15, isMoon)
    return vec4(mix(vec3(0.75, 0.48, 0.2), vec3(0.62, 0.68, 0.8), isMoon) * glow * s.a.w, 0)
  },
)

// Water striders. What shows of one from above is a small brown smudge and, beside it, the four round
// shadows its feet press into the light on the bottom.
const striders = shapes(
  { count: 1, instances: 2, cover: 0.012, draw: 'points' },
  (v, i) => {
    const s = cast.at(vec2(i, 0))
    return { at: vec2((s.xy / size) * 2 - 1), size: clamp((34 * unitOf()) / px, 1, 64) }
  },
  s => {
    const dv = vec2((s.coord.x - 0.5) * 34, (s.coord.y - 0.5) * 34)
    const body = smoothstep(1.6, 0.4, length(vec2(dv.x * 0.3 + 1.2, dv.y + 1)))
    const foot = vec2(abs(dv.x - 4) - 7.5, abs(dv.y - 4.5) - 5)
    const dimples = smoothstep(3.4, 1.2, length(foot))
    return vec4(vec3(0.16, 0.1, 0.05) * body * 0.7, clamp(0.7 * body + 0.3 * dimples, 0, 1))
  },
)

// Fireflies drift over the margins at night, each on a slow loop of its own, glowing and fading.
const flies = shapes(
  { count: 1, instances: 5, cover: 0.02, draw: 'points', blend: 'add' },
  (v, i) => {
    const f = cast.at(vec2(i + 2, 0))
    const night = 1 - modeBuf.at(vec2(0, 0)).r
    return { at: vec2((f.xy / size) * 2 - 1), size: clamp((44 * unitOf()) / px, 1, 64), a: vec4(f.z * night, 0, 0, 0), hide: night < 0.5 }
  },
  s => {
    const d = length(vec2(s.coord - 0.5)) * 2
    const g = s.a.x * (clamp(1.6 - d * 11, 0, 1) * 0.8 + (0.16 / (1 + d * d * 6)) * smoothstep(1, 0.6, d))
    return vec4(vec3(0.8, 1, 0.4) * g, 0)
  },
)

export default shader({ fps: 60, passes: [modeBuf, bed, top, overhead, grain, mood, plops, fish, food, cast, stir, wave, afloat, glim, koiLayer, koi, fry, view, lights, leaves, pellets, striders, flies] })
