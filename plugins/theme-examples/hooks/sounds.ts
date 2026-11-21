// Sound for Koi Pond and Falling Sand. A theme's sound is numbers, never a recording: the desktop app makes it from
// these layers of tones and noise once the person turns theme sound on. ./themes gives each to its scene once, for
// both of the scene's entries, so going from one entry to the other keeps the ambience playing.
import type { ThemeSetArgs } from 'claude-code'

/**
 * The `sound` of a theme: `ThemeSound`, where this Claude Code's types have it. Read off `ThemeSetArgs`, and not
 * imported by name, so that the mod still type-checks against the types of a Claude Code from before sound: there it
 * is any object, and nothing checks the numbers below.
 */
export type Sound = ThemeSetArgs extends { sound?: infer Known } ? NonNullable<Known> : object

// A press sounds one note of each list, by where it lands from the window's left edge to its right: the upper note
// glides up and the lower, an octave under it, glides down. All are notes of one pentatonic scale, as the drips are.
const POND_PLIPS = ['E5', 'F#5', 'A5', 'B5', 'D6']
const POND_BODIES = ['E4', 'F#4', 'A4', 'B4', 'D5']

/** Koi Pond: tonal, with reverb. Still water, a drip now and then, and a plop where a press drops food. */
export const KOI_POND_SOUND: Sound = {
  ambience: {
    reverb: 0.3,
    layers: [
      // The water: a low wash whose filter opens and closes once in 16 seconds, with two slow swells on the way.
      { wave: 'pink', drone: true, gain: 0.6, filter: { type: 'bandpass', hz: 380, to: 620 }, tremolo: { hz: 0.125, depth: 0.35 } },
      // A thin, high hiss that rises and falls a little, three times in the same 16 seconds.
      { wave: 'pink', drone: true, gain: 0.135, filter: { type: 'bandpass', hz: 2400, to: 3400 }, tremolo: { hz: 0.1875, depth: 0.4 } },
      // A drip every eight seconds or so. Its note rises, as a drop's does.
      { wave: 'sine', notes: ['A5', 'B5', 'D6', 'E6', 'F#6', 'A6'], scatter: 0.12, glide: 5, attack: 0.003, release: 0.11, gain: 0.26 },
      // Rarer and lower: a koi turning at the surface.
      { wave: 'sine', notes: ['D4', 'E4', 'A4'], scatter: 0.04, glide: -4, attack: 0.012, release: 0.3, gain: 0.19, filter: { type: 'lowpass', hz: 900 } },
    ],
  },
  cues: {
    // A press drops a pellet: a plop, pitched by where it lands.
    click: {
      reverb: 0.22,
      layers: [
        { wave: 'sine', notes: POND_PLIPS, glide: 9, attack: 0.003, release: 0.1, gain: 0.4 },
        { wave: 'sine', notes: POND_BODIES, glide: -5, attack: 0.004, release: 0.16, gain: 0.26 },
        { wave: 'pink', attack: 0.002, release: 0.035, gain: 0.18, filter: { type: 'highpass', hz: 2600 } },
      ],
    },
    // A message goes out: two quick drops, the second higher.
    send: {
      reverb: 0.2,
      layers: [{ wave: 'sine', notes: ['E5', 'A5'], step: 0.08, glide: 4, attack: 0.003, release: 0.1, gain: 0.38 }],
    },
    // The turn is over: one slow, low ring, with a drop on top.
    done: {
      reverb: 0.45,
      layers: [
        { wave: 'sine', notes: ['D4', 'A4'], attack: 0.06, release: 1.3, gain: 0.18, filter: { type: 'lowpass', hz: 1200 } },
        { wave: 'sine', notes: ['F#5'], glide: 3, attack: 0.004, release: 0.22, gain: 0.14 },
      ],
    },
    // Claude waits on the person: a koi turns, and two drops follow, the second higher. The drops are short and
    // slide a long way up, to keep them from ringing like a chime.
    ask: {
      reverb: 0.15,
      layers: [
        { wave: 'sine', notes: ['D4'], glide: -4, attack: 0.008, release: 0.22, gain: 0.3, filter: { type: 'lowpass', hz: 900 } },
        { wave: 'sine', notes: [0, 'F#5', 'B5'], step: 0.13, glide: 9, attack: 0.003, release: 0.08, gain: 0.4 },
        { wave: 'pink', attack: 0.002, release: 0.04, gain: 0.12, filter: { type: 'highpass', hz: 2600 } },
      ],
    },
    // The turn ended in an error: a low note that sinks, like a stone going down.
    error: {
      reverb: 0.25,
      layers: [
        { wave: 'sine', notes: ['A3'], glide: -7, attack: 0.006, release: 0.4, gain: 0.34 },
        { wave: 'sine', notes: ['A4'], glide: -7, attack: 0.006, release: 0.22, gain: 0.1 },
        { wave: 'brown', attack: 0.004, release: 0.22, gain: 0.2, filter: { type: 'lowpass', hz: 480 } },
      ],
    },
  },
}

