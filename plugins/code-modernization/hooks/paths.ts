/**
 * Path helpers. A hooks module has no `path` module: these are the few
 * string operations the hooks need, all over forward-slash paths.
 */

/** Forward slashes, no doubled separators, no trailing slash (root stays `/`). */
export function norm(path: string): string {
  const clean = path.replace(/\\/g, '/').replace(/\/{2,}/g, '/')

  return clean.length > 1 && clean.endsWith('/') ? clean.slice(0, -1) : clean
}

/** Resolves `.` and `..` segments lexically; absolute stays absolute. */
export function resolveDots(path: string): string {
  const isAbsolute = path.startsWith('/')
  const out: string[] = []

  for (const part of norm(path).split('/')) {
    if (part === '' || part === '.') {
      continue
    }

    if (part === '..') {
      if (out.length > 0 && out.at(-1) !== '..') {
        out.pop()
      } else if (!isAbsolute) {
        out.push('..')
      }

      continue
    }

    out.push(part)
  }

  return (isAbsolute ? '/' : '') + out.join('/')
}

/** `path` made absolute against `cwd` when it is relative. */
export function absOf(cwd: string, path: string): string {
  return resolveDots(path.startsWith('/') ? path : `${norm(cwd)}/${path}`)
}

/**
 * `path` relative to `cwd` when it lies inside it, else null. Both may be
 * given with or without the macOS `/private` prefix the engine sometimes adds.
 */
export function relTo(cwd: string, path: string): string | null {
  const strip = (p: string) => p.replace(/^\/private(?=\/(?:tmp|var)\/)/, '')
  const base = strip(norm(cwd))
  const full = strip(absOf(cwd, path))

  if (full === base) {
    return ''
  }

  return full.startsWith(`${base}/`) ? full.slice(base.length + 1) : null
}

/** True when relative path `rel` is `dir` or lies beneath it. */
export function isUnder(rel: string, dir: string): boolean {
  const d = norm(dir)

  return rel === d || rel.startsWith(`${d}/`)
}

/** The last segment. */
export function baseName(path: string): string {
  const parts = norm(path).split('/')

  return parts.at(-1) ?? ''
}

/** The last segment without its final extension. */
export function stemOf(path: string): string {
  const base = baseName(path)
  const dot = base.lastIndexOf('.')

  return dot > 0 ? base.slice(0, dot) : base
}

/** Everything but the last segment (`''` for a bare name). */
export function dirName(path: string): string {
  const parts = norm(path).split('/')

  parts.pop()

  return parts.join('/')
}

/** Joins segments with single slashes. */
export function join(...parts: string[]): string {
  return norm(parts.filter(part => part !== '').join('/'))
}
