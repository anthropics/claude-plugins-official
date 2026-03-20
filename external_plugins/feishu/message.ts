/**
 * Message utilities for the Feishu channel.
 *
 * Chunking, mention detection, attachment helpers, file security,
 * sent-ID tracking, event deduplication.
 */

import { realpathSync, statSync } from 'fs'
import { join, sep } from 'path'

// ── Constants ──────────────────────────────────────────────────────────────

/** Feishu allows ~30k chars but 4k is a practical default for readability. */
export const MAX_CHUNK_LIMIT = 4000

export const MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024

// ── Text chunking ──────────────────────────────────────────────────────────

/**
 * Split text into chunks that fit within `limit` characters.
 * `newline` mode prefers paragraph/line boundaries; `length` mode hard-cuts.
 */
export function chunk(text: string, limit: number, mode: 'length' | 'newline'): string[] {
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

// ── Mention detection ──────────────────────────────────────────────────────

export type FeishuMention = {
  key: string
  id: { open_id: string; user_id?: string; union_id?: string }
  name: string
}

/**
 * 3-tier mention check:
 * 1. Structured @mention in the mentions array
 * 2. parentId references a bot-sent message (in recentSentIds)
 * 3. Message text matches a regex from extraPatterns
 */
export function isMentioned(
  mentions: FeishuMention[],
  botOpenId: string,
  parentId: string | undefined,
  recentSentIds: Set<string>,
  extraPatterns: string[] | undefined,
  messageText: string,
): boolean {
  // 1. Structured @mention
  if (mentions.some(m => m.id?.open_id === botOpenId)) return true

  // 2. Reply to a bot message
  if (parentId && recentSentIds.has(parentId)) return true

  // 3. Regex patterns
  for (const pat of extraPatterns ?? []) {
    try {
      if (new RegExp(pat, 'i').test(messageText)) return true
    } catch {}
  }
  return false
}

// ── File security ──────────────────────────────────────────────────────────

/**
 * Prevent sending files from the channel state directory (except inbox/).
 * This stops the bot from leaking .env, access.json, etc.
 */
export function assertSendable(filePath: string, stateDir: string): void {
  let real: string, stateReal: string
  try {
    real = realpathSync(filePath)
    stateReal = realpathSync(stateDir)
  } catch {
    return // statSync will fail properly; or stateDir absent → nothing to leak
  }
  const inbox = join(stateReal, 'inbox')
  if (real.startsWith(stateReal + sep) && !real.startsWith(inbox + sep)) {
    throw new Error(`refusing to send channel state: ${filePath}`)
  }
}

// ── Attachment helpers ─────────────────────────────────────────────────────

/**
 * Strip injection-prone characters from attachment names.
 */
export function safeAttName(name: string): string {
  return name.replace(/[\[\]\r\n;]/g, '_')
}

const FILE_TYPE_MAP: Record<string, string> = {
  pdf: 'pdf',
  doc: 'doc', docx: 'doc',
  xls: 'xls', xlsx: 'xls',
  ppt: 'ppt', pptx: 'ppt',
  mp4: 'mp4',
  opus: 'opus', ogg: 'opus',
}

/**
 * Map file extension to Feishu file_type enum. Falls back to 'stream'.
 */
export function fileTypeFromExt(ext: string): string {
  return FILE_TYPE_MAP[ext.toLowerCase()] ?? 'stream'
}

const IMAGE_EXTS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'])

/**
 * Return true if the extension represents an image that should use im.image.create.
 */
export function isImageExt(ext: string): boolean {
  return IMAGE_EXTS.has(ext.toLowerCase())
}

// ── Recent sent ID tracking ────────────────────────────────────────────────

const RECENT_SENT_CAP = 200

/**
 * Record a sent message ID. Evicts the oldest when the set exceeds the cap.
 */
export function noteSent(id: string, recentSentIds: Set<string>): void {
  recentSentIds.add(id)
  if (recentSentIds.size > RECENT_SENT_CAP) {
    const first = recentSentIds.values().next().value
    if (first) recentSentIds.delete(first)
  }
}

export function createRecentSentIds(): Set<string> {
  return new Set<string>()
}

// ── Event deduplication ────────────────────────────────────────────────────

/**
 * Track recent message IDs to skip duplicates from WSClient reconnection.
 */
export function createDeduplicator(maxSize: number = 500) {
  const seen = new Set<string>()

  return {
    isDuplicate(messageId: string): boolean {
      if (seen.has(messageId)) return true
      seen.add(messageId)
      if (seen.size > maxSize) {
        const first = seen.values().next().value
        if (first) seen.delete(first)
      }
      return false
    },
  }
}
