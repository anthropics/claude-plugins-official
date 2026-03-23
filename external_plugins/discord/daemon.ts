#!/usr/bin/env bun
/**
 * PAI Discord Gateway Daemon
 *
 * Sole owner of the Discord gateway connection. Writes inbound messages
 * to a filesystem queue and executes outbound commands from it.
 * Managed by systemd — survives SSH drops and session crashes.
 *
 * Queue dirs:
 *   ~/.claude/channels/discord/inbound/   — daemon writes, consumer reads+deletes
 *   ~/.claude/channels/discord/outbound/  — consumer writes commands, daemon executes+writes results
 */

import {
  Client,
  GatewayIntentBits,
  Partials,
  ChannelType,
  type Message,
  type Attachment,
} from 'discord.js'
import { randomBytes } from 'crypto'
import {
  readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync,
  statSync, renameSync, existsSync, unlinkSync, appendFileSync,
} from 'fs'
import { homedir } from 'os'
import { join, sep } from 'path'

// ── Logging ────────────────────────────────────────────────────────────

const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 } as const
type LogLevel = keyof typeof LOG_LEVELS

const LOG_LEVEL: LogLevel = (process.env.DISCORD_LOG_LEVEL as LogLevel) ?? 'info'
const STATE_DIR   = join(homedir(), '.claude', 'channels', 'discord')
const LOG_FILE    = join(STATE_DIR, 'daemon.log')
const LOG_MAX_BYTES = 2 * 1024 * 1024 // 2MB — rotate when exceeded

function log(level: LogLevel, component: string, message: string, meta?: Record<string, unknown>): void {
  if (LOG_LEVELS[level] < LOG_LEVELS[LOG_LEVEL]) return
  const ts = new Date().toISOString()
  const metaStr = meta ? ' ' + JSON.stringify(meta) : ''
  const line = `${ts} [${level.toUpperCase().padEnd(5)}] ${component}: ${message}${metaStr}\n`
  process.stderr.write(line)
  try {
    // Rotate if over max
    try { if (statSync(LOG_FILE).size > LOG_MAX_BYTES) renameSync(LOG_FILE, LOG_FILE + '.old') } catch {}
    appendFileSync(LOG_FILE, line)
  } catch {}
}
const ACCESS_FILE = join(STATE_DIR, 'access.json')
const APPROVED_DIR = join(STATE_DIR, 'approved')
const ENV_FILE    = join(STATE_DIR, '.env')
const INBOUND_DIR = join(STATE_DIR, 'inbound')
const OUTBOUND_DIR = join(STATE_DIR, 'outbound')
const INBOX_DIR   = join(STATE_DIR, 'inbox')

for (const d of [INBOUND_DIR, OUTBOUND_DIR, INBOX_DIR, APPROVED_DIR]) {
  mkdirSync(d, { recursive: true })
}

// ── Load .env ──────────────────────────────────────────────────────────

try {
  for (const line of readFileSync(ENV_FILE, 'utf8').split('\n')) {
    const m = line.match(/^(\w+)=(.*)$/)
    if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2]
  }
} catch {}

const TOKEN = process.env.DISCORD_BOT_TOKEN
if (!TOKEN) {
  log('error', 'init', `DISCORD_BOT_TOKEN required — set in ${ENV_FILE}`)
  process.exit(1)
}

// ── Types (shared with server.ts) ──────────────────────────────────────

type PendingEntry = {
  senderId: string
  chatId: string
  createdAt: number
  expiresAt: number
  replies: number
}

type GroupPolicy = {
  requireMention: boolean
  allowFrom: string[]
}

type Access = {
  dmPolicy: 'pairing' | 'allowlist' | 'disabled'
  allowFrom: string[]
  groups: Record<string, GroupPolicy>
  pending: Record<string, PendingEntry>
  mentionPatterns?: string[]
  ackReaction?: string
  replyToMode?: 'off' | 'first' | 'all'
  textChunkLimit?: number
  chunkMode?: 'length' | 'newline'
}

function defaultAccess(): Access {
  return { dmPolicy: 'pairing', allowFrom: [], groups: {}, pending: {} }
}

// ── Access control (unchanged from server.ts) ──────────────────────────

