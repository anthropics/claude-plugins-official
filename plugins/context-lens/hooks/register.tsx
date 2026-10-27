import { atom, read, update } from 'claude-code'
import type { Register, RenderChildren } from 'claude-code'

import type { Category, Filter, Group, Item, Kind, Snap, View } from '../types'

const PANE = 'context-lens'
const MAX_SNAPS = 60
const MAX_BLOB = 400_000
const SNIPPET = 60

const snaps = atom({ plugin: 'context-lens', key: 'snaps' } as const, [] as Snap[])
const view = atom({ plugin: 'context-lens', key: 'view' } as const, {
  at: null,
  filter: 'all',
  query: '',
  open: null,
  line: 0,
  collapsed: ['system', 'tools'],
} as View)
const reminderTypes = atom({ plugin: 'context-lens', key: 'reminderTypes' } as const, {} as Record<string, string>)
const bandHidden = atom({ plugin: 'context-lens', key: 'bandHidden' } as const, false)
const BLOB = { plugin: 'context-lens', key: 'blob' } as const
const ITEMS = { plugin: 'context-lens', key: 'items' } as const
const MAX_REMINDER_TYPES = 500

type Section = { id: string; text: string; scope: string }
type ApiBlock = { type: string; [field: string]: unknown }
type ApiMessage = { role: 'user' | 'assistant'; content: ApiBlock[] }
type ToolRow = { name: string; description: string; mcp: boolean }

// Blobs are content-addressed and never change, so a module cache is safe across draws.
const blobCache = new Map<string, string>()
const written = new Set<string>()
const sectionsByModel = new Map<string, Section[]>()
const deferred = new Map<string, boolean>()
let lastSections: Section[] = []

const FILTERS: { id: Filter; label: string; hotkey: string }[] = [
  { id: 'all', label: 'All', hotkey: '1' },
  { id: 'system', label: 'System', hotkey: '2' },
  { id: 'tools', label: 'Tools', hotkey: '3' },
  { id: 'reminders', label: 'Reminders', hotkey: '4' },
  { id: 'chat', label: 'Chat', hotkey: '5' },
  { id: 'io', label: 'Tool I/O', hotkey: '6' },
  { id: 'new', label: 'New', hotkey: '7' },
]

const GROUP_TITLES: Record<Group, string> = {
  system: 'System prompt',
  tools: 'Tools',
  messages: 'Messages',
}

const KIND_TAGS: Record<Kind, string> = {
  section: 'section',
  tool: 'tool',
  prompt: 'prompt',
  reminder: 'reminder',
  assistant: 'reply',
  thinking: 'thinking',
  tool_use: 'tool call',
  tool_result: 'result',
  media: 'media',
  other: 'block',
}

const CATEGORY_COLORS: Record<string, string> = {
  'System prompt': '#d97757',
  'System tools': '#9a9a9a',
  'MCP tools': '#56b6c2',
  'Custom agents': '#98c379',
  'Memory files': '#c678dd',
  Skills: '#e5c07b',
  Messages: '#61afef',
}

export function hashOf(text: string): string {
  let h = 0x811c9dc5
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i)
    h = Math.imul(h, 0x01000193)
  }
  return 'b' + text.length.toString(36) + '_' + (h >>> 0).toString(36)
}

export function tokens(chars: number): number {
  return Math.max(1, Math.round(chars / 4))
}

/** An item's size: Claude Code's own count where the text itself isn't available, else about four characters a token. */
export function itemTokens(item: Item): number {
  return item.estTokens ?? tokens(item.chars)
}

const SYSTEM_UNREPORTED =
  "This session didn't hand its system prompt sections to mods, so the text can't be shown here. The size is Claude Code's own count, as /context's System prompt row reports it."

