import { plain } from '../text'
import type { ReviewLedger, ReviewVerdict } from '../reader/progress'

/**
 * `RULE_REVIEWS.json`, read without trusting it. Two writers keep it: this deck, and the `modernize-review` command
 * for people who work without the pane. Each entry is `{ verdict, at, title?, note? }`, the note being the reviewer's
 * own words. The file sits in a workspace anyone may have edited, and a model may have written it, so every value is
 * checked: a verdict is one of three exact words, a rule id is one plain token, a title or a note is cut to one short
 * plain line, and anything else in an entry is dropped.
 */

const VERDICTS: readonly string[] = ['confirmed', 'wrong', 'discuss']

/** What a note may hold: a reviewer's sentence or two, not a document. */
export const MAX_NOTE = 500
const MAX_TITLE = 120
const MAX_ENTRIES = 5_000
const RULE_ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$/
const FORBIDDEN_ID = new Set(['__proto__', 'constructor', 'prototype'])

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)

/** The ledger a file's text holds; empty when it is not one. */
export function parseLedger(text: string | null): ReviewLedger {
  if (text === null || text.length > 4_000_000) {
    return {}
  }

  let raw: unknown

  try {
    raw = JSON.parse(text)
  } catch {
    return {}
  }

  if (!isRecord(raw) || !isRecord(raw.reviews)) {
    return {}
  }

  const ledger: ReviewLedger = {}

  for (const [id, item] of Object.entries(raw.reviews).slice(0, MAX_ENTRIES)) {
    if (!RULE_ID.test(id) || FORBIDDEN_ID.has(id) || !isRecord(item) || typeof item.verdict !== 'string' || !VERDICTS.includes(item.verdict)) {
      continue
    }

    const title = typeof item.title === 'string' ? plain(item.title, MAX_TITLE) : ''
    const note = typeof item.note === 'string' ? plain(item.note, MAX_NOTE) : ''
    // A time is kept only when it is one: the page shows its date.
    const at = typeof item.at === 'string' && /^\d{4}-\d{2}-\d{2}/.test(item.at) ? item.at.slice(0, 40) : ''

    ledger[id] = { verdict: item.verdict as ReviewVerdict, at, ...(title !== '' && { title }), ...(note !== '' && { note }) }
  }

  return ledger
}

/**
 * The file's ledger with this session's decisions on top. `edits` maps a rule id to what the deck set it to, or null when the
 * deck took its verdict back. What the other writer put in the file meanwhile stays, and a note the deck did not write is
 * kept on a rule the deck decided again.
 */
export function mergeLedger(onDisk: ReviewLedger, edits: ReadonlyMap<string, ReviewLedger[string] | null>): ReviewLedger {
  const merged: ReviewLedger = { ...onDisk }

  for (const [id, edit] of edits) {
    if (edit === null) {
      delete merged[id]
    } else {
      const note = edit.note ?? onDisk[id]?.note

      merged[id] = { ...edit, ...(note !== undefined && { note }) }
    }
  }

  return merged
}