function readAccessFile(): Access {
  try {
    const raw = readFileSync(ACCESS_FILE, 'utf8')
    const parsed = JSON.parse(raw) as Partial<Access>
    return {
      dmPolicy: parsed.dmPolicy ?? 'pairing',
      allowFrom: parsed.allowFrom ?? [],
      groups: parsed.groups ?? {},
      pending: parsed.pending ?? {},
      mentionPatterns: parsed.mentionPatterns,
      ackReaction: parsed.ackReaction,
      replyToMode: parsed.replyToMode,
      textChunkLimit: parsed.textChunkLimit,
      chunkMode: parsed.chunkMode,
    }
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') return defaultAccess()
    try { renameSync(ACCESS_FILE, `${ACCESS_FILE}.corrupt-${Date.now()}`) } catch {}
    log('warn', 'access', 'access.json corrupt, moved aside')
    return defaultAccess()
  }
}

function loadAccess(): Access { return readAccessFile() }

function saveAccess(a: Access): void {
  mkdirSync(STATE_DIR, { recursive: true, mode: 0o700 })
  const tmp = ACCESS_FILE + '.tmp'
  writeFileSync(tmp, JSON.stringify(a, null, 2) + '\n', { mode: 0o600 })
  renameSync(tmp, ACCESS_FILE)
}

function pruneExpired(a: Access): boolean {
  const now = Date.now()
  let changed = false
  for (const [code, p] of Object.entries(a.pending)) {
    if (p.expiresAt < now) { delete a.pending[code]; changed = true }
  }
  return changed
}

type GateResult =
  | { action: 'deliver'; access: Access }
  | { action: 'drop' }
  | { action: 'pair'; code: string; isResend: boolean }

// ── Discord client ─────────────────────────────────────────────────────

