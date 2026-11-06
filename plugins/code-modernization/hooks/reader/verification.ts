import { plain } from '../text'
import type { TrackKey } from './tracks'

/**
 * `analysis/<system>/VERIFICATION.json`, written by the proof pack (`scripts/proof_pack.py`, run by the verify
 * command): one verdict per built module, computed by a script from the evidence files. The pane shows the verdicts
 * as they are and never computes one.
 *
 * The file is text from a run on an untrusted tree, and its shape may move between releases, so it is read
 * tolerantly: a field of the wrong type is ignored, a verdict is only ever one of the three exact words, a name or a
 * reason is cut to one short plain line, and how much is read is capped.
 */

export type Verdict = 'PROVEN' | 'PARTLY PROVEN' | 'NOT PROVEN'

const VERDICTS: readonly string[] = ['PROVEN', 'PARTLY PROVEN', 'NOT PROVEN']

/** What one module's verdict is, as the file says it. */
export type ProofEntry = {
  /** The module: a folder under `modernized/<system>/`, or the uplift's whole working copy. */
  name: string
  track: TrackKey
  verdict: Verdict
  /** The first reason the verdict is not PROVEN, as one plain line; empty when the file gives none. */
  reason: string
  /** When the module was checked; null when the file gives no time this can read. */
  atMs: number | null
}

export type Verification = {
  overall: Verdict | null
  entries: ProofEntry[]
  /** Built folders that hold only test code and the files that build it: the pack lists them and judges none, so the pane says nothing of them. */
  tooling: { track: TrackKey; name: string }[]
}

/** How the module is standing with the proof, for a chip and for the next step. */
export type ProofState = {
  /** `none`: built, and nothing checked it yet. `changed`: checked, and its code or tests are newer than that check. */
  state: 'proven' | 'partly' | 'not' | 'changed' | 'none'
  verdict?: Verdict
  reason: string
}

const MAX_TEXT = 4_000_000
const MAX_ENTRIES = 1_000
const MAX_NAME = 80
const MAX_REASON = 160

/** The proof pack's own spelling of a track: a rewrite is `rewrite` there. */
const TRACK_OF: Record<string, TrackKey> = { rewrite: 'transform', transform: 'transform', uplift: 'uplift', reimagine: 'reimagine' }

/** `2026-09-24 20:31 UTC` (the pack's stamp) as milliseconds since the epoch; null when it is anything else. */
function timeOf(value: unknown): number | null {
  if (typeof value !== 'string') {
    return null
  }

  const match = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?\s*(?:UTC|Z)?$/.exec(value.trim())

  if (match === null) {
    return null
  }

  const ms = Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]), Number(match[4]), Number(match[5]), Number(match[6] ?? 0))

  return Number.isFinite(ms) ? ms : null
}

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)

/** The file's text as a Verification; null when it is not one. */
export function parseVerification(text: string): Verification | null {
  if (text.length > MAX_TEXT) {
    return null
  }

  let raw: unknown

  try {
    raw = JSON.parse(text)
  } catch {
    return null
  }

  if (!isRecord(raw) || !Array.isArray(raw.modules)) {
    return null
  }

  const entries: ProofEntry[] = []

  for (const item of raw.modules.slice(0, MAX_ENTRIES) as unknown[]) {
    if (!isRecord(item)) {
      continue
    }

    const name = typeof item.name === 'string' ? plain(item.name, MAX_NAME) : ''
    const track = typeof item.track === 'string' ? TRACK_OF[item.track] : undefined

    // Only the exact words count: a verdict with anything added to it is not one.
    if (name === '' || track === undefined || typeof item.verdict !== 'string' || !VERDICTS.includes(item.verdict)) {
      continue
    }

    const first = Array.isArray(item.reasons) ? (item.reasons as unknown[]).find(reason => typeof reason === 'string' && reason.trim() !== '') : undefined

    entries.push({
      name,
      track,
      verdict: item.verdict as Verdict,
      reason: typeof first === 'string' ? plain(first, MAX_REASON) : '',
      atMs: timeOf(item.verifiedAt),
    })
  }

  const overall = isRecord(raw.overall) && typeof raw.overall.verdict === 'string' && VERDICTS.includes(raw.overall.verdict) ? (raw.overall.verdict as Verdict) : null
  const tooling: Verification['tooling'] = []

  for (const item of (Array.isArray(raw.toolingOnly) ? (raw.toolingOnly as unknown[]) : []).slice(0, MAX_ENTRIES)) {
    const name = isRecord(item) && typeof item.name === 'string' ? plain(item.name, MAX_NAME) : ''
    const track = isRecord(item) && typeof item.track === 'string' && Object.hasOwn(TRACK_OF, item.track) ? TRACK_OF[item.track] : undefined

    if (name !== '' && track !== undefined) {
      tooling.push({ track, name })
    }
  }

  return { overall, entries, tooling }
}

/** The pack stamps minutes; a file written in the same minute as the check is not newer than it. */
const SLACK_MS = 90_000

/**
 * Where a built module stands with the proof. Null when it has no notes and no verdict, so nothing is claimed of a
 * module still being built, and null for a folder the pack lists as test tooling (only test code and build files: nothing to prove).
 *
 * @param verification the file, or null when there is none
 * @param track the track the pane follows
 * @param name the module's folder under `modernized/`
 * @param changedAtMs when the module's notes or test reports last changed (0 when unknown)
 * @param hasNotes whether the module has notes: the sign a module was finished being built
 */
export function proofOfModule(
  verification: Verification | null,
  track: TrackKey,
  name: string,
  changedAtMs: number,
  hasNotes: boolean,
): ProofState | null {
  const entry = verification?.entries.find(candidate => candidate.track === track && candidate.name.toLowerCase() === plain(name, MAX_NAME).toLowerCase())

  if (entry === undefined) {
    const isTooling = verification?.tooling.some(item => item.track === track && item.name.toLowerCase() === plain(name, MAX_NAME).toLowerCase()) === true

    return hasNotes && !isTooling ? { state: 'none', reason: '' } : null
  }

  if (entry.atMs !== null && changedAtMs > entry.atMs + SLACK_MS) {
    return { state: 'changed', verdict: entry.verdict, reason: entry.reason }
  }

  return { state: entry.verdict === 'PROVEN' ? 'proven' : entry.verdict === 'PARTLY PROVEN' ? 'partly' : 'not', verdict: entry.verdict, reason: entry.reason }
}