export function fmtTokens(n: number): string {
  if (n >= 100_000) return Math.round(n / 1000) + 'k'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function firstLine(text: string): string {
  const line = text.split('\n').find(l => l.trim() !== '') ?? ''
  return line.replace(/^#+\s*/, '').trim()
}

function stripReminder(text: string): string | null {
  const m = /^\s*<system-reminder>\n?([\s\S]*?)\n?<\/system-reminder>\s*$/.exec(text)
  return m ? (m[1] ?? '') : null
}

function describeInput(name: string, input: Record<string, unknown>): string {
  const pick = ['file_path', 'command', 'pattern', 'url', 'query', 'description', 'prompt', 'path']
  for (const key of pick) {
    const v = input[key]
    if (typeof v === 'string' && v !== '') {
      const short = key === 'file_path' || key === 'path' ? v.split('/').slice(-2).join('/') : v
      return name + ' ' + short.replace(/\s+/g, ' ')
    }
  }
  return name
}

function resultText(content: unknown): string {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content
      .map(b => {
        const block = b as ApiBlock
        if (block.type === 'text') return String(block.text ?? '')
        return '[' + block.type + ' block]'
      })
      .join('\n')
  }
  return content === undefined ? '' : JSON.stringify(content, null, 2)
}

export function buildItems(
  sections: readonly Section[],
  tools: readonly ToolRow[],
  messages: readonly ApiMessage[],
  isDeferred: (name: string) => boolean,
  prevItems: readonly Item[] | undefined,
  systemTokens = 0,
): { items: Item[]; texts: Map<string, string> } {
  const items: Item[] = []
  const texts = new Map<string, string>()
  const before = new Set(prevItems?.map(i => i.key) ?? [])
  let block = 0
  const add = (group: Group, kind: Kind, label: string, sub: string, text: string, extra: Partial<Item> = {}) => {
    const hash = hashOf(text)
    // Position plus content, so a repeated block (the same command run twice) still counts as new.
    const key = group + ':' + (extra.msg ?? label) + ':' + block++ + ':' + hash
    const kept = text.length > MAX_BLOB ? text.slice(0, MAX_BLOB) + '\n[context-lens kept the first 400k characters]' : text
    texts.set(hash, kept)
    items.push({
      id: String(items.length),
      group,
      kind,
      label: label.slice(0, 200) || '(empty)',
      sub,
      hash,
      key,
      chars: text.length,
      isNew: prevItems === undefined ? true : !before.has(key),
      ...extra,
    })
  }

  for (const s of sections) add('system', 'section', s.id, s.scope, s.text)
  if (sections.length === 0 && systemTokens > 0) {
    add('system', 'section', 'system prompt (text not reported)', 'n/a', SYSTEM_UNREPORTED, { estTokens: systemTokens })
  }
  block = 0
  for (const t of tools) {
    add('tools', 'tool', t.name, isDeferred(t.name) ? 'deferred' : t.mcp ? 'mcp' : 'built-in', t.description)
  }

  const toolNames = new Map<string, string>()
  messages.forEach((m, index) => {
    const msg = index + 1
    block = 0
    for (const b of m.content) {
      if (b.type === 'text') {
        const text = String(b.text ?? '')
        const inner = m.role === 'user' ? stripReminder(text) : null
        if (inner !== null) add('messages', 'reminder', firstLine(inner), m.role, text, { msg, inner: hashOf(inner) })
        else add('messages', m.role === 'user' ? 'prompt' : 'assistant', firstLine(text), m.role, text, { msg })
      } else if (b.type === 'thinking') {
        add('messages', 'thinking', firstLine(String(b.thinking ?? '')), m.role, String(b.thinking ?? ''), { msg })
      } else if (b.type === 'redacted_thinking') {
        add('messages', 'thinking', 'redacted thinking', m.role, '[redacted thinking block]', { msg })
      } else if (b.type === 'tool_use') {
        const name = String(b.name ?? 'tool')
        const input = (b.input ?? {}) as Record<string, unknown>
        toolNames.set(String(b.id ?? ''), describeInput(name, input))
        add('messages', 'tool_use', describeInput(name, input), m.role, JSON.stringify(input, null, 2), { msg })
      } else if (b.type === 'tool_result') {
        const text = resultText(b.content)
        const of = toolNames.get(String(b.tool_use_id ?? '')) ?? 'tool'
        const lines = text.split('\n').length
        const label = of + (b.is_error === true ? ' (error)' : ' → ' + lines + (lines === 1 ? ' line' : ' lines'))
        add('messages', 'tool_result', label, m.role, text, { msg })
      } else if (b.type === 'image' || b.type === 'document') {
        add('messages', 'media', b.type, m.role, '[' + b.type + ' block]', { msg })
      } else {
        add('messages', 'other', b.type, m.role, JSON.stringify(b, null, 2), { msg })
      }
    }
  })

  return { items, texts }
}

async function record(
  $: any,
  turnId: string,
  step: number,
  model: string,
  messages: readonly ApiMessage[],
  tools: readonly ToolRow[],
): Promise<void> {
  const list = await read($, snaps)
  const prev = list.at(-1)
  const prevItems = prev === undefined ? undefined : ((await $.state.get({ ...ITEMS, id: prev.id })).value ?? [])
  let categories: Category[] = []
  let totalTokens = 0
  let window = 0
  try {
    const usage = await $.session.usage({ breakdown: 'summary' })
    window = usage.context.window
    const bd = usage.context.breakdown
    if (bd) {
      categories = bd.categories.map((c: Category) => ({ name: c.name, tokens: c.tokens, kind: c.kind }))
      totalTokens = bd.totalTokens
      window = bd.rawMaxTokens || window
    } else {
      totalTokens = usage.context.tokens ?? 0
    }
  } catch {
    totalTokens = 0
  }

  const sections = sectionsByModel.get(model) ?? lastSections
  const systemTokens = categories.find(c => c.name === 'System prompt')?.tokens ?? 0
  const { items, texts } = buildItems(sections, tools, messages, name => deferred.get(name) === true, prevItems, systemTokens)
  for (const [hash, text] of texts) {
    if (written.has(hash)) continue
    await $.state.set({ ...BLOB, id: hash }, text)
    written.add(hash)
    blobCache.set(hash, text)
  }
  if (totalTokens === 0) totalTokens = items.reduce((n, i) => n + itemTokens(i), 0)

  const fresh = items.filter(i => i.isNew)
  const latest = fresh.filter(i => i.group === 'messages').at(-1)
  const seq = (prev?.seq ?? 0) + 1
  const snap: Snap = {
    id: seq + ':' + turnId + ':' + step,
    seq,
    turnId,
    turn: prev === undefined ? 1 : prev.turnId === turnId ? prev.turn : prev.turn + 1,
    step,
    model,
    at: await $.clock.now(),
    window,
    categories,
    totalTokens,
    itemCount: items.length,
    newCount: fresh.length,
    newTokens: fresh.reduce((n, i) => n + itemTokens(i), 0),
    latest: latest === undefined ? undefined : KIND_TAGS[latest.kind] + ' ' + latest.label,
  }
  await $.state.set({ ...ITEMS, id: snap.id }, items)
  const kept = [...list, snap]
  const keep = new Set(items.map(i => i.hash))
  for (const old of kept.slice(0, Math.max(0, kept.length - MAX_SNAPS))) {
    // Release what only the pruned request carried; the newest request's text stays.
    for (const item of (await $.state.get({ ...ITEMS, id: old.id })).value ?? []) {
      if (keep.has(item.hash) || !written.has(item.hash)) continue
      await $.state.set({ ...BLOB, id: item.hash }, '')
      written.delete(item.hash)
      blobCache.delete(item.hash)
    }
    await $.state.set({ ...ITEMS, id: old.id }, [])
  }
  await update($, snaps, l => [...(l ?? []), snap].slice(-MAX_SNAPS))
}

async function blobText($: any, hash: string): Promise<string> {
  const hit = blobCache.get(hash)
  if (hit !== undefined) return hit
  const { value } = await $.state.get({ ...BLOB, id: hash })
  const text = value ?? ''
  blobCache.set(hash, text)
  return text
}

export function matchesFilter(item: Item, filter: Filter): boolean {
  switch (filter) {
    case 'all':
      return true
    case 'system':
      return item.group === 'system'
    case 'tools':
      return item.group === 'tools'
    case 'reminders':
      return item.kind === 'reminder'
    case 'chat':
      return item.kind === 'prompt' || item.kind === 'assistant' || item.kind === 'thinking'
    case 'io':
      return item.kind === 'tool_use' || item.kind === 'tool_result'
    case 'new':
      return item.isNew
  }
}

export function countHits(text: string, query: string): number {
  if (query === '') return 0
  const hay = text.toLowerCase()
  const needle = query.toLowerCase()
  let n = 0
  for (let at = hay.indexOf(needle); at !== -1; at = hay.indexOf(needle, at + needle.length)) n++
  return n
}

/** Hard-wraps text to the pane's width so one entry is one drawn row. */
export function wrapLines(text: string, width: number): { n: number; text: string }[] {
  const out: { n: number; text: string }[] = []
  const w = Math.max(10, width)
  text.split('\n').forEach((line, i) => {
    const clean = line.replace(/\t/g, '  ')
    if (clean.length <= w) out.push({ n: i + 1, text: clean })
    else for (let at = 0; at < clean.length; at += w) out.push({ n: at === 0 ? i + 1 : 0, text: clean.slice(at, at + w) })
  })
  return out
}

/** Splits a line around case-insensitive hits of the query. */
export function splitHits(line: string, query: string): { text: string; isHit: boolean }[] {
  if (query === '') return [{ text: line, isHit: false }]
  const parts: { text: string; isHit: boolean }[] = []
  const hay = line.toLowerCase()
  const needle = query.toLowerCase()
  let from = 0
  for (let at = hay.indexOf(needle); at !== -1; at = hay.indexOf(needle, from)) {
    if (at > from) parts.push({ text: line.slice(from, at), isHit: false })
    parts.push({ text: line.slice(at, at + needle.length), isHit: true })
    from = at + needle.length
  }
  if (from < line.length) parts.push({ text: line.slice(from), isHit: false })
  return parts
}

const TAG_COL = 10

function clip(text: string, width: number): string {
  return text.length > width ? text.slice(0, Math.max(0, width - 1)) + '…' : text
}

function snapAt(list: Snap[], v: View): { snap: Snap | undefined; index: number } {
  if (list.length === 0) return { snap: undefined, index: -1 }
  const pinned = v.at === null ? -1 : list.findIndex(s => s.id === v.at)
  const index = pinned === -1 ? list.length - 1 : pinned
  return { snap: list[index], index }
}

function exportMarkdown(snap: Snap, items: readonly Item[], texts: Map<string, string>): string {
  const out: string[] = []
  out.push('# Context window: request ' + snap.seq + ' (turn ' + snap.turn + ', step ' + (snap.step + 1) + ')', '')
  out.push('Model: ' + snap.model + '. Captured by the context-lens mod as the request was about to be sent.', '')
  let group: Group | null = null
  for (const item of items) {
    if (item.group !== group) {
      group = item.group
      out.push('## ' + GROUP_TITLES[group], '')
    }
    const where = item.msg !== undefined ? 'message ' + item.msg + ' (' + item.sub + ')' : item.sub
    out.push('### ' + KIND_TAGS[item.kind] + ': ' + item.label, '', '_' + where + ', about ' + itemTokens(item) + ' tokens' + (item.isNew ? ', new in this request' : '') + '_', '')
    out.push('~~~~', texts.get(item.hash) ?? '', '~~~~', '')
  }
  return out.join('\n')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'context-lens',
      description: 'Browse and search what is in the context window, request by request (args: a search, "export" or "band")',
    })

    return next(e)
  })

  on('command.run', { command: 'context-lens' }, async ($, e) => {
    const args = e.args.trim()
    if (args === 'export') {
      const list = await read($, snaps)
      const v = await read($, view)
      const { snap } = snapAt(list, v)
      if (snap === undefined) return { text: 'context-lens: no request captured yet. Send a prompt first.' }
      const items = (await $.state.get({ ...ITEMS, id: snap.id })).value ?? []
      const texts = new Map<string, string>()
      for (const item of items) texts.set(item.hash, await blobText($, item.hash))
      const path = (await $.session.cwd()) + '/context-lens-request-' + snap.seq + '.md'
      await $.fs.write(path, exportMarkdown(snap, items, texts))

      return { text: 'context-lens: wrote request ' + snap.seq + ' (' + items.length + ' items) to ' + path }
    }

    if (args === 'band') {
      await update($, bandHidden, () => false)

      return { text: 'context-lens: the band above the prompt is back.' }
    }

    await update($, view, v => ({ ...(v as View), query: args, open: null, line: 0 }))
    await $.ui.open({ id: PANE, title: 'Context lens', focus: true })

    return { text: args === '' ? 'Context lens opened.' : 'Context lens opened, searching for "' + args + '".' }
  })

  on('prompt.compose', async ($, e, next) => {
    const result = await next(e)
    // /context measures with an analysis render and a teammate composes its own; neither is this conversation's prompt
    if (!e.traits.includes('analysis') && !e.traits.includes('teammate')) {
      const sections = result.sections.map(s => ({ id: s.id, text: s.text, scope: s.scope }))
      sectionsByModel.set(e.model, sections)
      lastSections = sections
    }

    return result
  })

  on('tool.describe', async ($, e, next) => {
    const result = await next(e)
    deferred.set(e.tool, result.isDeferred === true || (result.isDeferred === undefined && e.isDeferred === true))

    return result
  })

  on('prompt.attachment', async ($, e, next) => {
    const result = await next(e)
    const sent = result.text ?? null
    if (typeof sent === 'string' && sent !== '') {
      const key = hashOf(sent)
      const known = await read($, reminderTypes)
      if (known[key] !== e.type) {
        await update($, reminderTypes, m => Object.fromEntries([...Object.entries(m ?? {}), [key, e.type]].slice(-MAX_REMINDER_TYPES)))
      }
    }

    return result
  })

  on('turn.step', async function* ($, e, next) {
    if (e.agentId !== undefined) return yield* next(e)

    let pending: Promise<void> | null = null
    try {
      const [messages, tools] = await Promise.all([$.session.messages({ as: 'api' }), $.tool.list()])
      pending = record($, e.turnId, e.index, e.model, messages as ApiMessage[], tools).catch(() => undefined)
    } catch {
      pending = null
    }
    try {
      return yield* next(e)
    } finally {
      if (pending !== null) await pending
    }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    const list = await read($, snaps)
    const snap = list.at(-1)
    if (snap === undefined || (await read($, bandHidden))) return next(e)

    const { Box, Text, Button } = $.ui.resolve(e)
    const window = snap.window > 0 ? snap.window : snap.totalTokens
    const added =
      list.length === 1
        ? 'first request: ' + snap.itemCount + ' items'
        : 'request ' + snap.seq + ' added ' + snap.newCount + (snap.newCount === 1 ? ' item' : ' items') + ' (≈' + fmtTokens(snap.newTokens) + ' tok)' + (snap.latest ? ', last: ' + snap.latest : '')

    return (
      <Box flexDirection="row" gap={1} width={Math.max(40, e.props.bodyColumns - 4)}>
        <Box flexShrink={0}>
          <Text>
            <Text color="#d97757">◎</Text> context {fmtTokens(snap.totalTokens)}/{fmtTokens(window)}
          </Text>
        </Box>
        <Box flexGrow={1} flexShrink={1} minWidth={0}>
          <Text dimColor wrap="truncate-end">
            · {added}
          </Text>
        </Box>
        <Box flexShrink={0} gap={1}>
          <Button key="open" plain hotkey="o" label="open lens" onPress={() => void $.ui.open({ id: PANE, title: 'Context lens', focus: true })} />
          <Button key="hide" plain hotkey="h" label="hide" dimColor onPress={() => update($, bandHidden, () => true)} />
        </Box>
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const table = $.ui.resolve(e)
    const { Box, Text, Button } = table
    // mobile draws no field yet; search is then typed with /context-lens <query>
    const Input = 'Input' in table ? table.Input : undefined
    const list = await read($, snaps)
    const v = await read($, view)
    const kindsOf = await read($, reminderTypes)
    // two cells short of the body: the surface draws its close mark in the last column
    const width = Math.max(40, (e.props.bodyColumns ?? 80) - 2)
    // the rows the surface gives the pane body; the whole viewport only where a surface does not say
    const rows = Math.max(12, e.props.scroll?.bodyRows ?? e.viewport?.rows ?? 40)
    const { snap, index } = snapAt(list, v)
    const setView = (fn: (old: View) => View) => update($, view, old => fn(old as View))

    if (snap === undefined) {
      return (
        <Box flexDirection="column">
          <Text bold>Context lens</Text>
          <Text dimColor>No request captured yet. Each model request is snapshotted as it is sent;</Text>
          <Text dimColor>send a prompt and this pane fills in.</Text>
        </Box>
      )
    }

    const items = (await $.state.get({ ...ITEMS, id: snap.id })).value ?? []
    const labelOf = (item: Item) => (item.inner !== undefined && kindsOf[item.inner] ? kindsOf[item.inner] + ': ' : '') + item.label
    const isLive = v.at === null || index === list.length - 1
    const newCount = snap.newCount
    const newTokens = snap.newTokens

    const openHash = v.open === null ? undefined : items.find(i => i.id === v.open)?.hash
    // Stepping between requests keeps the same text open when the other request carries it.
    const goTo = async (target: number | null) => {
      const to = target === null ? list[list.length - 1] : list[target]
      const at = target === null || to === undefined ? null : to.id
      const toItems = openHash === undefined || to === undefined ? [] : ((await $.state.get({ ...ITEMS, id: to.id })).value ?? [])
      const same = toItems.find(i => i.hash === openHash)
      await setView(o => ({ ...o, at, open: same?.id ?? null, line: same ? o.line : 0 }))
    }
    const nav = (
      <Box flexDirection="row" gap={1}>
        <Button key="prev" plain hotkey="p" label="◀ prev" dimColor={index === 0} onPress={() => goTo(Math.max(0, index - 1))} />
        <Button key="next" plain hotkey="n" label="next ▶" dimColor={isLive} onPress={() => goTo(index + 1 >= list.length - 1 ? null : index + 1)} />
        <Button key="live" plain hotkey="l" label="latest" dimColor={isLive} onPress={() => goTo(null)} />
      </Box>
    )

    const header = (
      <Box flexDirection="column">
        <Box flexDirection="row" justifyContent="space-between" width={width}>
          <Text bold>
            Request {snap.seq}/{list[list.length - 1]?.seq ?? snap.seq} · turn {snap.turn} · step {snap.step + 1}
          </Text>
          <Text color={isLive ? '#98c379' : '#e5c07b'}>{isLive ? '● live' : '◌ ' + (list.length - 1 - index) + ' newer'}</Text>
        </Box>
        <Text dimColor>
          {snap.model} · {snap.itemCount} items · {index === 0 ? 'first request captured' : '+' + newCount + ' new (≈' + fmtTokens(newTokens) + ' tok) since the last request'}
        </Text>
      </Box>
    )

    const used = snap.categories.filter(c => c.kind === 'used' && c.tokens > 0)
    const barWidth = width - 2
    const total = snap.window > 0 ? snap.window : Math.max(1, snap.totalTokens)
    const segments = used.map(c => ({ c, cells: Math.max(1, Math.round((c.tokens / total) * barWidth)) }))
    const usedCells = segments.reduce((n, s) => n + s.cells, 0)
    const bar = (
      <Box flexDirection="column">
        <Box flexDirection="row">
          {segments.map(s => (
            <Text color={CATEGORY_COLORS[s.c.name] ?? '#abb2bf'}>{'█'.repeat(s.cells)}</Text>
          ))}
          <Text dimColor>{'░'.repeat(Math.max(0, barWidth - usedCells))}</Text>
        </Box>
        <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
          {used.map(c => (
            <Text>
              <Text color={CATEGORY_COLORS[c.name] ?? '#abb2bf'}>■</Text> {c.name} {fmtTokens(c.tokens)}
            </Text>
          ))}
          <Text dimColor>
            {fmtTokens(snap.totalTokens)} of {fmtTokens(total)} ({Math.round((snap.totalTokens / total) * 100)}%)
          </Text>
        </Box>
      </Box>
    )

    const opened = v.open === null ? undefined : items.find(i => i.id === v.open)

    if (opened !== undefined) {
      const kept = await blobText($, opened.hash)
      const text = kept === '' && opened.chars > 0 ? '[context-lens let this text go: it was only in requests older than the last ' + MAX_SNAPS + ']' : kept
      // the terminal pages by drawn rows, so it wraps here; a desktop wraps proportional text itself
      const lines = e.surface === 'terminal' ? wrapLines(text, width - 6) : text.split('\n').map((t, i) => ({ n: i + 1, text: t.replace(/\t/g, '  ') }))
      const room = Math.max(6, rows - 9)
      const hitRows = v.query === '' ? [] : lines.map((l, i) => (countHits(l.text, v.query) > 0 ? i : -1)).filter(i => i >= 0)
      const top = Math.min(Math.max(0, v.line), Math.max(0, lines.length - room))
      const shown = lines.slice(top, top + room)
      const pos = items.indexOf(opened)
      const atEnd = top + room >= lines.length
      const nextHit = (atEnd ? undefined : hitRows.find(r => r > top + 2)) ?? hitRows[0]
      const go = (item: Item | undefined) => item && setView(o => ({ ...o, open: item.id, line: 0 }))
      const where = opened.msg !== undefined ? 'message ' + opened.msg + ' · ' + opened.sub : GROUP_TITLES[opened.group] + ' · ' + opened.sub

      return (
        <Box flexDirection="column">
          {header}
          {nav}
          <Box flexDirection="row" gap={1} flexWrap="wrap">
            <Button key="back" plain hotkey="b" label="back" onPress={() => setView(o => ({ ...o, open: null, line: 0 }))} />
            <Button key="up" plain hotkey="k" label="◀ item" dimColor={pos === 0} onPress={() => go(items[pos - 1])} />
            <Button key="down" plain hotkey="j" label="item ▶" dimColor={pos === items.length - 1} onPress={() => go(items[pos + 1])} />
            <Button key="pgup" plain hotkey="u" label="page ▲" dimColor={top === 0} onPress={() => setView(o => ({ ...o, line: Math.max(0, top - room) }))} />
            <Button key="pgdn" plain hotkey="d" label="page ▼" dimColor={top + room >= lines.length} onPress={() => setView(o => ({ ...o, line: top + room }))} />
            {hitRows.length > 0 && (
              <Button key="hit" plain hotkey="m" label={'next match (' + hitRows.length + ')'} onPress={() => setView(o => ({ ...o, line: Math.max(0, (nextHit ?? 0) - 2) }))} />
            )}
            <Button key="copy" plain hotkey="y" label="copy" onPress={() => void $.ui.copy({ text, surface: e.surface })} />
          </Box>
          <Text>
            <Text bold color="#61afef">{KIND_TAGS[opened.kind]}</Text> <Text bold>{labelOf(opened)}</Text>
          </Text>
          <Text dimColor>
            {where} · ≈{fmtTokens(itemTokens(opened))} tok · {opened.chars.toLocaleString('en-US')} chars{opened.isNew ? ' · new in this request' : ''} · lines {lines.length === 0 ? 0 : top + 1}–{Math.min(lines.length, top + room)} of {lines.length}
          </Text>
          {opened.kind === 'tool' && <Text dimColor>The tool's input schema is sent too; mods can't read it, so /context's System tools row is the full count.</Text>}
          <Text dimColor>{'─'.repeat(width)}</Text>
          {shown.map(l => (
            <Box flexDirection="row">
              <Box width={5} flexShrink={0} justifyContent="flex-end" paddingRight={1}>
                <Text dimColor>{l.n === 0 ? '' : String(l.n)}</Text>
              </Box>
              <Box flexGrow={1} flexShrink={1} minWidth={0}>
                <Text wrap="wrap">
                  {splitHits(l.text, v.query).map(p => (p.isHit ? <Text backgroundColor="#e5c07b" color="#1e1e1e">{p.text}</Text> : p.text))}
                </Text>
              </Box>
            </Box>
          ))}
        </Box>
      )
    }

    const query = v.query.trim()
    const visible = items.filter(i => matchesFilter(i, v.filter))
    const hits = new Map<string, { count: number; snippet: string }>()
    if (query !== '') {
      const texts = await Promise.all(visible.map(item => blobText($, item.hash)))
      for (const [n, item] of visible.entries()) {
        const text = texts[n] ?? ''
        // a label is mostly the text's own first line; count it only when the text itself has no hit
        const count = countHits(text, query) || countHits(labelOf(item), query)
        if (count === 0) continue
        const at = text.toLowerCase().indexOf(query.toLowerCase())
        const start = Math.max(0, at - 20)
        const snippet = at < 0 ? '' : (start > 0 ? '…' : '') + text.slice(start, start + SNIPPET).replace(/\s+/g, ' ')
        hits.set(item.id, { count, snippet })
      }
    }
    const shownItems = query === '' ? visible : visible.filter(i => hits.has(i.id))
    const totalHits = [...hits.values()].reduce((n, h) => n + h.count, 0)

    const filters = (
      <Box flexDirection="row" flexWrap="wrap" columnGap={2}>
        {FILTERS.map(f => (
          <Button
            key={'f-' + f.id}
            plain
            hotkey={f.hotkey}
            label={f.label + (f.id === 'new' ? ' +' + newCount : '') + (v.filter === f.id ? ' ●' : '')}
            dimColor={v.filter !== f.id}
            onPress={() => setView(o => ({ ...o, filter: f.id }))}
          />
        ))}
      </Box>
    )

    const search = (
      <Box flexDirection="column">
        {Input !== undefined && (
        <Input
          key="search"
          label="Search"
          placeholder="text anywhere in this request (Tab here, then type)"
          value={v.query}
          submitLabel="search"
          onInput={value => void setView(o => ({ ...o, query: value }))}
          onSubmit={value => void setView(o => ({ ...o, query: value }))}
        />
        )}
        {query !== '' && (
          <Text dimColor>
            {totalHits} {totalHits === 1 ? 'match' : 'matches'} in {hits.size} of {visible.length} items
          </Text>
        )}
      </Box>
    )

    const sizeCol = 7
    const labelCol = Math.max(10, width - sizeCol - TAG_COL - 5)
    const groups: Group[] = ['system', 'tools', 'messages']
    const body: RenderChildren[] = []
    for (const g of groups) {
      const inGroup = shownItems.filter(i => i.group === g)
      if (inGroup.length === 0) continue
      const isCollapsed = query === '' && v.filter === 'all' && v.collapsed.includes(g)
      const sum = inGroup.reduce((n, i) => n + itemTokens(i), 0)
      const fresh = inGroup.filter(i => i.isNew).length
      body.push(
        <Button
          key={'g-' + g}
          plain
          label={(isCollapsed ? '▸ ' : '▾ ') + GROUP_TITLES[g] + ' · ' + inGroup.length + ' · ≈' + fmtTokens(sum) + ' tok' + (g === 'tools' ? ' of descriptions' : '') + (fresh > 0 && index > 0 ? ' · +' + fresh + ' new' : '')}
          onPress={() => setView(o => ({ ...o, collapsed: o.collapsed.includes(g) ? o.collapsed.filter(x => x !== g) : [...o.collapsed, g] }))}
        />,
      )
      if (isCollapsed) continue
      let lastMsg = -1
      for (const item of inGroup) {
        if (item.msg !== undefined && item.msg !== lastMsg) {
          lastMsg = item.msg
          body.push(
            <Text dimColor>
              {'  #' + item.msg + ' ' + item.sub}
            </Text>,
          )
        }
        const mark = item.isNew && index > 0 ? '+' : ' '
        const hit = hits.get(item.id)
        const size = hit ? hit.count + (hit.count === 1 ? ' hit' : ' hits') : '≈' + fmtTokens(itemTokens(item))
        // fixed-width columns in Boxes, not padded strings: a desktop draws proportional text and folds runs of spaces
        body.push(
          <Box flexDirection="row" width={width}>
            <Box width={3} flexShrink={0}>
              <Text color="#98c379">{mark}</Text>
            </Box>
            <Box width={TAG_COL} flexShrink={0}>
              <Text dimColor>{KIND_TAGS[item.kind]}</Text>
            </Box>
            <Box flexGrow={1} flexShrink={1} minWidth={0} overflow="hidden">
              <Button
                key={'i-' + item.id}
                plain
                // only the terminal's cells are worth counting; a desktop's proportional text is cut by this Box
                label={e.surface === 'terminal' ? clip(labelOf(item), labelCol) : clip(labelOf(item), 200)}
                onPress={() => setView(o => ({ ...o, open: item.id, line: 0 }))}
              />
            </Box>
            <Box width={sizeCol + 1} flexShrink={0} justifyContent="flex-end">
              <Text dimColor={!hit} color={hit ? '#e5c07b' : undefined}>
                {size}
              </Text>
            </Box>
          </Box>,
        )
        if (hit && hit.snippet !== '') {
          body.push(
            <Box flexDirection="row" paddingLeft={3 + TAG_COL}>
              <Text dimColor wrap="truncate-end">
                {splitHits(hit.snippet, query).map(p => (p.isHit ? <Text backgroundColor="#e5c07b" color="#1e1e1e">{p.text}</Text> : p.text))}
              </Text>
            </Box>,
          )
        }
      }
    }
    if (body.length === 0) body.push(<Text dimColor>Nothing here matches.</Text>)

    return (
      <Box flexDirection="column">
        {header}
        {nav}
        {bar}
        {search}
        {filters}
        <Text dimColor>{'─'.repeat(width)}</Text>
        {body}
      </Box>
    )
  })
}