const client = new Client({
  intents: [
    GatewayIntentBits.DirectMessages,
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
  partials: [Partials.Channel],
})

const recentSentIds = new Set<string>()
const RECENT_SENT_CAP = 200

function noteSent(id: string): void {
  recentSentIds.add(id)
  if (recentSentIds.size > RECENT_SENT_CAP) {
    const first = recentSentIds.values().next().value
    if (first) recentSentIds.delete(first)
  }
}

async function isMentioned(msg: Message, extraPatterns?: string[]): Promise<boolean> {
  if (client.user && msg.mentions.has(client.user)) return true
  const refId = msg.reference?.messageId
  if (refId) {
    if (recentSentIds.has(refId)) return true
    try {
      const ref = await msg.fetchReference()
      if (ref.author.id === client.user?.id) return true
    } catch {}
  }
  for (const pat of extraPatterns ?? []) {
    try { if (new RegExp(pat, 'i').test(msg.content)) return true } catch {}
  }
  return false
}

async function gate(msg: Message): Promise<GateResult> {
  const access = loadAccess()
  if (pruneExpired(access)) saveAccess(access)
  if (access.dmPolicy === 'disabled') return { action: 'drop' }

  const senderId = msg.author.id
  const isDM = msg.channel.type === ChannelType.DM

  if (isDM) {
    if (access.allowFrom.includes(senderId)) return { action: 'deliver', access }
    if (access.dmPolicy === 'allowlist') return { action: 'drop' }

    for (const [code, p] of Object.entries(access.pending)) {
      if (p.senderId === senderId) {
        if ((p.replies ?? 1) >= 2) return { action: 'drop' }
        p.replies = (p.replies ?? 1) + 1
        saveAccess(access)
        return { action: 'pair', code, isResend: true }
      }
    }
    if (Object.keys(access.pending).length >= 3) return { action: 'drop' }

    const code = randomBytes(3).toString('hex')
    const now = Date.now()
    access.pending[code] = {
      senderId, chatId: msg.channelId,
      createdAt: now, expiresAt: now + 60 * 60 * 1000, replies: 1,
    }
    saveAccess(access)
    return { action: 'pair', code, isResend: false }
  }

  const channelId = msg.channel.isThread()
    ? msg.channel.parentId ?? msg.channelId : msg.channelId
  const policy = access.groups[channelId]
  if (!policy) return { action: 'drop' }
  if ((policy.allowFrom ?? []).length > 0 && !policy.allowFrom.includes(senderId))
    return { action: 'drop' }
  if ((policy.requireMention ?? true) && !(await isMentioned(msg, access.mentionPatterns)))
    return { action: 'drop' }
  return { action: 'deliver', access }
}

// ── Attachment helpers ─────────────────────────────────────────────────

const MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024

function safeAttName(att: Attachment): string {
  return (att.name ?? att.id).replace(/[\[\]\r\n;]/g, '_')
}

async function downloadAttachment(att: Attachment): Promise<string> {
  if (att.size > MAX_ATTACHMENT_BYTES)
    throw new Error(`attachment too large: ${(att.size / 1024 / 1024).toFixed(1)}MB`)
  const res = await fetch(att.url)
  const buf = Buffer.from(await res.arrayBuffer())
  const name = att.name ?? `${att.id}`
  const rawExt = name.includes('.') ? name.slice(name.lastIndexOf('.') + 1) : 'bin'
  const ext = rawExt.replace(/[^a-zA-Z0-9]/g, '') || 'bin'
  const path = join(INBOX_DIR, `${Date.now()}-${att.id}.${ext}`)
  mkdirSync(INBOX_DIR, { recursive: true })
  writeFileSync(path, buf)
  return path
}

// ── Chunking ───────────────────────────────────────────────────────────

const MAX_CHUNK_LIMIT = 2000

function chunk(text: string, limit: number, mode: 'length' | 'newline'): string[] {
  if (text.length <= limit) return [text]
  const out: string[] = []
  let rest = text
  while (rest.length > limit) {
    let cut = limit
    if (mode === 'newline') {
      const para = rest.lastIndexOf('\n\n', limit)
      const line = rest.lastIndexOf('\n', limit)
      const space = rest.lastIndexOf(' ', limit)
      cut = para > limit / 2 ? para : line > limit / 2 ? line : space > 0 ? space : limit
    }
    out.push(rest.slice(0, cut))
    rest = rest.slice(cut).replace(/^\n+/, '')
  }
  if (rest) out.push(rest)
  return out
}

// ── Inbound: write Discord messages to queue ───────────────────────────

async function handleInbound(msg: Message): Promise<void> {
  const result = await gate(msg)

  if (result.action === 'drop') {
    log('debug', 'gate', `dropped message`, { user: msg.author.username, user_id: msg.author.id, channel: msg.channelId, isDM: msg.channel.type === ChannelType.DM })
    return
  }

  if (result.action === 'pair') {
    log('info', 'gate', `pairing initiated`, { user: msg.author.username, user_id: msg.author.id })
    const lead = result.isResend ? 'Still pending' : 'Pairing required'
    try {
      await msg.reply(`${lead} — run in Claude Code:\n\n/discord:access pair ${result.code}`)
    } catch (err) {
      log('error', 'pairing', `failed to send pairing code`, { error: String(err) })
    }
    return
  }

  // Typing indicator
  if ('sendTyping' in msg.channel) {
    void msg.channel.sendTyping().catch(() => {})
  }

  // Ack reaction
  const access = result.access
  if (access.ackReaction) {
    void msg.react(access.ackReaction).catch(() => {})
  }

  // Build attachment metadata
  const atts: Array<{ name: string; type: string; size: number; url: string }> = []
  for (const att of msg.attachments.values()) {
    atts.push({
      name: safeAttName(att),
      type: att.contentType ?? 'unknown',
      size: att.size,
      url: att.url,
    })
  }

  // Write inbound message to queue
  const inboundMsg = {
    type: 'message',
    chat_id: msg.channelId,
    message_id: msg.id,
    user: msg.author.username,
    user_id: msg.author.id,
    content: msg.content || (atts.length > 0 ? '(attachment)' : ''),
    ts: msg.createdAt.toISOString(),
    attachments: atts,
  }

  const filename = `${Date.now()}-${msg.id}.json`
  const tmpPath = join(INBOUND_DIR, `.${filename}.tmp`)
  const finalPath = join(INBOUND_DIR, filename)
  writeFileSync(tmpPath, JSON.stringify(inboundMsg, null, 2))
  renameSync(tmpPath, finalPath)

  log('info', 'inbound', `queued message`, { user: msg.author.username, user_id: msg.author.id, chat_id: msg.channelId, message_id: msg.id, preview: msg.content.slice(0, 80) })
}

// ── Outbound: execute commands from queue ──────────────────────────────

async function fetchTextChannel(id: string) {
  const ch = await client.channels.fetch(id)
  if (!ch || !ch.isTextBased()) throw new Error(`channel ${id} not found or not text-based`)
  return ch
}

async function fetchAllowedChannel(id: string) {
  const ch = await fetchTextChannel(id)
  const access = loadAccess()
  if (ch.type === ChannelType.DM) {
    if (access.allowFrom.includes(ch.recipientId)) return ch
  } else {
    const key = ch.isThread() ? ch.parentId ?? ch.id : ch.id
    if (key in access.groups) return ch
  }
  throw new Error(`channel ${id} is not allowlisted`)
}

function assertSendable(f: string): void {
  let real: string, stateReal: string
  try { real = Bun.resolveSync(f, '.'); stateReal = Bun.resolveSync(STATE_DIR, '.') }
  catch { return }
  const inbox = join(stateReal, 'inbox')
  if (real.startsWith(stateReal + sep) && !real.startsWith(inbox + sep))
    throw new Error(`refusing to send channel state: ${f}`)
}

async function processOutbound(file: string): Promise<void> {
  const filepath = join(OUTBOUND_DIR, file)
  let cmd: Record<string, unknown>
  try {
    cmd = JSON.parse(readFileSync(filepath, 'utf8'))
  } catch {
    rmSync(filepath, { force: true })
    return
  }

  const requestId = cmd.request_id as string
  const resultPath = join(OUTBOUND_DIR, `${file.replace('.json', '')}.result.json`)

  const writeResult = (success: boolean, result: string, error: string | null) => {
    const tmp = resultPath + '.tmp'
    writeFileSync(tmp, JSON.stringify({ request_id: requestId, success, result, error }))
    renameSync(tmp, resultPath)
  }

  try {
    switch (cmd.type) {
      case 'reply': {
        const chatId = cmd.chat_id as string
        const text = cmd.text as string
        const replyTo = cmd.reply_to as string | undefined
        const files = (cmd.files as string[] | undefined) ?? []

        const ch = await fetchAllowedChannel(chatId)
        if (!('send' in ch)) throw new Error('channel is not sendable')

        for (const f of files) {
          assertSendable(f)
          const st = statSync(f)
          if (st.size > MAX_ATTACHMENT_BYTES)
            throw new Error(`file too large: ${f}`)
        }
        if (files.length > 10) throw new Error('max 10 attachments')

        const access = loadAccess()
        const limit = Math.max(1, Math.min(access.textChunkLimit ?? MAX_CHUNK_LIMIT, MAX_CHUNK_LIMIT))
        const mode = access.chunkMode ?? 'length'
        const replyMode = access.replyToMode ?? 'first'
        const chunks = chunk(text, limit, mode)
        const sentIds: string[] = []

        for (let i = 0; i < chunks.length; i++) {
          const shouldReplyTo = replyTo != null && replyMode !== 'off' && (replyMode === 'all' || i === 0)
          const sent = await ch.send({
            content: chunks[i],
            ...(i === 0 && files.length > 0 ? { files } : {}),
            ...(shouldReplyTo ? { reply: { messageReference: replyTo, failIfNotExists: false } } : {}),
          })
          noteSent(sent.id)
          sentIds.push(sent.id)
        }

        const result = sentIds.length === 1
          ? `sent (id: ${sentIds[0]})`
          : `sent ${sentIds.length} parts (ids: ${sentIds.join(', ')})`
        log('info', 'outbound', `reply sent`, { chat_id: chatId, chunks: chunks.length, files: files.length, request_id: requestId })
        writeResult(true, result, null)
        break
      }

      case 'react': {
        const ch = await fetchAllowedChannel(cmd.chat_id as string)
        const msg = await ch.messages.fetch(cmd.message_id as string)
        await msg.react(cmd.emoji as string)
        writeResult(true, 'reacted', null)
        break
      }

      case 'edit_message': {
        const ch = await fetchAllowedChannel(cmd.chat_id as string)
        const msg = await ch.messages.fetch(cmd.message_id as string)
        const edited = await msg.edit(cmd.text as string)
        writeResult(true, `edited (id: ${edited.id})`, null)
        break
      }

      case 'fetch_messages': {
        const ch = await fetchAllowedChannel(cmd.chat_id as string)
        const limit = Math.min((cmd.limit as number) ?? 20, 100)
        const msgs = await ch.messages.fetch({ limit })
        const me = client.user?.id
        const arr = [...msgs.values()].reverse()
        const out = arr.length === 0
          ? '(no messages)'
          : arr.map(m => {
              const who = m.author.id === me ? 'me' : m.author.username
              const atts = m.attachments.size > 0 ? ` +${m.attachments.size}att` : ''
              const text = m.content.replace(/[\r\n]+/g, ' ⏎ ')
              return `[${m.createdAt.toISOString()}] ${who}: ${text}  (id: ${m.id}${atts})`
            }).join('\n')
        writeResult(true, out, null)
        break
      }

      case 'download_attachment': {
        const ch = await fetchAllowedChannel(cmd.chat_id as string)
        const msg = await ch.messages.fetch(cmd.message_id as string)
        if (msg.attachments.size === 0) {
          writeResult(true, 'message has no attachments', null)
          break
        }
        const lines: string[] = []
        for (const att of msg.attachments.values()) {
          const path = await downloadAttachment(att)
          const kb = (att.size / 1024).toFixed(0)
          lines.push(`  ${path}  (${safeAttName(att)}, ${att.contentType ?? 'unknown'}, ${kb}KB)`)
        }
        writeResult(true, `downloaded ${lines.length} attachment(s):\n${lines.join('\n')}`, null)
        break
      }

      default:
        writeResult(false, '', `unknown command type: ${cmd.type}`)
    }
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err)
    writeResult(false, '', errMsg)
    log('error', 'outbound', `${cmd.type} failed`, { error: errMsg, request_id: requestId })
  }

  // Clean up the command file after processing
  rmSync(filepath, { force: true })
}

