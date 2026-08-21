/**
 * Durable inbound log.
 *
 * The channel delivers inbound messages to Claude as fire-and-forget MCP
 * notifications. If no client is attached (crash, /reload-plugins, or a dropped
 * transport while server.ts keeps polling), that notification has nowhere to go
 * and the message is lost — attachments survive in inbox/, but text did not.
 *
 * This module persists every inbound to an append-only JSONL log and tracks a
 * "delivered cursor". On the next session connect the server replays everything
 * past the cursor, so a disconnect no longer drops messages. Pure fs helpers,
 * no grammy/MCP deps, so they're unit-testable in isolation.
 */
import { appendFileSync, readFileSync, writeFileSync, mkdirSync } from 'fs'
import { dirname } from 'path'

export type InboundRecord = {
  seq: number
  ts: string
  /** The MCP notification params: { content, meta }. Opaque here. */
  params: unknown
}

function ensureDir(file: string): void {
  mkdirSync(dirname(file), { recursive: true, mode: 0o700 })
}

/** Parse the whole log, skipping any torn/corrupt line rather than throwing. */
export function readAllInbound(logPath: string): InboundRecord[] {
  let raw: string
  try {
    raw = readFileSync(logPath, 'utf8')
  } catch {
    return []
  }
  const out: InboundRecord[] = []
  for (const line of raw.split('\n')) {
    if (!line.trim()) continue
    try {
      const rec = JSON.parse(line) as InboundRecord
      if (typeof rec.seq === 'number') out.push(rec)
    } catch {
      // A crash mid-append can leave a partial final line — skip it.
    }
  }
  return out
}

/** Highest seq in the log, so a fresh process resumes the counter (0 if empty). */
export function maxSeq(logPath: string): number {
  let m = 0
  for (const r of readAllInbound(logPath)) if (r.seq > m) m = r.seq
  return m
}

export function appendInbound(logPath: string, rec: InboundRecord): void {
  ensureDir(logPath)
  appendFileSync(logPath, JSON.stringify(rec) + '\n', { mode: 0o600 })
}

/** Records logged after `sinceSeq` — i.e. everything not yet delivered. */
export function readInboundSince(logPath: string, sinceSeq: number): InboundRecord[] {
  return readAllInbound(logPath).filter(r => r.seq > sinceSeq)
}

/** Trim the log to its most recent `keep` records. No-op if already smaller. */
export function pruneInbound(logPath: string, keep: number): void {
  const recs = readAllInbound(logPath)
  if (recs.length <= keep) return
  const tail = recs.slice(recs.length - keep)
  ensureDir(logPath)
  writeFileSync(logPath, tail.map(r => JSON.stringify(r)).join('\n') + '\n', { mode: 0o600 })
}

export function loadCursor(cursorPath: string): number {
  try {
    return parseInt(readFileSync(cursorPath, 'utf8').trim(), 10) || 0
  } catch {
    return 0
  }
}

export function saveCursor(cursorPath: string, seq: number): void {
  ensureDir(cursorPath)
  writeFileSync(cursorPath, String(seq) + '\n', { mode: 0o600 })
}
