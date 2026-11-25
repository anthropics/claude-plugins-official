// The key under which a project-wide theme is kept, made so that a session in a linked git worktree meets the choice of its project.
// Seven steps, (k1) to (k7). Every step that fails ends in the key every earlier version used: the prefix, then the session's root as answered.
// The first two calls are not caught here: register.tsx catches them, to the same end.
// (d3) to (d5) say what is kept in the process and which keys a read, a write and a clear take.
// Erasable TypeScript only, no import: it runs under node's own type stripping.

/** What the stat of the engine answers. A missing or withheld path is a rejection, not an answer. */
export interface StatAnswer {
  kind: 'file' | 'directory' | 'other'
  /** Absolute, every link followed. Absent where the engine gives none. */
  realPath?: string
}

/** The four calls of the engine the key is made from. register.tsx binds them to the engine's own names. */
export interface KeyEngine {
  root(): Promise<string>
  cwd(): Promise<string>
  /** The root inside the repository of the session; null outside one. It may reject on an older engine. */
  repo(): Promise<string | null>
  stat(path: string): Promise<StatAnswer>
}

export type KeyStep =
  | 'k1-cwd-apart'
  | 'k2-no-repository'
  | 'k3-no-real-path'
  | 'k4-no-entry'
  | 'k5-main-tree'
  | 'k6-own-root'
  | 'k6-other-marker'
  | 'k6-cwd-spelling'
  | 'k6-linked-worktree'
  | 'k7-other-kind'

export interface KeyAnswer {
  /** Read first; the only key that is written. */
  key: string
  /** (d4) the key of today, read behind `key` and cleared with it; null where it must not be read. */
  olderKey: string | null
  /** (d3) false: valid for this ask alone, asked again when the next turn begins. */
  keep: boolean
  /** Which end of the seven steps gave the key. For tests and a debug line. */
  step: KeyStep
}

/** (d3) what is kept in the process beside the root it was made for. */
export interface KeptKey {
  forRoot: string
  answer: KeyAnswer
}

/** (k4) a fixed cap beside the count of separators: it guards a loop that should not be. */
export const WALK_CAP = 64

const ENTRY_NAME = '.git'

function lastSeparatorIndex(path: string): number {
  return Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\'))
}

function separatorOf(path: string): string {
  return path.includes('/') ? '/' : '\\'
}

function countSeparators(path: string): number {
  let count = 0
  for (const sign of path) {
    if (sign === '/' || sign === '\\') count += 1
  }
  return count
}

function isBelow(path: string, folder: string): boolean {
  return path.startsWith(folder + '/') || path.startsWith(folder + '\\')
}

function isAtOrBelow(path: string, folder: string): boolean {
  return path === folder || isBelow(path, folder)
}

async function statOrNull(
  engine: KeyEngine,
  path: string,
): Promise<StatAnswer | null> {
  try {
    return await engine.stat(path)
  } catch {
    return null
  }
}

async function realPathOrNull(
  engine: KeyEngine,
  path: string,
): Promise<string | null> {
  const answer = await statOrNull(engine, path)
  return answer?.realPath ?? null
}

async function repoOrNull(engine: KeyEngine): Promise<string | null> {
  try {
    return await engine.repo()
  } catch {
    return null
  }
}

function keyOfToday(
  prefix: string,
  rootAsAnswered: string,
  keep: boolean,
  step: KeyStep,
): KeyAnswer {
  return { key: prefix + rootAsAnswered, olderKey: null, keep, step }
}

/** (k5) and the first two ends of (k6): the real path of the root, the key of today behind it where the strings part. */
function keyOfRealRoot(
  prefix: string,
  rootAsAnswered: string,
  realRoot: string,
  step: KeyStep,
): KeyAnswer {
  const key = prefix + realRoot
  const today = prefix + rootAsAnswered
  return { key, olderKey: today === key ? null : today, keep: true, step }
}

interface WalkFind {
  top: string
  kind: StatAnswer['kind']
}