// A press pours sand at the pointer. The first grain ticks on the stone, lower at the left and higher at the right.
const SAND_TICKS = [1400, 1650, 1900, 2200, 2500, 2850]

/** Falling Sand: mostly noise, with no reverb. A faint pour, a slide of sand now and then, and a short pour at a press. */
export const FALLING_SAND_SOUND: Sound = {
  ambience: {
    layers: [
      // The nozzles' steady pour: a wide hiss in two layers. The lower one drifts a little up and back once in 16
      // seconds, with two slow swells.
      { wave: 'white', drone: true, gain: 0.18, filter: { type: 'bandpass', hz: 2400, to: 2700 }, tremolo: { hz: 0.125, depth: 0.25 } },
      { wave: 'white', drone: true, gain: 0.14, filter: { type: 'bandpass', hz: 4200 } },
      // Grains ticking in the pour.
      { wave: 'crackle', drone: true, gain: 0.03, filter: { type: 'highpass', hz: 2800 } },
      // A heap gives way: a short slide of sand every ten seconds or so, lower than the pour, to stand clear of it.
      { wave: 'pink', scatter: 0.1, attack: 0.06, release: 0.55, gain: 0.5, filter: { type: 'bandpass', hz: 1500, to: 600 } },
      // Now and then a grain lands on stone: a short tick, like the one a press starts with.
      { wave: 'triangle', notes: [1400, 1900, 2500], scatter: 0.25, glide: -9, attack: 0.002, release: 0.03, gain: 0.2 },
    ],
  },
  cues: {
    // A press pours: a hiss that falls as it thins, grains in it, and the tick of the first grain on stone.
    click: {
      layers: [
        { wave: 'white', attack: 0.015, release: 0.32, gain: 1, filter: { type: 'bandpass', hz: 5200, to: 2300 } },
        { wave: 'crackle', attack: 0.004, release: 0.3, gain: 0.2, filter: { type: 'bandpass', hz: 4000, to: 2000 } },
        { wave: 'triangle', notes: SAND_TICKS, glide: -9, attack: 0.002, release: 0.03, gain: 0.15 },
      ],
    },
    // A message goes out: a pinch of sand thrown up.
    send: {
      layers: [
        { wave: 'white', attack: 0.004, release: 0.16, gain: 1, filter: { type: 'bandpass', hz: 2600, to: 6200 } },
        { wave: 'white', attack: 0.004, release: 0.12, gain: 0.75, filter: { type: 'highpass', hz: 3000 } },
      ],
    },
    // A tool call: one grain. It comes often, so it is about as loud as the ambience's own ticks.
    tool: {
      layers: [{ wave: 'crackle', attack: 0.002, release: 0.025, gain: 0.12, filter: { type: 'highpass', hz: 4200 } }],
    },
    // The turn is over: the last of a pour settles, and two pebbles come to rest.
    done: {
      layers: [
        { wave: 'white', attack: 0.02, release: 0.6, gain: 0.75, filter: { type: 'bandpass', hz: 4200, to: 1100 } },
        { wave: 'crackle', attack: 0.02, release: 0.8, gain: 0.25, filter: { type: 'bandpass', hz: 4200, to: 1100 } },
        { wave: 'triangle', notes: [1760, 1320], step: 0.1, glide: -5, attack: 0.002, release: 0.05, gain: 0.2 },
      ],
    },
    // Claude waits on the person: a pebble knocks on stone, twice and then once more. Each knock is two notes that
    // make no chord and drop fast, to keep it from ringing like a chime.
    ask: {
      layers: [
        { wave: 'triangle', notes: [950, 950, 0, 1130], step: 0.09, glide: -14, attack: 0.002, release: 0.05, gain: 0.55 },
        { wave: 'triangle', notes: [1340, 1340, 0, 1600], step: 0.09, glide: -14, attack: 0.002, release: 0.035, gain: 0.35 },
        { wave: 'white', attack: 0.003, release: 0.05, gain: 0.1, filter: { type: 'highpass', hz: 5000 } },
      ],
    },
    // The turn ended in an error: a shelf of sand slumps.
    error: {
      layers: [
        { wave: 'pink', attack: 0.008, release: 0.45, gain: 1, filter: { type: 'bandpass', hz: 700, to: 240 } },
        { wave: 'pink', attack: 0.008, release: 0.4, gain: 1, filter: { type: 'bandpass', hz: 1100, to: 450 } },
        { wave: 'white', attack: 0.008, release: 0.35, gain: 1, filter: { type: 'bandpass', hz: 1800, to: 800 } },
        { wave: 'crackle', attack: 0.01, release: 0.3, gain: 0.3, filter: { type: 'bandpass', hz: 1800 } },
      ],
    },
  },
}
