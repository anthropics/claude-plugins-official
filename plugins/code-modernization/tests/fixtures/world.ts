import type { On, RenderElement, RenderNode } from 'claude-code'

/**
 * The world beneath the plugin, in memory: a file tree the `$.fs` calls are
 * answered from, and a record of everything the plugin asked the engine to do.
 */
export type World = {
  files: Map<string, string>
  mtimes: Map<string, number>
  writes: { path: string; text: string }[]
  opened: { id: string; focus: boolean }[]
  closed: string[]
  logs: string[]
  toasts: string[]
  statuses: (string | undefined)[]
  blits: number
  invalidations: number
  /** How many of the next opens the engine holds back undrawn (unasked, on a terminal too narrow to dock a pane). */
  unplaced: number
  fills: string[]
  commands: string[]
  aborted: string[]
  /** Every path the plugin asked the file system about, as it arrived. */
  asked: string[]
  /** Replaces a file's text as something outside the engine would, moving its mtime on. */
  put: (path: string, text: string) => void
}

export const CWD = '/work'

const relOf = (path: string) => (path.startsWith(`${CWD}/`) ? path.slice(CWD.length + 1) : path.replace(/^\.\//, ''))

/** Seats the in-memory world beneath the plugin. */
export function worldOf(
  on: On,
  files: Readonly<Record<string, string>>,
  env: Readonly<Record<string, string>> = {},
  /** Paths (relative to the working directory) that are symbolic links to a directory: the engine lists a link as `other`. */
  links: readonly string[] = [],
): World {
  let tick = 1_000

  const world: World = {
    files: new Map(Object.entries(files)),
    mtimes: new Map(Object.keys(files).map(path => [path, 1_000])),
    writes: [],
    opened: [],
    closed: [],
    logs: [],
    toasts: [],
    statuses: [],
    blits: 0,
    invalidations: 0,
    unplaced: 0,
    fills: [],
    commands: [],
    aborted: [],
    asked: [],
    put: (path, text) => {
      tick += 1_000
      world.files.set(path, text)
      world.mtimes.set(path, tick)
    },
  }

  const isDir = (path: string) => [...world.files.keys()].some(file => file.startsWith(`${path}/`))

  on('fs.read', ($, e) => {
    world.asked.push(`read ${e.path}`)

    const text = world.files.get(relOf(e.path))

    return text === undefined ? { deny: `ENOENT: ${e.path}` } : { value: text }
  })

  on('fs.exists', ($, e) => {
    world.asked.push(`exists ${e.path}`)

    return { value: world.files.has(relOf(e.path)) || isDir(relOf(e.path)) }
  })

  on('fs.stat', ($, e) => {
    const path = relOf(e.path)
    const text = world.files.get(path)

    if (text !== undefined) {
      return { value: { kind: 'file' as const, size: text.length, mtimeMs: world.mtimes.get(path) ?? 0 } }
    }

    return isDir(path) ? { value: { kind: 'dir' as const, size: 0, mtimeMs: 0 } } : { deny: `ENOENT: ${e.path}` }
  })

  on('fs.list', ($, e) => {
    world.asked.push(`list ${e.path}`)

    const dir = relOf(e.path)
    const names = new Map<string, 'file' | 'dir'>()

    for (const file of world.files.keys()) {
      if (!file.startsWith(`${dir}/`)) {
        continue
      }

      const rest = file.slice(dir.length + 1)
      const name = rest.split('/')[0] ?? ''

      names.set(name, rest.includes('/') ? 'dir' : 'file')
    }

    return {
      value: [...names.entries()].sort().map(([name, kind]) => {
        const isLink = links.includes(dir === '' ? name : `${dir}/${name}`)

        return {
          name,
          kind: isLink ? ('other' as const) : kind,
          size: kind === 'file' ? (world.files.get(`${dir}/${name}`)?.length ?? 0) : 0,
          isLink,
        }
      }),
    }
  })

  on('fs.write', ($, e) => {
    world.writes.push({ path: relOf(e.path), text: e.text })
    world.put(relOf(e.path), e.text)

    return { value: undefined }
  })

  on('env.get', ($, e) => ({ value: env[e.name] }))
  on('store.get', () => ({ value: undefined }))
  on('store.set', () => ({ value: undefined }))

  on('command.register', ($, e) => {
    world.commands.push(e.name)

    return { value: { command: e.name } }
  })

  on('ui.open', ($, e) => {
    world.opened.push({ id: e.id, focus: e.focus === true })

    if (world.unplaced > 0) {
      world.unplaced -= 1

      return { value: { isPlaced: false, reason: 'unasked below 144 columns (120 now): press the pane\'s button or type /modernize-panel' } } as never
    }

    return { value: { isPlaced: true } } as never
  })

  on('ui.close', ($, e) => {
    world.closed.push(e.id)

    return { value: undefined }
  })

  on('ui.log', ($, e) => {
    world.logs.push(e.text)

    return { value: undefined }
  })

  on('ui.toast', ($, e) => {
    world.toasts.push(e.text)

    return { value: undefined }
  })

  on('ui.status', ($, e) => {
    world.statuses.push(e.text)

    return { value: undefined }
  })

  on('ui.invalidate', () => {
    world.invalidations += 1

    return { value: undefined }
  })

  on('ui.blit', () => {
    world.blits += 1

    return { value: {} }
  })

  on('prompt.fill', ($, e) => {
    world.fills.push(e.text)

    return { isFilled: true }
  })

  on('turn.abort', ($, e) => {
    world.aborted.push(e.turnId)

    return { value: undefined }
  })

  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('prompt.submit', ($, e) => ({ text: e.text, ...(e.context !== undefined && { context: e.context }) }))

  return world
}

/** Every string a drawn tree holds, in drawing order. */
export function stringsOf(node: RenderNode | RenderElement | null | undefined): string[] {
  if (node === null || node === undefined) {
    return []
  }

  if (typeof node === 'string') {
    return [node]
  }

  const own: string[] = []
  const props = (node as { props?: Record<string, unknown> }).props

  if (node.type === 'Button' && typeof props?.label === 'string') {
    own.push(props.label)
  }

  if (node.type === 'Code' && typeof props?.source === 'string') {
    own.push(props.source)
  }

  if (node.type === 'Input') {
    own.push(`${typeof props?.label === 'string' ? props.label : ''}: ${typeof props?.value === 'string' ? props.value : ''}`)
  }

  const children = (node as { children?: readonly RenderNode[] }).children ?? []

  return [...own, ...children.flatMap(child => stringsOf(child))]
}

/** A drawn tree as one string. */
export const textOf = (node: RenderNode | RenderElement | null | undefined): string => stringsOf(node).join('')

/** Every element of `type` in a drawn tree. */
export function elementsOf(node: RenderNode | RenderElement | null | undefined, type: string): RenderElement[] {
  if (node === null || node === undefined || typeof node === 'string') {
    return []
  }

  const children = (node as { children?: readonly RenderNode[] }).children ?? []

  return [...(node.type === type ? [node] : []), ...children.flatMap(child => elementsOf(child, type))]
}

/** How many terminal rows a drawn tree takes, counting each Text as one row (the pane wraps its own). */
export function rowsOf(tree: unknown): number {
  const node = tree as { type?: string; props?: Record<string, unknown>; children?: unknown[] } | string | null | undefined

  if (node === null || node === undefined || typeof node === 'string') {
    return 0
  }

  if (node.type === 'Text' || node.type === 'Button' || node.type === 'Input') {
    return 1
  }

  if (node.type === 'Raster') {
    return Number(node.props?.rows ?? 0)
  }

  if (node.type === 'Code') {
    return String(node.props?.source ?? '').split('\n').length
  }

  const kids = (node.children ?? []).map(rowsOf)
  const isRow = node.type === 'Box' && node.props?.flexDirection !== 'column'
  const gap = !isRow ? Number(node.props?.rowGap ?? 0) * Math.max(0, kids.filter(count => count > 0).length - 1) : 0
  const inner = isRow ? Math.max(0, ...kids) : kids.reduce((a, b) => a + b, 0)

  return inner + gap + Number(node.props?.marginTop ?? 0)
}
