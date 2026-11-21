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
import { duckPondSvg } from './scenes/duck-pond/still'
import { fallingSandSvg } from './scenes/falling-sand/still'
import { fieldLinesSvg } from './scenes/field-lines/still'
import { gardenBeetlesSvg } from './scenes/garden-beetles/still'
import { koiPondSvg } from './scenes/koi-pond/still'
import { rippleTankSvg } from './scenes/ripple-tank/still'
import { seaSparkleSvg } from './scenes/sea-sparkle/still'
import { semicolonySvg } from './scenes/semicolony/still'
import { starChartSvg } from './scenes/star-chart/still'
import { FALLING_SAND_SOUND, KOI_POND_SOUND } from './sounds'
import type { Sound } from './sounds'

/** The scenes a shader plays over. Each name is a folder under ./scenes, which holds the shader and its still. */
export type ShaderScene =
  | 'duck-pond'
  | 'falling-sand'
  | 'field-lines'
  | 'garden-beetles'
  | 'koi-pond'
  | 'ripple-tank'
  | 'sea-sparkle'
  | 'semicolony'
  | 'star-chart'

/** One theme: what the card and the list say, the glass over it, and its scene: a function that builds one SVG. The SVG's
 *  own CSS animates it, or it is a still that a shader plays over (see ./interactive). A scene says whether it is dark or
 *  light with its tint, picked from it. */
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
  /** The shader that plays over the scene, where there is one: the scene is then its still, and follows the window. */
  shader?: ShaderScene
  /** Set where the picture is dark, or pale, whatever the window: a show's bursts are then bright, or deep, in both. */
  ground?: Theme['window']
  /** The theme's sound, where it has one (see ./sounds). */
  sound?: Sound
}

/** What a scene's two entries share: both of its rows below spread one of these, so they cannot differ. */
type Picture = Required<Pick<Theme, 'scene' | 'shader'>> & Pick<Theme, 'ground' | 'sound'>

