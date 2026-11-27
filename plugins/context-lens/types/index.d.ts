/** Where an item sits in the request: the system prompt, the tool list, or the messages. */
export type Group = 'system' | 'tools' | 'messages'

export type Kind =
  | 'section'
  | 'tool'
  | 'prompt'
  | 'reminder'
  | 'assistant'
  | 'thinking'
  | 'tool_use'
  | 'tool_result'
  | 'media'
  | 'other'

/** One piece of one request: a system prompt section, a tool, or a message block. */
export type Item = {
  id: string
  group: Group
  kind: Kind
  label: string
  /** Secondary label: a section's cache scope, a tool's origin, the message's role. */
  sub: string
  /** Key of the item's text in the blob family. */
  hash: string
  /** Where the item sits plus its hash: the same key in the previous request means it is not new. */
  key: string
  /** Key of a reminder's inner text, to name it once its attachment type is known. */
  inner?: string
  chars: number
  /** Claude Code's own token count, for an item whose text mods can't read. */
  estTokens?: number
  /** Not in the previous request: what this request added. */
  isNew: boolean
  /** 1-based message number, for message blocks. */
  msg?: number
}

export type Category = { name: string; tokens: number; kind: string }

/** One model request of the main conversation, as it was about to be sent; its items are kept apart, by id. */
export type Snap = {
  id: string
  /** The request's number in this session, from 1. */
  seq: number
  turnId: string
  turn: number
  step: number
  model: string
  at: number
  window: number
  /** Tokens by category, as /context counts them (local estimate). */
  categories: Category[]
  totalTokens: number
  itemCount: number
  /** Items not in the previous request, and their size. */
  newCount: number
  newTokens: number
  /** The newest message block the request added, as the band names it. */
  latest?: string
}

export type Filter = 'all' | 'system' | 'tools' | 'reminders' | 'chat' | 'io' | 'new'

export type View = {
  /** The request shown, by snapshot id, or null to follow the newest. */
  at: string | null
  filter: Filter
  query: string
  /** The item open in the reader, by id, or null for the list. */
  open: string | null
  /** First wrapped line the reader shows. */
  line: number
  collapsed: Group[]
}

declare module 'claude-code' {
  interface PluginState {
    'context-lens': {
      snaps: Snap[]
      view: View
      reminderTypes: Record<string, string>
      bandHidden: boolean
      items: StateFamily<Item[]>
      blob: StateFamily<string>
    }
  }
}