function pollOutbound(): void {
  let files: string[]
  try { files = readdirSync(OUTBOUND_DIR) } catch { return }

  for (const file of files) {
    // Only process command files, skip result files and temp files
    if (!file.endsWith('.json') || file.endsWith('.result.json') || file.startsWith('.')) continue
    processOutbound(file).catch(err => {
      log('error', 'outbound', `processing error`, { error: String(err), file })
    })
  }
}

// ── Approval checking (unchanged from server.ts) ──────────────────────

function checkApprovals(): void {
  let files: string[]
  try { files = readdirSync(APPROVED_DIR) } catch { return }
  if (files.length === 0) return

  for (const senderId of files) {
    const file = join(APPROVED_DIR, senderId)
    let dmChannelId: string
    try { dmChannelId = readFileSync(file, 'utf8').trim() }
    catch { rmSync(file, { force: true }); continue }
    if (!dmChannelId) { rmSync(file, { force: true }); continue }

    void (async () => {
      try {
        const ch = await fetchTextChannel(dmChannelId)
        if ('send' in ch) await ch.send("Paired! Say hi to Claude.")
        rmSync(file, { force: true })
      } catch (err) {
        log('error', 'pairing', `approval confirm failed`, { error: String(err), senderId })
        rmSync(file, { force: true })
      }
    })()
  }
}