const DUCK_POND: Picture = { scene: duckPondSvg, shader: 'duck-pond' }
const FALLING_SAND: Picture = { scene: fallingSandSvg, shader: 'falling-sand', sound: FALLING_SAND_SOUND }
const FIELD_LINES: Picture = { scene: fieldLinesSvg, shader: 'field-lines' }
const GARDEN_BEETLES: Picture = { scene: gardenBeetlesSvg, shader: 'garden-beetles' }
const KOI_POND: Picture = { scene: koiPondSvg, shader: 'koi-pond', ground: 'dark', sound: KOI_POND_SOUND }
const RIPPLE_TANK: Picture = { scene: rippleTankSvg, shader: 'ripple-tank' }
const SEA_SPARKLE: Picture = { scene: seaSparkleSvg, shader: 'sea-sparkle' }
const SEMICOLONY: Picture = { scene: semicolonySvg, shader: 'semicolony' }
const STAR_CHART: Picture = { scene: starChartSvg, shader: 'star-chart' }

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
  {
    id: 'duck-pond',
    title: 'Duck Pond',
    blurb: 'Rubber ducks on a pixel pond, and a press drops bugs for them to eat.',
    window: 'light',
    twin: 'duck-pond-night',
    glass: { blur: 16, tint: '#e8ecd9', opacity: 0.6 },
    ...DUCK_POND,
  },
  {
    id: 'duck-pond-night',
    title: 'Duck Pond, Night',
    blurb: 'Rubber ducks on a pixel pond, and a press drops bugs for them to eat.',
    window: 'dark',
    twin: 'duck-pond',
    glass: { blur: 16, tint: '#0f2433', opacity: 0.6 },
    ...DUCK_POND,
  },
  {
    id: 'falling-sand',
    title: 'Falling Sand',
    blurb: 'Pixel sand pours down stone shelves, and a press pours more.',
    window: 'light',
    twin: 'falling-sand-night',
    glass: { blur: 16, tint: '#f5ebd6', opacity: 0.6 },
    ...FALLING_SAND,
  },
  {
    id: 'falling-sand-night',
    title: 'Falling Sand, Night',
    blurb: 'Pixel sand pours down stone shelves, and a press pours more.',
    window: 'dark',
    twin: 'falling-sand',
    glass: { blur: 16, tint: '#1c1424', opacity: 0.6 },
    ...FALLING_SAND,
  },
  {
    id: 'field-lines',
    title: 'Field Lines',
    blurb: 'A magnetic field drawn in short dashes that turn toward your pointer.',
    window: 'light',
    twin: 'field-lines-night',
    glass: { blur: 16, tint: '#f3f1e7', opacity: 0.6 },
    ...FIELD_LINES,
  },
  {
    id: 'field-lines-night',
    title: 'Field Lines, Night',
    blurb: 'A magnetic field drawn in short dashes that turn toward your pointer.',
    window: 'dark',
    twin: 'field-lines',
    glass: { blur: 16, tint: '#22282b', opacity: 0.6 },
    ...FIELD_LINES,
  },
  {
    id: 'garden-beetles',
    title: 'Garden Beetles',
    blurb: 'Pixel beetles on a garden path that hide when your pointer comes near.',
    window: 'light',
    twin: 'garden-beetles-night',
    glass: { blur: 16, tint: '#ece5d3', opacity: 0.6 },
    ...GARDEN_BEETLES,
  },
  {
    id: 'garden-beetles-night',
    title: 'Garden Beetles, Night',
    blurb: 'Pixel beetles on a garden path that hide when your pointer comes near.',
    window: 'dark',
    twin: 'garden-beetles',
    glass: { blur: 16, tint: '#27393a', opacity: 0.6 },
    ...GARDEN_BEETLES,
  },
  {
    id: 'koi-pond',
    title: 'Koi Pond',
    blurb: 'A pond from above with ripples at your pointer and koi fed by a press.',
    window: 'light',
    twin: 'koi-pond-night',
    glass: { blur: 16, tint: '#d7e4e0', opacity: 0.6 },
    ...KOI_POND,
  },
  {
    id: 'koi-pond-night',
    title: 'Koi Pond, Night',
    blurb: 'A pond from above with ripples at your pointer and koi fed by a press.',
    window: 'dark',
    twin: 'koi-pond',
    glass: { blur: 16, tint: '#0e1824', opacity: 0.6 },
    ...KOI_POND,
  },
  {
    id: 'ripple-tank',
    title: 'Ripple Tank',
    blurb: 'Water striders on a printed pond, where your pointer sends out rings.',
    window: 'light',
    twin: 'ripple-tank-night',
    glass: { blur: 16, tint: '#d6e7e0', opacity: 0.6 },
    ...RIPPLE_TANK,
  },
  {
    id: 'ripple-tank-night',
    title: 'Ripple Tank, Night',
    blurb: 'Water striders on a printed pond, where your pointer sends out rings.',
    window: 'dark',
    twin: 'ripple-tank',
    glass: { blur: 16, tint: '#112e34', opacity: 0.6 },
    ...RIPPLE_TANK,
  },
  {
    id: 'sea-sparkle',
    title: 'Sea Sparkle',
    blurb: 'A night sea in three inks, where your pointer stirs plankton to glow.',
    window: 'light',
    twin: 'sea-sparkle-night',
    glass: { blur: 16, tint: '#ecf0ee', opacity: 0.6 },
    ...SEA_SPARKLE,
  },
  {
    id: 'sea-sparkle-night',
    title: 'Sea Sparkle, Night',
    blurb: 'A night sea in three inks, where your pointer stirs plankton to glow.',
    window: 'dark',
    twin: 'sea-sparkle',
    glass: { blur: 16, tint: '#090e1c', opacity: 0.6 },
    ...SEA_SPARKLE,
  },
  {
    id: 'semicolony',
    title: 'Semicolony',
    blurb: 'Code punctuation living as small creatures, magnified at your pointer.',
    window: 'light',
    twin: 'semicolony-night',
    glass: { blur: 16, tint: '#f1ece0', opacity: 0.6 },
    ...SEMICOLONY,
  },
  {
    id: 'semicolony-night',
    title: 'Semicolony, Night',
    blurb: 'Code punctuation living as small creatures, magnified at your pointer.',
    window: 'dark',
    twin: 'semicolony',
    glass: { blur: 16, tint: '#13161c', opacity: 0.6 },
    ...SEMICOLONY,
  },
  {
    id: 'star-chart',
    title: 'Star Chart',
    blurb: 'An engraved sky map that links nearby stars to your pointer.',
    window: 'light',
    twin: 'star-chart-night',
    glass: { blur: 16, tint: '#ece2ca', opacity: 0.6 },
    ...STAR_CHART,
  },
  {
    id: 'star-chart-night',
    title: 'Star Chart, Night',
    blurb: 'An engraved sky map that links nearby stars to your pointer.',
    window: 'dark',
    twin: 'star-chart',
    glass: { blur: 16, tint: '#101b30', opacity: 0.6 },
    ...STAR_CHART,
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
