import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, Timer } from 'claude-code'

import {
  NIGHT_GLASS,
  NIGHT_ID,
  SHOW_SUFFIXES,
  WORD,
  nightScene,
  sceneWithFireworks,
  themeIdOfShow,
} from './fireworks'
import { keyToWrite, keysToClear, keysToRead, projectKeyFor } from './project-key'
import type { KeptKey, KeyEngine } from './project-key'
import { THEMES, sceneFault, sceneOf } from './themes'
import type { Theme } from './themes'
import type { ThemeChoice } from '../types'

const PLUGIN = 'theme-examples'
const CARD = 'theme-card'
// Not `theme`: that is the engine's own command (the terminal's color theme).
const COMMAND = 'custom-theme'
const PREVIEW_MS = 20_000
const FIREWORKS_COMMAND = 'fireworks'
const SHOW_MS = 7000
// Holds 'off' where the person turned the show on the word off; absent, it is on. One key for every session and project.
const AUTO_KEY = 'fireworks:auto'
const SESSION_PREFIX = 'session:'
// How many sessions' own choices the store keeps: past it, the one written longest ago goes.
const SESSIONS_KEPT = 200
// Said where a theme is set and the engine answers that nothing draws it. That answer is what the attached windows said of themselves at the moment of
// the set: one that attaches later still draws the theme, and one that draws themes under another name than this engine asks after draws it all the
// same. An engine with none of the three calls is answered the same way (setBackdrop's last line), and there nothing draws it. So the words hold
// whether or not the theme shows, and never say why.
const UNSHOWN = 'If no theme shows, this window may not draw themes yet'
const KEPT_UNSHOWN = `${UNSHOWN}. Your choice is saved.`
const SHOW_UNSHOWN = 'If none shows, this window may not draw them yet.'
// The module's own variables start over on a reload: so does a show in flight, which is fine for a show.
// `starting` from the tick a show is asked for until its timer stands: see `fireworks`.
let showEnding: Timer | 'starting' | undefined
let showCount = 0
let previewEnding: Timer | undefined
// The loader's scan reads this reference: both names are written as string literals.
const choice = atom({ plugin: 'theme-examples', key: 'choice' } as const, {}, {
  shape: 'choice-1',
})

/** What a set comes to on any engine, as far as this mod reads it: drawn or not. */
type BackdropAnswer = { isDrawn: boolean }
type BackdropChoice = { id: string; glass: Theme['glass']; colorScheme?: Theme['window'] }
/** The engines this mod meets, for the type checker alone: the theme noun or the older call may be absent. */
type AnyEngine = {
  theme?: { set(args: unknown): Promise<BackdropAnswer>; clear(): Promise<unknown> }
  // `toast` is named only so that this type shares a member with every engine's ui noun: the checker refuses one that shares none.
  ui: { toast: EngineInterface['ui']['toast']; backdrop?(args: BackdropChoice | undefined): Promise<BackdropAnswer> }
}
// The way of setting a backdrop this engine took, learnt at the first set that can tell; a reload learns it again.
let taken: 'beside' | 'nested' | 'older' | 'none' | undefined

/**
 * A try may be followed by the next one only where the engine lacks the call (reaching for it throws a TypeError) or
 * refuses the shape as one it does not know: in its own words for that, or by naming the member that this try alone
 * bears, should those words ever move. Any other fault is the caller's to see.
 * NO CALL IS ASKED AFTER AHEAD OF ITS TRY: the engine loads a module only where each call on its handle is called on the
 * spot; one that is read, bound or passed keeps the whole module from loading. So each is made, and its fault judged.
 */
function isNotThisEnginesWay(error: unknown, member?: string): boolean {
  return (
    error instanceof TypeError ||
    (error instanceof Error &&
      (error.message.includes('does not know the attribute') || (member !== undefined && error.message.includes(member))))
  )
}

/**
 * Sets a backdrop by whichever call this engine has: the theme noun with the window's kind beside the backdrop, the
 * theme noun with it inside the backdrop, or the older call on the ui noun. The calls are written out plainly, each in
 * its own try: a call the engine lacks throws as it is reached for, and a shape it does not take it refuses. THE NEWEST FIRST: an engine that
 * wants the kind beside the backdrop takes the one inside it too, and drops it without a word.
 * THE SCENE's NAME GOES UNDER TWO NAMES AT ONCE in the newest shape: the newest engines read `scene`, the ones before
 * them `id`. Each engine's own theme noun lets the members it knows cross and drops any other, so one shape serves both;
 * a backdrop with the one name alone is refused by the engines that read the other, in words that name no unknown attribute.
 * Answers nothing where no way was taken.
 */