// ── Health HTTP server ─────────────────────────────────────────────────

const HEALTH_PORT = 8890

Bun.serve({
  port: HEALTH_PORT,
  fetch(req) {
    const url = new URL(req.url)
    if (url.pathname === '/health') {
      const connected = client.ws.status === 0 // WebSocketManager.READY = 0
      return Response.json({
        status: connected ? 'ok' : 'disconnected',
        uptime: process.uptime(),
        gateway: connected,
        bot: client.user?.tag ?? 'not ready',
        inbound_queue: readdirSync(INBOUND_DIR).filter(f => f.endsWith('.json')).length,
        outbound_queue: readdirSync(OUTBOUND_DIR).filter(f => f.endsWith('.json') && !f.endsWith('.result.json')).length,
      }, { status: connected ? 200 : 503 })
    }
    return new Response('not found', { status: 404 })
  },
})

// ── Start ──────────────────────────────────────────────────────────────

// Poll intervals
setInterval(checkApprovals, 5000)
setInterval(pollOutbound, 1000) // Check outbound every second for low latency

client.on('messageCreate', msg => {
  if (msg.author.bot) return
  handleInbound(msg).catch(e => log('error', 'gateway', `handleInbound failed`, { error: String(e), user: msg.author.username }))
})

client.once('ready', c => {
  log('info', 'gateway', `connected as ${c.user.tag}`)
  log('info', 'health', `endpoint on http://localhost:${HEALTH_PORT}/health`)
})

await client.login(TOKEN)

log('info', 'init', `daemon started`, { pid: process.pid })

// Log gateway lifecycle events for debugging
client.on('warn', (msg) => log('warn', 'gateway', msg))
client.on('error', (err) => log('error', 'gateway', err.message))
client.on('shardDisconnect', (ev, id) => log('warn', 'gateway', `shard ${id} disconnected`, { code: ev.code, reason: ev.reason }))
client.on('shardReconnecting', (id) => log('info', 'gateway', `shard ${id} reconnecting`))
client.on('shardResume', (id, replayed) => log('info', 'gateway', `shard ${id} resumed`, { replayed }))
