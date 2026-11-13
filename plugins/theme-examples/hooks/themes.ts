import type { ThemeBackdropGlass } from 'claude-code'

import { auroraSvg, deepWaterSvg, emberSvg } from './scenes/classic'
import { blueprintSvg } from './scenes/blueprint'
import { brailleStarsSvg } from './scenes/braille-stars'
import { departureBoardSvg } from './scenes/departure-board'
import { ditherDunesSvg, ditherDunesNightSvg } from './scenes/dither-dunes'
import { halftoneDawnSvg, halftoneDuskSvg } from './scenes/halftone-dawn'
import { honuLagoonSvg } from './scenes/honu-lagoon'
import { koiMosaicSvg } from './scenes/koi-mosaic'
import { nightReefSvg } from './scenes/night-reef'
import { paperGardenSvg, paperGardenKraftSvg } from './scenes/paper-garden'
import { plotterTideSvg, plotterTideNightSvg } from './scenes/plotter-tide'
import { snowPinesSvg } from './scenes/snow-pines'
import { teletextCloudsSvg } from './scenes/teletext-clouds'
import { vectorRangeSvg } from './scenes/vector-range'

/** One theme: what the card and the list say, the glass over it, and its scene: a function that builds one SVG whose
 *  own CSS animates it. A scene says whether it is dark or light with its tint, picked from it. */
export type Theme = {
  id: string
  title: string
  blurb: string
  /** Which window the scene is made for: the app uses a theme's tint only where its own text reads on it. */
  window: 'light' | 'dark'
  /** The same scene made for the other kind of window, by its id, where there is one: the list and the card name it. */
  twin?: string
  glass: ThemeBackdropGlass
  scene: () => string
}