async function setByAWay($: AnyEngine, backdrop: BackdropChoice): Promise<BackdropAnswer | undefined> {
  if (taken === undefined || taken === 'beside') {
    try {
      const set = await $.theme!.set({
        backdrop: { scene: backdrop.id, id: backdrop.id, glass: backdrop.glass },
        ...(backdrop.colorScheme !== undefined && { overrideColorScheme: backdrop.colorScheme }),
      })

      // With no kind to hand over this shape is the next one's too: it tells nothing of the engine, so nothing is learnt.
      // A belt: learnt wrongly here, the next set with a kind would be refused once and the ways walked anew.
      if (backdrop.colorScheme !== undefined) {
        taken = 'beside'
      }

      return set
    } catch (error) {
      if (!isNotThisEnginesWay(error, 'overrideColorScheme')) throw error
    }
  }

  if (taken === undefined || taken === 'nested') {
    try {
      const set = await $.theme!.set({
        backdrop: {
          id: backdrop.id,
          glass: backdrop.glass,
          ...(backdrop.colorScheme !== undefined && { colorScheme: backdrop.colorScheme }),
        },
      })
      taken = 'nested'

      return set
    } catch (error) {
      if (!isNotThisEnginesWay(error)) throw error
    }
  }

  if (taken === undefined || taken === 'older') {
    try {
      // The older call is given the id and the glass alone.
      const set = await $.ui.backdrop!({ id: backdrop.id, glass: backdrop.glass })
      taken = 'older'

      return set
    } catch (error) {
      if (!isNotThisEnginesWay(error)) throw error
    }
  }

  return undefined
}

/**
 * A way once learnt is the only one tried. Where the engine does not take it after all the ways are walked anew; an
 * engine with none of them draws nothing, and the answer says so.
 */
async function setBackdrop($: AnyEngine, backdrop: BackdropChoice): Promise<BackdropAnswer> {
  if (taken === 'none') {
    return { isDrawn: false }
  }

  const learnt = taken
  const set = await setByAWay($, backdrop)

  if (set !== undefined) {
    return set
  }

  if (learnt !== undefined) {
    taken = undefined

    const again = await setByAWay($, backdrop)

    if (again !== undefined) {
      return again
    }
  }

  taken = 'none'

  return { isDrawn: false }
}

/** Clears the backdrop by whichever call this engine has; an engine with neither is left alone. */
async function clearBackdrop($: AnyEngine): Promise<void> {
  try {
    await $.theme!.clear()

    return
  } catch (error) {
    if (!isNotThisEnginesWay(error)) throw error
  }

  try {
    await $.ui.backdrop!(undefined)
  } catch (error) {
    if (!isNotThisEnginesWay(error)) throw error
  }
}

/**
 * The scene's name as the engine hands it to the Backdrop hook: under `scene` on the newest engines, under `id` on the
 * ones before them. Read under either, the newer first: a hook that knew the one name alone would find no theme on the
 * other engines and pass the ask on, and nothing would say so.
 */
function sceneNameOf(props: { scene?: unknown; id?: unknown }): string | undefined {
  if (typeof props.scene === 'string') {
    return props.scene
  }

  return typeof props.id === 'string' ? props.id : undefined
}

function themeOf(id: string | undefined): Theme | undefined {
  return THEMES.find(theme => theme.id === id)
}

