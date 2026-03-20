/**
 * Access control for the Feishu channel.
 *
 * Manages pairing, allowlists, group policies, and config persistence.
 * State lives in ~/.claude/channels/feishu/access.json.
 */

import { randomBytes } from 'crypto'
import { readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync, renameSync } from 'fs'
import { homedir } from 'os'
import { join } from 'path'

// ── Paths ──────────────────────────────────────────────────────────────────

export const STATE_DIR = join(homedir(), '.claude', 'channels', 'feishu')
export const ACCESS_FILE = join(STATE_DIR, 'access.json')
export const APPROVED_DIR = join(STATE_DIR, 'approved')
export const ENV_FILE = join(STATE_DIR, '.env')
export const INBOX_DIR = join(STATE_DIR, 'inbox')

// ── Types ──────────────────────────────────────────────────────────────────

export type PendingEntry = {
  senderId: string    // open_id
  chatId: string      // DM chat_id — where to send the approval confirmation
  createdAt: number
  expiresAt: number
  replies: number
}

export type GroupPolicy = {
  requireMention: boolean
  allowFrom: string[] // open_id list; empty = any member
}

export type Access = {
  dmPolicy: 'pairing' | 'allowlist' | 'disabled'
  allowFrom: string[] // open_id list
  groups: Record<string, GroupPolicy> // keyed on chat_id
  pending: Record<string, PendingEntry> // keyed on 6-char hex code
  mentionPatterns?: string[]
  ackReaction?: string       // Feishu emoji_type string, empty = disabled
  replyToMode?: 'off' | 'first' | 'all'
  textChunkLimit?: number
  chunkMode?: 'length' | 'newline'
}

export type GateResult =
  | { action: 'deliver'; access: Access }
  | { action: 'drop' }
  | { action: 'pair'; code: string; isResend: boolean }

// ── Environment ────────────────────────────────────────────────────────────

/**
 * Load ~/.claude/channels/feishu/.env into process.env. Shell env wins.
 */
export function loadEnv(): void {
  try {
    for (const line of readFileSync(ENV_FILE, 'utf8').split('\n')) {
      const m = line.match(/^(\w+)=(.*)$/)
      if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2]
    }
  } catch {}
}

// ── Config I/O ─────────────────────────────────────────────────────────────

export function defaultAccess(): Access {
  return {
    dmPolicy: 'pairing',
    allowFrom: [],
    groups: {},
    pending: {},
  }
}

export function readAccessFile(): Access {
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
    process.stderr.write('feishu: access.json is corrupt, moved aside. Starting fresh.\n')
    return defaultAccess()
  }
}

export function saveAccess(a: Access): void {
  mkdirSync(STATE_DIR, { recursive: true, mode: 0o700 })
  const tmp = ACCESS_FILE + '.tmp'
  writeFileSync(tmp, JSON.stringify(a, null, 2) + '\n', { mode: 0o600 })
  renameSync(tmp, ACCESS_FILE)
}

// ── Expiry ─────────────────────────────────────────────────────────────────

export function pruneExpired(a: Access): boolean {
  const now = Date.now()
  let changed = false
  for (const [code, p] of Object.entries(a.pending)) {
    if (p.expiresAt < now) {
      delete a.pending[code]
      changed = true
    }
  }
  return changed
}

// ── Static mode ────────────────────────────────────────────────────────────

const STATIC = process.env.FEISHU_ACCESS_MODE === 'static'

const BOOT_ACCESS: Access | null = STATIC
  ? (() => {
      const a = readAccessFile()
      if (a.dmPolicy === 'pairing') {
        process.stderr.write(
          'feishu channel: static mode — dmPolicy "pairing" downgraded to "allowlist"\n',
        )
        a.dmPolicy = 'allowlist'
      }
      a.pending = {}
      return a
    })()
  : null

export function loadAccess(): Access {
  return BOOT_ACCESS ?? readAccessFile()
}

// ── Gate ────────────────────────────────────────────────────────────────────

export function gate(
  senderId: string,
  chatId: string,
  chatType: 'p2p' | 'group',
  isMentionedFn: () => boolean,
): GateResult {
  const access = loadAccess()
  const pruned = pruneExpired(access)
  if (pruned && !STATIC) saveAccess(access)

  if (access.dmPolicy === 'disabled') return { action: 'drop' }

  if (chatType === 'p2p') {
    if (access.allowFrom.includes(senderId)) return { action: 'deliver', access }
    if (access.dmPolicy === 'allowlist') return { action: 'drop' }

    // Pairing mode — check for existing non-expired code for this sender.
    for (const [code, p] of Object.entries(access.pending)) {
      if (p.senderId === senderId) {
        // Reply twice max (initial + one reminder), then go silent.
        if ((p.replies ?? 1) >= 2) return { action: 'drop' }
        p.replies = (p.replies ?? 1) + 1
        if (!STATIC) saveAccess(access)
        return { action: 'pair', code, isResend: true }
      }
    }
    // Cap pending at 3.
    if (Object.keys(access.pending).length >= 3) return { action: 'drop' }

    const code = randomBytes(3).toString('hex') // 6 hex chars
    const now = Date.now()
    access.pending[code] = {
      senderId,
      chatId,
      createdAt: now,
      expiresAt: now + 60 * 60 * 1000, // 1h
      replies: 1,
    }
    if (!STATIC) saveAccess(access)
    return { action: 'pair', code, isResend: false }
  }

  // Group chat — per-chat opt-in.
  const policy = access.groups[chatId]
  if (!policy) return { action: 'drop' }
  const groupAllowFrom = policy.allowFrom ?? []
  const requireMention = policy.requireMention ?? true

  if (groupAllowFrom.length > 0 && !groupAllowFrom.includes(senderId)) {
    return { action: 'drop' }
  }
  if (requireMention && !isMentionedFn()) {
    return { action: 'drop' }
  }
  return { action: 'deliver', access }
}

// ── Approval polling ───────────────────────────────────────────────────────

/**
 * Poll approved/ dir for pairing approvals. The /feishu:access skill writes
 * a file at approved/<senderId> with the DM chatId as contents.
 */
export function checkApprovals(feishuClient: any): void {
  let files: string[]
  try {
    files = readdirSync(APPROVED_DIR)
  } catch {
    return
  }
  if (files.length === 0) return

  for (const senderId of files) {
    const file = join(APPROVED_DIR, senderId)
    let dmChatId: string
    try {
      dmChatId = readFileSync(file, 'utf8').trim()
    } catch {
      rmSync(file, { force: true })
      continue
    }
    if (!dmChatId) {
      rmSync(file, { force: true })
      continue
    }

    void (async () => {
      try {
        await feishuClient.im.message.create({
          params: { receive_id_type: 'chat_id' },
          data: {
            receive_id: dmChatId,
            content: JSON.stringify({ text: '已配对！向 Claude 打个招呼吧。' }),
            msg_type: 'text',
          },
        })
        rmSync(file, { force: true })
      } catch (err) {
        process.stderr.write(`feishu channel: failed to send approval confirm: ${err}\n`)
        rmSync(file, { force: true })
      }
    })()
  }
}