export const THEMES: readonly Theme[] = [
  {
    id: 'honu-lagoon',
    title: 'Honu Lagoon',
    blurb: 'A live ASCII lagoon from above: a tile turtle swims by a sand island',
    window: 'light',
    glass: { blur: 7, tint: '#e6fbff', opacity: 0.42 },
    scene: honuLagoonSvg,
  },
  {
    id: 'koi-mosaic',
    title: 'Koi Mosaic',
    blurb: 'A tiled koi pond from above: two koi, lily pads, slow ripples.',
    window: 'light',
    glass: { blur: 12, tint: '#eef8f1', opacity: 0.36 },
    scene: koiMosaicSvg,
  },
  {
    id: 'halftone-dawn',
    title: 'Halftone Dawn',
    blurb: 'A two-ink riso sunrise: halftone dots that breathe outward.',
    window: 'light',
    twin: 'halftone-dusk',
    glass: { blur: 14, tint: '#f6ead9', opacity: 0.55 },
    scene: halftoneDawnSvg,
  },
  {
    id: 'halftone-dusk',
    title: 'Halftone Dusk',
    blurb: 'The riso sunrise on night-blue stock: an ember sun in breathing dots.',
    window: 'dark',
    twin: 'halftone-dawn',
    glass: { blur: 14, tint: '#1f2336', opacity: 0.5 },
    scene: halftoneDuskSvg,
  },
  {
    id: 'plotter-tide',
    title: 'Plotter Tide',
    blurb: 'Pen-plotter tide lines drawing themselves on warm paper.',
    window: 'light',
    twin: 'plotter-tide-night',
    glass: { blur: 0, tint: '#f4efe4', opacity: 0.32 },
    scene: plotterTideSvg,
  },
  {
    id: 'plotter-tide-night',
    title: 'Plotter Tide, Night',
    blurb: 'The plotter\'s tide chart in pale ink on blue-black night paper.',
    window: 'dark',
    twin: 'plotter-tide',
    glass: { blur: 0, tint: '#141a27', opacity: 0.32 },
    scene: plotterTideNightSvg,
  },
  {
    id: 'dither-dunes',
    title: 'Dither Dunes',
    blurb: 'One-bit dunes on sand paper, shaded in dots, under a terracotta sun',
    window: 'light',
    twin: 'dither-dunes-night',
    glass: { blur: 18, tint: '#f1e8d6', opacity: 0.34 },
    scene: ditherDunesSvg,
  },
  {
    id: 'dither-dunes-night',
    title: 'Dither Dunes Night',
    blurb: 'The same dunes after dark: pale dots on umber, an ember sun',
    window: 'dark',
    twin: 'dither-dunes',
    glass: { blur: 18, tint: '#1c1712', opacity: 0.4 },
    scene: ditherDunesNightSvg,
  },
  {
    id: 'paper-garden',
    title: 'Paper Garden',
    blurb: 'Cut-paper leaves at the edges of a warm white sheet, one coral bloom.',
    window: 'light',
    twin: 'paper-garden-kraft',
    glass: { blur: 16, tint: '#fbf6ec', opacity: 0.5 },
    scene: paperGardenSvg,
  },
  {
    id: 'paper-garden-kraft',
    title: 'Paper Garden, Kraft',
    blurb: 'Cut-paper leaves at the edges of dark kraft paper, one coral bloom.',
    window: 'dark',
    twin: 'paper-garden',
    glass: { blur: 16, tint: '#35312a', opacity: 0.5 },
    scene: paperGardenKraftSvg,
  },
  {
    id: 'night-reef',
    title: 'Night Reef',
    blurb: 'The lagoon after dark: a turtle and a ray that glow as they swim',
    window: 'dark',
    glass: { blur: 14, tint: '#0a1430', opacity: 0.4 },
    scene: nightReefSvg,
  },
  {
    id: 'snow-pines',
    title: 'Snow Pines',
    blurb: 'An ASCII pine forest at dusk, snow drifting down through the trees.',
    window: 'dark',
    glass: { blur: 16, tint: '#14143a', opacity: 0.5 },
    scene: snowPinesSvg,
  },
  {
    id: 'braille-stars',
    title: 'Braille Stars',
    blurb: 'A slow night sky drawn dot by dot on a braille grid.',
    window: 'dark',
    glass: { blur: 20, tint: '#0a1430', opacity: 0.3 },
    scene: brailleStarsSvg,
  },
  {
    id: 'teletext-clouds',
    title: 'Block Clouds',
    blurb: 'Night clouds built from blocks on a teletext grid, drifting in',
    window: 'dark',
    glass: { blur: 12, tint: '#0d173f', opacity: 0.34 },
    scene: teletextCloudsSvg,
  },
  {
    id: 'vector-range',
    title: 'Vector Range',
    blurb: 'Phosphor mountains on black; an amber beam keeps retracing them.',
    window: 'dark',
    glass: { blur: 22, tint: '#0e2f27', opacity: 0.42 },
    scene: vectorRangeSvg,
  },
  {
    id: 'departure-board',
    title: 'Departure Board',
    blurb: 'An amber LED board re-lettering itself, row by row.',
    window: 'dark',
    glass: { blur: 14, tint: '#1a120b', opacity: 0.34 },
    scene: departureBoardSvg,
  },
  {
    id: 'blueprint',
    title: 'Blueprint',
    blurb: 'A cyanotype sheet; a comet goes round its plotted orbit in the corner.',
    window: 'dark',
    glass: { blur: 14, tint: '#0c2444', opacity: 0.42 },
    scene: blueprintSvg,
  },
  {
    id: 'deep-water',
    title: 'Deep Water',
    blurb: 'Light falling through deep water, and one quiet turtle',
    window: 'dark',
    glass: { blur: 14, tint: '#062c3a', opacity: 0.34 },
    scene: deepWaterSvg,
  },
  {
    id: 'aurora',
    title: 'Aurora',
    blurb: 'Northern lights swaying over a dark ridge',
    window: 'dark',
    glass: { blur: 18, tint: '#14123a', opacity: 0.3 },
    scene: auroraSvg,
  },
  {
    id: 'ember',
    title: 'Ember',
    blurb: 'A warm glow in the corners and a few embers rising',
    window: 'dark',
    glass: { blur: 12, tint: '#2a0d12', opacity: 0.3 },
    scene: emberSvg,
  },
]

const built = new Map<string, string>()

/** A theme's SVG, built the first time it is asked for: a session pays only for the scenes it shows. */
export function sceneOf(theme: Theme): string {
  const ready = built.get(theme.id)
  if (ready !== undefined) return ready
  const source = theme.scene()
  built.set(theme.id, source)
  return source
}

/** Why a theme's scene cannot be drawn, in the fault's own words; nothing where it builds. */
export function sceneFault(theme: Theme): string | undefined {
  try {
    sceneOf(theme)

    return undefined
  } catch (error) {
    return error instanceof Error ? error.message : String(error)
  }
}