/** A name as typed, a title as shown and an id all come to one key: lower case, each run of anything else a hyphen. */
function keyOf(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

/** The theme a person named: by its id or its title, in any case, with spaces or hyphens between the words. */
function themeNamed(text: string): Theme | undefined {
  const key = keyOf(text)

  return THEMES.find(theme => theme.id === key || keyOf(theme.title) === key)
}

/** How many single-letter edits turn one word into the other. */
function editsBetween(from: string, to: string): number {
  let row = Array.from({ length: to.length + 1 }, (_, column) => column)

  for (let line = 1; line <= from.length; line += 1) {
    const next = [line]

    for (let column = 1; column <= to.length; column += 1) {
      const swap = (row[column - 1] ?? 0) + (from[line - 1] === to[column - 1] ? 0 : 1)

      next.push(Math.min(swap, (row[column] ?? 0) + 1, (next[column - 1] ?? 0) + 1))
    }

    row = next
  }

  return row[to.length] ?? 0
}

/**
 * The theme whose name is nearest a mistyped one. A few edits away speaks first (one id can be the start of another:
 * plotter-tide and plotter-tide-night); else the longest id the typed name starts with (a name with a wrong word behind
 * it); else the first id that starts with what was typed; else none.
 */
function nearestTheme(text: string): Theme | undefined {
  const key = keyOf(text)

  if (key === '') return undefined

  const byEdits = THEMES.map(theme => ({ theme, edits: editsBetween(key, theme.id) })).sort(
    (one, other) => one.edits - other.edits,
  )
  const nearest = byEdits[0]

  if (nearest !== undefined && nearest.edits <= Math.max(2, Math.floor(key.length / 3))) {
    return nearest.theme
  }

  const startsIt = THEMES.filter(theme => key.startsWith(theme.id)).sort(
    (one, other) => other.id.length - one.id.length,
  )

  return startsIt[0] ?? THEMES.find(theme => theme.id.startsWith(key))
}

/** The two kinds of window, in the order the list and the card show them. */
const WINDOWS = ['dark', 'light'] as const

/** The themes made for one kind of window, a row each: the name to type, its title, what it is, and its twin's name. */
function rowsFor(window: Theme['window']): string[] {
  return THEMES.filter(theme => theme.window === window).map(theme => {
    const twin = themeOf(theme.twin)

    return `  ${theme.id}: ${theme.title}. ${theme.blurb}${twin === undefined ? '' : ` (for ${twin.window} windows: ${twin.id})`}`
  })
}

/** Every theme by the name to type, under the window it is made for. */
function themeList(): string {
  return [
    `Theme examples (${THEMES.length}):`,
    ...WINDOWS.flatMap(window => [`For ${window} windows:`, ...rowsFor(window)]),
    `Apply one with /${COMMAND} <name>, add "session" for this session only, /${COMMAND} off clears it.`,
  ].join('\n')
}

/**
 * Shows a theme behind the chat, or with none clears the session's theme, and answers what a set came to.
 * A clear takes away whatever theme stands, whichever mod set it, so `show` is given none only on a person's ask
 * (off, a preview's end, a show's end) or to take a theme of this mod's own away, never over a window it left bare.
 */
async function show($: EngineInterface, id: string | undefined): Promise<BackdropAnswer | undefined> {
  const theme = themeOf(id)

  if (theme === undefined) {
    await clearBackdrop($)

    return undefined
  }

  return setBackdrop($, { id: theme.id, glass: theme.glass, colorScheme: theme.window })
}

const PROJECT_PREFIX = 'project:'

// The key made for a root is kept beside that root and made again only when the root has moved. A reload starts it over.
let keptProjectKey: KeptKey | null = null
// The end last told to the log: told again only when it changes, so a turn's start adds no line.
let toldKeyStep: string | undefined

/**
 * Says which end of the seven steps gave the project's key, or that the making failed: no path and no key.
 * TO THE DEBUG LOG ALONE: with no option the engine's log call appends a line to the person's transcript.
 * The engine leads every such line with the plugin's name: the text does not say it again.
 */
async function tellKeyStep($: EngineInterface, step: string): Promise<void> {
  if (step === toldKeyStep) {
    return
  }

  toldKeyStep = step

  try {
    await $.ui.log(`the project's key came by ${step}`, { to: 'debug' })
  } catch {
    // An engine without that call, or one that refuses it: nothing more to tell.
  }
}

/** The engine's four calls as the key's maker asks them: the repository's root alone, and the stat's `dir` as its `directory`. */
function keyEngineOf($: EngineInterface): KeyEngine {
  return {
    root: () => $.session.root(),
    cwd: () => $.session.cwd(),
    repo: async () => (await $.session.repo())?.root ?? null,
    stat: async path => {
      const { kind, realPath } = await $.fs.stat(path, { resolve: true })
      const told = kind === 'dir' ? 'directory' : kind

      return realPath === undefined ? { kind: told } : { kind: told, realPath }
    },
  }
}

/** The keys a project's choice is read under, in order; the one it is written under; the ones a clear takes away. */
type ProjectKeys = { read: string[]; write: string; clear: string[] }

/**
 * One choice per project: a session in a linked git worktree shares the key of the matching folder in the main tree.
 * A fault nobody foresaw in the making ends where each foreseen one does: in the key every earlier version used.
 */
async function projectKeys($: EngineInterface): Promise<ProjectKeys> {
  try {
    const found = await projectKeyFor(keyEngineOf($), PROJECT_PREFIX, keptProjectKey)

    keptProjectKey = found.kept
    await tellKeyStep($, found.answer.step)

    return { read: keysToRead(found.answer), write: keyToWrite(found.answer), clear: keysToClear(found.answer) }
  } catch {
    const today = `${PROJECT_PREFIX}${await $.session.root()}`

    await tellKeyStep($, 'fault')

    return { read: [today], write: today, clear: [today] }
  }
}

/** What the store keeps for one session: its own theme's id, or null where it chose none. */
type SessionChoice = { theme: string | null }

/** An id an engine may not offer: a fault counts as no answer. */
async function orNothing(ask: () => Promise<string | undefined>): Promise<string | undefined> {
  try {
    return await ask()
  } catch {
    return undefined
  }
}

/**
 * The key a session's own choice is stored under: one per row a person sees in the desktop app, else one per
 * Claude Code session. An empty id counts as none. With neither id there is no key, and the choice lasts as long
 * as this process does.
 */
async function sessionKey($: EngineInterface): Promise<string | undefined> {
  const id =
    // The desktop app's own name for its row, unpromised: it outlives /clear and an archive. Unset (the terminal, another app), the next line serves.
    (await orNothing(() => $.env.get('CLAUDE_CODE_HOST_SESSION_ID'))) ||
    (await orNothing(() => $.session.id()))

  return id === undefined || id === '' ? undefined : `${SESSION_PREFIX}${id}`
}

/** The choice stored under a session's key, or nothing: none was made, or its theme is no longer in the table. */
async function sessionChoice($: EngineInterface, key: string): Promise<SessionChoice | undefined> {
  const stored = await $.store.get(key)

  if (typeof stored !== 'object' || stored === null || !('theme' in stored)) {
    return undefined
  }

  const theme = stored.theme

  return theme === null || (typeof theme === 'string' && themeOf(theme) !== undefined) ? { theme } : undefined
}

/**
 * Stores a session's own choice. The key is taken out first, so that the store's order is the order of the last
 * writes and the cap drops the session that chose longest ago. Those are two writes: where the second fails, what
 * stood is put back as far as the store lets it, so that a choice that was not applied does not cost the earlier one.
 * The cap is housekeeping: its fault costs the choice nothing.
 */
async function keepForSession($: EngineInterface, key: string, id: string | undefined): Promise<void> {
  const kept: SessionChoice = { theme: id ?? null }
  const stood = await $.store.get(key)

  await $.store.delete(key)

  try {
    await $.store.set(key, kept)
  } catch (error) {
    if (stood !== undefined) {
      try {
        await $.store.set(key, stood)
      } catch {
        // The first fault is the one to tell.
      }
    }

    throw error
  }

  try {
    const keys = (await $.store.keys()).filter(name => name.startsWith(SESSION_PREFIX))

    for (const oldest of keys.slice(0, Math.max(0, keys.length - SESSIONS_KEPT))) {
      await $.store.delete(oldest)
    }
  } catch {
    // The next choice tries again.
  }
}

/**
 * THE ONE WAY this mod changes which theme stands behind the chat: nothing else calls `show`.
 * It asks the engine for a theme (or none) and only then keeps the choice: `keep` writes the store or the state.
 * A set the engine refuses throws here with nothing written and what stood still shown. Where `keep` fails, the
 * window is put back to what stood, so that what a person sees and what they are told agree, and that first
 * fault is thrown on, whatever the put-back comes to. Each caller words its own plain sentence from the fault.
 * It answers what the set came to: a set the engine takes may be drawn by no surface, and the choice is kept all the
 * same (the engine hands what stands to a client that joins the session later and draws backdrops). A caller with a
 * person to tell says so; one that runs unasked stays quiet.
 */
async function showThenKeep(
  $: EngineInterface,
  id: string | undefined,
  keep?: () => Promise<unknown>,
): Promise<BackdropAnswer | undefined> {
  const stood = await read($, choice)
  const set = await show($, id)

  try {
    await keep?.()
  } catch (error) {
    try {
      await show($, stood.preview ?? stood.applied)
    } catch {
      // The first fault is the one to tell.
    }

    throw error
  }

  return set
}

/**
 * Applies a theme (or none) to this session, and with `forProject` to every later session of the project.
 * A choice for this session alone is stored under the session's key; one for the project takes that key away.
 */
async function apply(
  $: EngineInterface,
  id: string | undefined,
  forProject: boolean,
): Promise<BackdropAnswer | undefined> {
  return showThenKeep($, id, async () => {
    const own = await sessionKey($)

    // The session's key first: where that fails, nothing is written for the project, and "could not be applied" is true.
    if (own !== undefined) {
      await (forProject ? $.store.delete(own) : keepForSession($, own, id))
    }

    if (forProject) {
      const keys = await projectKeys($)

      if (id === undefined) {
        for (const key of keys.clear) {
          await $.store.delete(key)
        }
      } else {
        await $.store.set(keys.write, id)
      }
    }

    await update($, choice, (was): ThemeChoice => ({
      cardInBand: was.cardInBand,
      cardAway: was.cardAway,
      applied: id,
      scope: forProject ? 'project' : 'session',
    }))
  })
}

/** A fault's own words. */
function reasonOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

/**
 * Runs a step that must never cost a person their start or their prompt: its fault is told in one dim line of the
 * transcript, which is not sent to the model: the one sign a person gets. No toast: one at every turn would nag.
 */
async function quietly($: EngineInterface, step: () => Promise<void>): Promise<void> {
  try {
    await step()
  } catch (error) {
    try {
      await $.ui.log(`a step nobody waits on failed, and the window stays as it is (${reasonOf(error)})`)
    } catch {
      // An engine without that call, or one that refuses it: nothing more to tell.
    }
  }
}

/**
 * What is said where a theme is set that no surface draws. Only a project's choice is said to be saved: it is always
 * stored. A session's own is stored under the id of the moment, and with no id not at all. No place is promised.
 */
function unshownNote(isSaved: boolean): string {
  return isSaved ? KEPT_UNSHOWN : `${UNSHOWN}.`
}

/** What became of a pick: a fault's one plain sentence; or none, and whether a theme was set that no surface draws. */
type Picked = { fault: string } | { fault: undefined; isUnshown: boolean }

/**
 * Applies what a person picked, a theme or none, or says in one plain sentence why it could not: a scene that does
 * not build, a set the engine refuses, a store that fails, in the fault's own words. A person must read why, not the
 * engine's hint for authors. Nothing is kept then and the theme that stood stays.
 * A clear promises nothing to see, so it is never unshown.
 */
async function applyOrSay(
  $: EngineInterface,
  theme: Theme | undefined,
  forProject: boolean,
): Promise<Picked> {
  const fault = theme === undefined ? undefined : sceneFault(theme)

  if (theme !== undefined && fault !== undefined) {
    return { fault: `${theme.title} could not be drawn: ${fault}` }
  }

  try {
    const set = await apply($, theme?.id, forProject)

    return { fault: undefined, isUnshown: set?.isDrawn === false }
  } catch (error) {
    return {
      fault:
        theme === undefined
          ? `The theme could not be cleared: ${reasonOf(error)}`
          : `${theme.title} could not be applied: ${reasonOf(error)}`,
    }
  }
}

/** The project's stored choice: a theme's id, or none. The first key that holds one wins. */
async function projectChoice($: EngineInterface): Promise<string | undefined> {
  for (const key of (await projectKeys($)).read) {
    const stored = await $.store.get(key)

    if (typeof stored === 'string' && themeOf(stored) !== undefined) {
      return stored
    }
  }

  return undefined
}

/**
 * Brings a session to the choice it is due: at a start, and at each turn's start, so that a session open while
 * another one changed the project takes the change at its next turn.
 * A session with a choice of its own in this process is left alone. A choice kept before the scope was is the
 * session's own where it differs from the project's (it can only have come from this session), else the project's.
 * A session whose own choice an earlier process stored takes that up again. Any other follows its project.
 * ONE RULE FOR THE TWO IDS: the key of the moment is the only one read or written. Where this process holds the
 * session's own choice and the store holds nothing under that key (the app's id came late), the choice is written
 * there: the same process, so nothing is guessed. No choice is ever looked for under another key.
 */
async function followChoice($: EngineInterface): Promise<void> {
  const now = await read($, choice)
  const project = await projectChoice($)
  const isOwn = now.scope === 'session' || (now.scope === undefined && now.applied !== undefined && now.applied !== project)

  if (now.preview !== undefined || showEnding !== undefined) {
    return
  }

  const key = await sessionKey($)
  const kept = key === undefined ? undefined : await sessionChoice($, key)

  if (isOwn) {
    if (key !== undefined && kept === undefined) {
      await keepForSession($, key, now.applied)
    }

    return
  }

  if (kept !== undefined) {
    const own = kept.theme ?? undefined
    const take = (): Promise<unknown> =>
      update($, choice, (was): ThemeChoice => ({ ...was, applied: own, scope: 'session' }))

    // None chosen and none shown: the engine is asked nothing, or a clear would take another mod's theme away.
    await (own === undefined && now.applied === undefined ? take() : showThenKeep($, own, take))

    return
  }

  if (now.applied === project) {
    return
  }

  // Asked first: a theme the engine refuses is not taken as applied, and the next turn tries it again.
  await showThenKeep($, project, () =>
    update($, choice, (was): ThemeChoice => ({ ...was, applied: project, scope: 'project' })),
  )
}

/**
 * Ends a look at a theme unless it was applied meanwhile: back to what the session shows.
 * An end runs from a timer, with nobody to tell: it runs `quietly`. One that comes after the mod is unloaded or the
 * session is over is refused by the engine, and so is its note: nothing is left for the mod to do.
 */
async function endPreview($: EngineInterface, id: string): Promise<void> {
  previewEnding = undefined

  const later = await read($, choice)

  if (later.preview === id) {
    await showThenKeep($, later.applied, () => update($, choice, was => ({ ...was, preview: undefined })))
  }
}

/**
 * Ends a show: back to the theme the session shows, or to no backdrop where it has none.
 * The flag is let go only once the window is back, however that went: an ask that came while the end waited on the
 * engine would else start a show that this end then draws over.
 */
async function endFireworks($: EngineInterface): Promise<void> {
  try {
    const later = await read($, choice)

    await showThenKeep($, later.preview ?? later.applied)
  } finally {
    showEnding = undefined
  }
}

/**
 * Seven seconds of fireworks: over the session's theme where it has one, else over a night sky of their own.
 * ONE SHOW AT A TIME: a word or a command that comes while a show runs starts nothing and lengthens nothing, so
 * however often the word is said the window changes twice in a show's seconds and no oftener.
 * The flag is TAKEN IN THE SAME TICK AS IT IS TESTED, ahead of the first await: a command and a reply's block come on
 * their own clocks, and a second ask that came while the first waited on the engine would else pass the test too.
 * KNOWN: the timer's call stands outside the try. It throws only where the mod is already unloaded, and this load's
 * flag goes with the load. A wait that another mod's hook refuses is not thrown here, it is never run: the flag then
 * stays up, with no further show and no following of the project, until a reload.
 * A show that no surface says it draws runs its seconds all the same: a window may draw it without having said so.
 * The answer then bears one sentence more.
 */
async function fireworks($: EngineInterface): Promise<string> {
  if (showEnding !== undefined) {
    return 'Fireworks are already going.'
  }

  showEnding = 'starting'
  showCount += 1

  // The theme stays: a show is a sibling backdrop that draws the theme's scene with the bursts over it.
  const suffix = SHOW_SUFFIXES[showCount % SHOW_SUFFIXES.length] ?? SHOW_SUFFIXES[0]
  // The one setter beside showThenKeep: a show's backdrop is no theme of the table, its answer is told, and nothing is kept, so nothing is to put back.
  let set: BackdropAnswer

  try {
    const now = await read($, choice)
    const theme = themeOf(now.preview ?? now.applied)

    set = await setBackdrop(
      $,
      theme === undefined
        ? { id: NIGHT_ID, glass: NIGHT_GLASS }
        : { id: `${theme.id}${suffix}`, glass: theme.glass, colorScheme: theme.window },
    )
  } catch (error) {
    // A show that did not begin costs a reply nothing, and the next word may try again.
    showEnding = undefined

    return `Fireworks could not be shown: ${reasonOf(error)}`
  }

  showEnding = $.clock.after(SHOW_MS, () => void quietly($, () => endFireworks($)))

  return set?.isDrawn === false ? `Fireworks. ${SHOW_UNSHOWN}` : 'Fireworks.'
}

/**
 * Whether a show may go off by itself on the word: yes, unless the person turned that off.
 * A store that cannot be read counts as off: on a doubt no picture comes unasked.
 */
async function goesOffByItself($: EngineInterface): Promise<boolean> {
  try {
    return (await $.store.get(AUTO_KEY)) !== 'off'
  } catch {
    return false
  }
}

/** `/fireworks` alone starts a show, whatever the key holds; `auto off` and `auto on` write the key. */
async function fireworksCommand($: EngineInterface, args: string): Promise<string> {
  const words = args.trim().toLowerCase().split(/\s+/).join(' ')

  if (words === '') {
    return fireworks($)
  }

  if (words !== 'auto off' && words !== 'auto on') {
    return 'Try /fireworks, /fireworks auto off or /fireworks auto on.'
  }

  try {
    await (words === 'auto off' ? $.store.set(AUTO_KEY, 'off') : $.store.delete(AUTO_KEY))
  } catch (error) {
    return `That could not be kept: ${reasonOf(error)}`
  }

  return words === 'auto off'
    ? 'Fireworks no longer go off by themselves. /fireworks still starts a show.'
    : 'Fireworks go off again when Claude says "merged".'
}

type CardElements = Pick<
  ReturnType<EngineInterface['ui']['resolve']>,
  'Box' | 'Text' | 'Button'
>

/** Puts the card away, placed or above the prompt, until the command shows it again. */
async function putCardAway($: EngineInterface): Promise<void> {
  await update($, choice, was => ({ ...was, cardInBand: false, cardAway: true }))
}

/**
 * A pick on the card: the theme (or none) applied, and the card put away, as a menu closes on a choice.
 * A pick that could not be kept is said, and the card stays for another. One that is kept and that no surface draws is said too.
 */
async function pick($: EngineInterface, theme: Theme | undefined, forProject: boolean): Promise<void> {
  const picked = await applyOrSay($, theme, forProject)

  if (picked.fault !== undefined) {
    void $.ui.toast(picked.fault)

    return
  }

  if (picked.isUnshown) {
    void $.ui.toast(unshownNote(forProject))
  }

  await putCardAway($)
}

/**
 * The card. Close and No theme stand at its head, so that it can be put away without scrolling past twenty rows.
 * The themes stand under the list's two heads, by the kind of window each is made for: a mod cannot learn which kind
 * the window is, and not every window follows its theme, so the card is where a person is steered. A theme made in
 * both kinds names its twin on a line of its own: its twin stands under the other head, and a row must not grow wider.
 * Each theme is its title, its blurb beneath, and its three buttons kept together. The desktop draws a button's
 * `label` and never its children, and a row there does not wrap; other surfaces draw the children. So both are one
 * short word that carries the state, and the theme's title on the row above says whose the three are: twenty
 * buttons share each word, and the keys alone tell them apart.
 * Applied is said only of the project's choice; a session's own choice is marked on This session.
 */
function card($: EngineInterface, { Box, Text, Button }: CardElements, now: ThemeChoice) {
  // Spacing flows from each parent's gap: more between two themes than anywhere inside one, so that a row of
  // buttons reads as its own theme's. A title and its buttons share a row, which wraps where the card is narrow.
  return (
    <Box flexDirection="column" borderStyle="round" paddingX={1} gap="md">
      <Box flexDirection="row" gap={1}>
        <Text bold>Theme examples</Text>
        <Button key="off" label="No theme" onPress={() => pick($, undefined, true)}>
          No theme
        </Button>
        {/* Where a surface carries it, the keyboard's ring starts here: Enter on Close changes nothing but the card. */}
        <Button
          key="close"
          label="Close"
          role="dismiss"
          autoFocus
          onPress={() => putCardAway($)}
        >
          Close
        </Button>
      </Box>
      {WINDOWS.map(window => (
        <Box key={`group-${window}`} flexDirection="column" gap="md">
          <Text key={`head-${window}`} size="heading" bold>{`For ${window} windows`}</Text>
          {THEMES.filter(theme => theme.window === window).map(theme => {
            const twin = themeOf(theme.twin)
            const applyWord = now.applied === theme.id && now.scope !== 'session' ? 'Applied' : 'Apply'
            const sessionWord = now.applied === theme.id && now.scope === 'session' ? '✓ This session' : 'This session'
            const previewWord = now.preview === theme.id ? 'Previewing' : 'Preview'

            return (
              <Box key={`theme-${theme.id}`} flexDirection="column" gap="xs">
                <Box flexDirection="row" flexWrap="wrap" justifyContent="space-between" columnGap="md" rowGap="xs">
                  <Text bold={now.applied === theme.id}>
                    {now.applied === theme.id ? '✓ ' : ''}
                    {theme.title}
                  </Text>
                  <Box flexDirection="row" gap={1}>
                    <Button key={`apply-${theme.id}`} label={applyWord} onPress={() => pick($, theme, true)}>
                      {applyWord}
                    </Button>
                    <Button
                      key={`session-${theme.id}`}
                      label={sessionWord}
                      onPress={() => pick($, theme, false)}
                    >
                      {sessionWord}
                    </Button>
                    <Button
                      key={`preview-${theme.id}`}
                      label={previewWord}
                      onPress={async () => {
                        let set: BackdropAnswer | undefined

                        try {
                          set = await showThenKeep($, theme.id, () => update($, choice, was => ({ ...was, preview: theme.id })))
                        } catch (error) {
                          // A look that did not begin leaves an earlier one its own end.
                          void $.ui.toast(`${theme.title} could not be shown: ${reasonOf(error)}`)

                          return
                        }

                        // This look's seconds start now: an earlier timer is stopped, or it would end this look early.
                        previewEnding?.cancel()
                        previewEnding = $.clock.after(PREVIEW_MS, () => void quietly($, () => endPreview($, theme.id)))

                        // A look stores nothing: the short form. Behind the timer's start: nothing stands between the state's write and its clock.
                        if (set?.isDrawn === false) {
                          void $.ui.toast(unshownNote(false))
                        }
                      }}
                    >
                      {previewWord}
                    </Button>
                  </Box>
                </Box>
                <Text dimColor>{theme.blurb}</Text>
                {twin === undefined ? [] : [<Text key={`twin-${theme.id}`} dimColor>{`For ${twin.window} windows: ${twin.title}`}</Text>]}
              </Box>
            )
          })}
        </Box>
      ))}
    </Box>
  )
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    // A refused name must not cost the session its backdrop: go on without the command.
    try {
      await $.command.register({
        name: COMMAND,
        description:
          'A backdrop behind the chat: alone it shows the card; with a theme\'s name it applies that theme to this project (add "session" for this session only); "list" names them, "off" clears.',
      })
    } catch (error) {
      void $.ui.toast(`theme-examples: /${COMMAND} is not available (${String(error)})`)
    }

    try {
      await $.command.register({
        name: FIREWORKS_COMMAND,
        description:
          'Fireworks behind the chat for a few seconds, over the theme if there is one (they also go off when Claude says "merged": /fireworks auto off stops that)',
      })
    } catch (error) {
      void $.ui.toast(`theme-examples: /${FIREWORKS_COMMAND} is not available (${String(error)})`)
    }

    // A preview left in the state has no clock in this load (the module's own variables start over): its end
    // never ran. Drop it, or this session would never follow its project again.
    if ((await read($, choice)).preview !== undefined) {
      await update($, choice, was => ({ ...was, preview: undefined }))
    }

    // A session's own choice outlives a reload and a new process; any other follows the project's.
    // Two steps, each quiet by itself: a choice that cannot be followed must not cost the window what the state holds.
    await quietly($, () => followChoice($))
    await quietly($, async () => {
      const shown = (await read($, choice)).applied

      if (themeOf(shown) !== undefined) {
        await showThenKeep($, shown)
      }
    })

    return next(e)
  })

  // A turn's start: an open session takes a change another session made to the project. It always passes on:
  // a fault of its own must never cost the person their prompt.
  on('prompt.submit', async ($, e, next) => {
    await quietly($, () => followChoice($))

    return next(e)
  })

  on('command.run', { command: COMMAND }, async ($, e) => {
    const words = e.args.trim().split(/\s+/).filter(word => word !== '')
    const last = words.at(-1)?.toLowerCase()
    // A scope word is the last of two or more words, and only these two: any other word is part of the name.
    const isScoped = words.length > 1 && (last === 'session' || last === 'project')
    const forProject = !(isScoped && last === 'session')
    const name = (isScoped ? words.slice(0, -1) : words).join(' ')
    const key = keyOf(name)

    if (name === '') {
      // A surface that draws no placed rows yet gets the card above the prompt.
      const placed = await $.ui.place({ id: CARD })

      await update($, choice, was => ({ ...was, cardInBand: !placed.isPlaced, cardAway: false }))

      return { text: 'Pick a theme on the card.' }
    }

    if (key === 'list') {
      return { text: themeList() }
    }

    if (key === 'off') {
      const cleared = await applyOrSay($, undefined, forProject)

      if (cleared.fault !== undefined) {
        return { text: cleared.fault }
      }

      return {
        text: forProject
          ? 'Theme cleared for this project. Other open sessions of it clear at their next turn.'
          : 'Theme cleared for this session only. The project keeps its theme for other sessions.',
      }
    }

    const theme = themeNamed(name)

    if (theme === undefined) {
      // One line: the reason stays in view. Nothing is applied and nothing is stored.
      const nearest = nearestTheme(name)

      return {
        text:
          `No theme named "${name}". ` +
          (nearest === undefined ? '' : `The nearest is ${nearest.id}. `) +
          `/${COMMAND} list names all ${THEMES.length}; "session" as the last word is this session only.`,
      }
    }

    const picked = await applyOrSay($, theme, forProject)

    if (picked.fault !== undefined) {
      return { text: picked.fault }
    }

    // A mod cannot learn which kind the window is, so every answer says which kind the theme is made for, and names its twin as the list does.
    const twin = themeOf(theme.twin)
    const said =
      (forProject
        ? `${theme.title} applied to this project. Other open sessions of it take it at their next turn.`
        : `${theme.title} applied to this session only.`) +
      ` Made for ${theme.window} windows${twin === undefined ? '' : ` (for ${twin.window} windows: ${twin.id})`}.`

    return { text: picked.isUnshown ? `${said} ${unshownNote(forProject)}` : said }
  })

  on('command.run', { command: FIREWORKS_COMMAND }, async ($, e) => ({ text: await fireworksCommand($, e.args) }))

  // Every block of the model's reply comes through here once, as text, before it is stored.
  on('session.append', { door: 'response' }, async ($, e, next) => {
    const said = e.message.content.some(
      block => block.type === 'text' && typeof block.text === 'string' && WORD.test(block.text),
    )

    if (said && (await goesOffByItself($))) {
      await fireworks($)
    }

    return next(e)
  })

  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    // Only a window has room behind the chat, and only its table has `Svg`.
    if (e.props.plugin !== PLUGIN || e.surface !== 'desktop') {
      return next(e)
    }

    const name = sceneNameOf(e.props)

    if (name === undefined) {
      return next(e)
    }

    const { Svg } = $.ui.resolve(e)

    if (name === NIGHT_ID) {
      return <Svg isInteractive alt="Fireworks bursting over a night sky" source={nightScene()} />
    }

    const showOf = themeOf(themeIdOfShow(name))

    if (showOf !== undefined) {
      return (
        <Svg
          isInteractive
          alt={`Fireworks over ${showOf.title}`}
          source={sceneWithFireworks(showOf, sceneOf(showOf))}
        />
      )
    }

    const theme = themeOf(name)

    if (theme === undefined) {
      return next(e)
    }

    return <Svg isInteractive alt={`${theme.title}: ${theme.blurb}`} source={sceneOf(theme)} />
  })

  on('ui.render', { component: 'Placed' }, async ($, e, next) => {
    if (e.props.plugin !== PLUGIN || e.props.id !== CARD) {
      return next(e)
    }

    const now = await read($, choice)

    // Put away: a placed row whose hook passes draws nothing.
    if (now.cardAway === true) {
      return next(e)
    }

    return card($, $.ui.resolve(e), now)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const now = await read($, choice)

    if (now.cardInBand !== true) {
      return next(e)
    }

    return card($, $.ui.resolve(e), now)
  })
}
