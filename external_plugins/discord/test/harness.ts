// Imported first by every test file: it points the server's state dir at a
// scratch directory before server.ts reads the env at module load.
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { ChannelType } from 'discord.js'

export const STATE_DIR = mkdtempSync(join(tmpdir(), 'discord-channel-test-'))
process.env.DISCORD_STATE_DIR = STATE_DIR
process.env.DISCORD_BOT_TOKEN ??= 'test-token-not-a-real-bot'

export const BOT_ID = '100000000000000001'

export function writeAccess(access: Record<string, unknown>): void {
  mkdirSync(STATE_DIR, { recursive: true })
  writeFileSync(join(STATE_DIR, 'access.json'), JSON.stringify(access, null, 2))
}

export function cleanup(): void {
  rmSync(STATE_DIR, { recursive: true, force: true })
}

type MsgOpts = {
  id?: string
  content?: string
  authorId?: string
  username?: string
  bot?: boolean
  channel?: any
  reference?: { messageId: string } | null
  mentions?: string[]
  mentionsBot?: boolean
  attachments?: any[]
  reference_author?: string
}

export function mkChannel(o: {
  id?: string
  type?: number
  name?: string
  parentId?: string | null
  messages?: Record<string, any>
} = {}): any {
  const type = o.type ?? ChannelType.GuildText
  const isThread =
    type === ChannelType.PublicThread ||
    type === ChannelType.PrivateThread ||
    type === ChannelType.AnnouncementThread
  const store = o.messages ?? {}
  const ch: any = {
    id: o.id ?? '200000000000000001',
    type,
    name: o.name ?? 'general',
    parentId: o.parentId ?? null,
    sent: [] as any[],
    isThread: () => isThread,
    isTextBased: () => true,
    sendTyping: async () => {},
    messages: {
      fetch: async (arg: any) => {
        if (typeof arg === 'object' && arg !== null && !('id' in arg)) {
          return new Map(Object.entries(store).map(([k, v]) => [k, v])) as any
        }
        const id = typeof arg === 'string' ? arg : arg?.id
        const m = store[id]
        if (!m) throw Object.assign(new Error('Unknown Message'), { code: 10008 })
        return m
      },
    },
    threads: {
      create: async (opts: any) => {
        ch.threadsCreated.push(opts)
        return { id: '300000000000000009', name: opts.name }
      },
      fetchActive: async () => ({ threads: new Map() }),
      fetchArchived: async () => ({ threads: new Map() }),
    },
    threadsCreated: [] as any[],
    send: async (payload: any) => {
      const sent = {
        id: `9000000000000000${ch.sent.length + 10}`,
        ...payload,
        delete: async () => {},
      }
      ch.sent.push(payload)
      return sent
    },
  }
  return ch
}

export function mkMsg(o: MsgOpts = {}): any {
  const channel = o.channel ?? mkChannel()
  const mentionIds = o.mentions ?? []
  const users = new Map(mentionIds.map(id => [id, { id, username: `u${id}` }]))
  if (o.mentionsBot) users.set(BOT_ID, { id: BOT_ID, username: 'claude' })
  const msg: any = {
    id: o.id ?? '400000000000000001',
    content: o.content ?? 'hello',
    channelId: channel.id,
    channel,
    author: {
      id: o.authorId ?? '500000000000000001',
      username: o.username ?? 'someone',
      bot: o.bot ?? false,
    },
    createdAt: new Date('2026-09-07T01:23:45.000Z'),
    attachments: new Map((o.attachments ?? []).map((a, i) => [String(i), a])),
    reference: o.reference ?? null,
    mentions: {
      users,
      has: (u: any) => users.has(typeof u === 'string' ? u : u?.id),
    },
    reactions: [] as string[],
    replies: [] as string[],
    react: async (e: string) => { msg.reactions.push(e) },
    reply: async (t: string) => { msg.replies.push(t) },
    fetchReference: async () => {
      if (!o.reference) throw new Error('no reference')
      const ref = channel.messages ? await channel.messages.fetch(o.reference.messageId) : null
      if (!ref) throw new Error('not found')
      return ref
    },
    edit: async (t: string) => ({ id: msg.id, content: t }),
    delete: async () => { msg.deleted = true },
    startThread: async (opts: any) => {
      msg.startedThread = opts
      return { id: '300000000000000009', name: opts.name }
    },
  }
  return msg
}

/** Replaces mcp.notification with a collector. Returns the collected params. */
export function captureNotifications(mcp: any): { notes: any[]; restore: () => void } {
  const notes: any[] = []
  const original = mcp.notification.bind(mcp)
  mcp.notification = async (n: any) => { notes.push(n) }
  return { notes, restore: () => { mcp.notification = original } }
}
