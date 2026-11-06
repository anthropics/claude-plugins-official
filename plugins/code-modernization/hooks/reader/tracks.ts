/**
 * The three ways the plugin's commands work on a system, and what each leaves behind. The pane follows
 * whichever one the artifacts on disk say is under way, so a same-stack version uplift or a greenfield
 * rebuild is followed as closely as a rewrite is.
 */

export type TrackKey = 'transform' | 'uplift' | 'reimagine'

export const TRACK_LABELS: Record<TrackKey, string> = {
  transform: 'rewrite',
  uplift: 'uplift',
  reimagine: 'reimagine',
}

/** The unit of work in each track, as the pane names a list of them. */
export const TRACK_UNITS: Record<TrackKey, { one: string; many: string }> = {
  transform: { one: 'module', many: 'Modules' },
  uplift: { one: 'module', many: 'Modules' },
  reimagine: { one: 'service', many: 'Services' },
}

/** What each state of a unit of work is called, by track: the same colors, worded for what the work is. */
export const STATE_WORDS_BY_TRACK: Record<TrackKey, Record<string, string>> = {
  transform: {
    untouched: 'untouched',
    scaffolded: 'scaffolded',
    'tests-written': 'tests written',
    'tests-red': 'tests red',
    'tests-failing': 'tests failing',
    'tests-green': 'tests green',
    reviewed: 'reviewed',
    ported: 'ported',
    switched: 'switched',
  },
  uplift: {
    untouched: 'not migrated',
    scaffolded: 'changed',
    'tests-written': 'tests written',
    'tests-red': 'worse than baseline',
    'tests-failing': 'tests failing',
    'tests-green': 'tests pass',
    reviewed: 'matches baseline',
    ported: 'ported',
    switched: 'switched',
  },
  reimagine: {
    untouched: 'legacy',
    scaffolded: 'scaffolded',
    'tests-written': 'tests written',
    'tests-red': 'tests red',
    'tests-failing': 'tests failing',
    'tests-green': 'tests green',
    reviewed: 'reviewed',
    ported: 'ported',
    switched: 'switched',
  },
}

/** Times (ms) of the artifacts that mark each track as under way; null where the artifact is absent. */
export type TrackFacts = {
  transformAt: number | null
  upliftAt: number | null
  reimagineAt: number | null
}

/**
 * The track under way: the one whose own artifacts were written last. The discovery artifacts (preflight,
 * assess, map, rules, brief) feed all three and decide nothing. With no track's own artifacts a system
 * is at the start of the rewrite path, which is where the plugin's commands begin.
 */
export function pickTrack(option: TrackKey | 'auto', facts: TrackFacts): TrackKey {
  if (option !== 'auto') {
    return option
  }

  const ranked = (
    [
      ['transform', facts.transformAt],
      ['reimagine', facts.reimagineAt],
      ['uplift', facts.upliftAt],
    ] as const
  ).filter((entry): entry is readonly [TrackKey, number] => entry[1] !== null)

  if (ranked.length === 0) {
    return 'transform'
  }

  return ranked.reduce((best, entry) => (entry[1] > best[1] ? entry : best))[0]
}
