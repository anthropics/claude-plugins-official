import { baseName, norm } from '../paths'

/**
 * `analysis/<system>/topology.json`, read into the few shapes the live pane uses.
 *
 * The file is written by an agent, so every field is treated as optional and
 * of unknown shape: anything that does not fit is dropped, never thrown on.
 */

export type TopoNode = {
  id: string
  name: string
  /** `module`, `datastore`, `screen`, or whatever the map stage wrote. */
  kind: string
  /** Lines of code; 0 when the map gave none. */
  loc: number
  /** Source file relative to `legacy/<system>/`, when the node is one file. */
  file?: string
  /** The name of the domain (first ancestor of kind `domain`) it sits under. */
  domain?: string
  /** The language the map recorded for it, as written (`cobol`, `java`, `php`). */
  language?: string
}

export type TopoEdge = { source: string; target: string; kind: string }

export type TopoFlow = {
  name: string
  persona?: string
  steps: { label: string; nodes: string[] }[]
}

export type Topology = {
  system: string
  nodes: TopoNode[]
  /** Nodes that are code (`kind: module`, or any leaf with a file and loc). */
  modules: TopoNode[]
  domains: { name: string; modules: TopoNode[] }[]
  edges: TopoEdge[]
  entryPoints: Set<string>
  deadEnds: Set<string>
  flows: TopoFlow[]
  byId: Map<string, TopoNode>
  /** Lower-cased base name of a node's file, to the nodes that have it. */
  byFileBase: Map<string, TopoNode[]>
}

const str = (value: unknown): string | undefined =>
  typeof value === 'string' && value !== '' ? value : undefined

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const list = (value: unknown): unknown[] => (Array.isArray(value) ? value : [])

function walk(
  raw: unknown,
  domain: string | undefined,
  out: TopoNode[],
  depth: number,
): void {
  if (!isRecord(raw) || depth > 12) {
    return
  }

  const id = str(raw.id) ?? str(raw.name)

  if (id === undefined) {
    return
  }

  const kind = str(raw.kind) ?? 'node'
  const name = str(raw.name) ?? id
  const children = list(raw.children)
  const here = kind === 'domain' ? name : domain
  const loc = typeof raw.loc === 'number' && raw.loc > 0 ? raw.loc : 0
  const file = str(raw.file)
  const language = str(raw.language)

  if (children.length === 0 || kind === 'module') {
    out.push({
      id,
      name,
      kind,
      loc,
      ...(file !== undefined && { file: norm(file) }),
      ...(here !== undefined && { domain: here }),
      ...(language !== undefined && { language }),
    })
  }

  for (const child of children) {
    walk(child, here, out, depth + 1)
  }
}

/** Parses topology.json; null when the text is not a usable topology. */
export function parseTopology(text: string): Topology | null {
  let raw: unknown

  try {
    raw = JSON.parse(text)
  } catch {
    return null
  }

  if (!isRecord(raw)) {
    return null
  }

  const nodes: TopoNode[] = []

  if (isRecord(raw.root)) {
    walk(raw.root, undefined, nodes, 0)
  }

  for (const flat of list(raw.nodes)) {
    walk(flat, undefined, nodes, 0)
  }

  if (nodes.length === 0) {
    return null
  }

  const byId = new Map<string, TopoNode>()

  for (const node of nodes) {
    if (!byId.has(node.id)) {
      byId.set(node.id, node)
    }
  }

  const unique = [...byId.values()]

  const modules = unique.filter(
    node =>
      node.kind === 'module' ||
      (node.file !== undefined && node.loc > 0 && node.kind !== 'datastore'),
  )

  const byDomain = new Map<string, TopoNode[]>()

  for (const node of modules) {
    const key = node.domain ?? 'Other'
    const bucket = byDomain.get(key) ?? []

    bucket.push(node)
    byDomain.set(key, bucket)
  }

  const byFileBase = new Map<string, TopoNode[]>()

  for (const node of unique) {
    if (node.file === undefined) {
      continue
    }

    const key = baseName(node.file).toLowerCase()
    const bucket = byFileBase.get(key) ?? []

    bucket.push(node)
    byFileBase.set(key, bucket)
  }

  const edges: TopoEdge[] = []

  for (const edge of list(raw.edges)) {
    if (!isRecord(edge)) {
      continue
    }

    const source = str(edge.source) ?? str(edge.from)
    const target = str(edge.target) ?? str(edge.to)

    if (source !== undefined && target !== undefined) {
      edges.push({ source, target, kind: str(edge.kind) ?? 'uses' })
    }
  }

  const flows: TopoFlow[] = []

  for (const flow of list(raw.flows)) {
    if (!isRecord(flow)) {
      continue
    }

    const name = str(flow.name)

    if (name === undefined) {
      continue
    }

    const persona = str(flow.persona)

    flows.push({
      name,
      ...(persona !== undefined && { persona }),
      steps: list(flow.steps)
        .filter(isRecord)
        .map(step => ({
          label: str(step.label) ?? '',
          nodes: list(step.nodes).filter(
            (node): node is string => typeof node === 'string',
          ),
        })),
    })
  }

  const ids = (value: unknown) =>
    new Set(list(value).filter((id): id is string => typeof id === 'string'))

  return {
    system: str(raw.system) ?? '',
    nodes: unique,
    modules,
    domains: [...byDomain.entries()].map(([name, members]) => ({
      name,
      modules: members,
    })),
    edges,
    entryPoints: ids(raw.entryPoints),
    deadEnds: ids(raw.deadEnds),
    flows,
    byId,
    byFileBase,
  }
}

/**
 * The topology node a legacy file belongs to: by its path relative to
 * `legacy/<system>/` when the map recorded one, else by base name alone.
 */
export function nodeOfFile(topo: Topology, fileRel: string): TopoNode | null {
  const wanted = norm(fileRel)
  const candidates = topo.byFileBase.get(baseName(wanted).toLowerCase()) ?? []

  return (
    candidates.find(node => node.file === wanted) ??
    candidates.find(node => wanted.endsWith(node.file ?? '\0')) ??
    candidates[0] ??
    null
  )
}