/** (k4) from the real root upward, one stat a step on the entry; a rejected step counts as no entry. */
async function findWorkingTreeTop(
  engine: KeyEngine,
  realRoot: string,
): Promise<WalkFind | null> {
  const steps = Math.min(countSeparators(realRoot), WALK_CAP)
  let folder = realRoot
  for (let step = 0; step < steps; step += 1) {
    const entry = await statOrNull(
      engine,
      folder + separatorOf(realRoot) + ENTRY_NAME,
    )
    if (entry !== null) return { top: folder, kind: entry.kind }
    const cut = lastSeparatorIndex(folder)
    if (cut <= 0) return null
    folder = folder.slice(0, cut)
  }
  return null
}

/** The seven steps. Every step that fails ends in the key of today; a rejection of the first two calls is the caller's to catch. It reads; it writes and keeps nothing. */
export async function makeProjectKey(
  engine: KeyEngine,
  prefix: string,
): Promise<KeyAnswer> {
  const rootAsAnswered = await engine.root()
  const cwdAsAnswered = await engine.cwd()

  const realRoot = await realPathOrNull(engine, rootAsAnswered)
  if (realRoot === null)
    return keyOfToday(prefix, rootAsAnswered, true, 'k3-no-real-path')
  const realCwd = await realPathOrNull(engine, cwdAsAnswered)
  if (realCwd !== realRoot)
    return keyOfToday(prefix, rootAsAnswered, false, 'k1-cwd-apart')

  const repoAsAnswered = await repoOrNull(engine)
  if (repoAsAnswered === null)
    return keyOfToday(prefix, rootAsAnswered, true, 'k2-no-repository')

  const realRepo = await realPathOrNull(engine, repoAsAnswered)
  if (realRepo === null)
    return keyOfToday(prefix, rootAsAnswered, true, 'k3-no-real-path')

  const find = await findWorkingTreeTop(engine, realRoot)
  if (find === null)
    return keyOfToday(prefix, rootAsAnswered, true, 'k4-no-entry')

  if (find.kind === 'directory')
    return keyOfRealRoot(prefix, rootAsAnswered, realRoot, 'k5-main-tree')
  if (find.kind !== 'file')
    return keyOfToday(prefix, rootAsAnswered, true, 'k7-other-kind')

  if (realRepo === find.top)
    return keyOfRealRoot(prefix, rootAsAnswered, realRoot, 'k6-own-root')
  if (isBelow(realRepo, find.top) && isAtOrBelow(realRoot, realRepo)) {
    return keyOfRealRoot(prefix, rootAsAnswered, realRoot, 'k6-other-marker')
  }
  // The belt: the engine climbed from a spelling that is not the real one. Folded to one unicode form for this one compare alone.
  if (cwdAsAnswered.normalize('NFC') !== realCwd.normalize('NFC')) {
    return keyOfToday(prefix, rootAsAnswered, true, 'k6-cwd-spelling')
  }
  const restBelowTop = realRoot.slice(find.top.length)
  return {
    key: prefix + realRepo + restBelowTop,
    olderKey: null,
    keep: true,
    step: 'k6-linked-worktree',
  }
}

export interface KeyLookup {
  answer: KeyAnswer
  kept: KeptKey | null
}

/** (d3) made once and kept beside the root; made again only when the root has moved, or where nothing was kept. */
export async function projectKeyFor(
  engine: KeyEngine,
  prefix: string,
  kept: KeptKey | null,
): Promise<KeyLookup> {
  const rootAsAnswered = await engine.root()
  if (kept !== null && kept.forRoot === rootAsAnswered)
    return { answer: kept.answer, kept }
  const answer = await makeProjectKey(engine, prefix)
  return {
    answer,
    kept: answer.keep ? { forRoot: rootAsAnswered, answer } : null,
  }
}

/** (d4) the order of a read: the first key that holds a pick wins. */
export function keysToRead(answer: KeyAnswer): string[] {
  return answer.olderKey === null ? [answer.key] : [answer.key, answer.olderKey]
}

/** (d5) a write goes to the new key alone. */
export function keyToWrite(answer: KeyAnswer): string {
  return answer.key
}

/** (d5) a clear project-wide takes both where both are read, else the older pick comes back at the next read. */
export function keysToClear(answer: KeyAnswer): string[] {
  return keysToRead(answer)
}
