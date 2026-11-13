import type { Theme } from './themes'

/** The word that sets a show off, whole and in any case: "merged", not "unmerged" or "emerged". */
export const WORD = /\bmerged\b/i
/** A show's backdrop is its theme's id with one of these behind it; two, so a second show starts afresh. */
export const SHOW_SUFFIXES = ['--fireworks-a', '--fireworks-b'] as const
/** The backdrop of a show in a session with no theme: the bursts over a night sky of their own. */
export const NIGHT_ID = 'fireworks-night'
// No tint: no theme stands, so the panels keep the window's own color and the show asks no side of it.
export const NIGHT_GLASS = { blur: 10, opacity: 0.45 }

type Burst = { x: number; y: number; hue: number; delay: number; size: number }

// Bursts at the edges, and along the top edge over the conversation, so no spoke crosses the text being read.
// FOR PEOPLE SENSITIVE TO FLASHING LIGHT: each burst plays once, and their starts stand 1 s apart. Keep it so: a burst
// added, or a start moved nearer, makes the whole picture change more often.
const BURSTS: readonly Burst[] = [
  { x: 220, y: 230, hue: 48, delay: 0, size: 150 },
  { x: 1380, y: 200, hue: 330, delay: 1, size: 170 },
  { x: 800, y: 40, hue: 190, delay: 2, size: 120 },
  { x: 1470, y: 560, hue: 20, delay: 3, size: 140 },
  { x: 140, y: 620, hue: 280, delay: 4, size: 120 },
  { x: 1340, y: 380, hue: 300, delay: 5, size: 130 },
]

// Every name carries `fw`: the layer shares one document with a theme's own classes and keyframes.
// A burst RESTS open and its keyframes hide it ahead of its start and behind its end: where the app
// holds a scene still (no GPU, or animation off) the bursts then stand for the show, not vanish.
// Held still, only the bursts to the right of the words' column rest open (`fw-shut` rests the others closed):
// an open burst over the conversation or under the sidebar's labels would sit on text for as long as the
// scene is held. Running, the keyframes name every moment, so the class changes nothing.
// A person who asked their system for less motion asked for no picture either: there every burst rests closed.
const STYLE =
  '<style>' +
  '.fw-bloom{transform-box:view-box;transform:scale(1);opacity:.55;stroke-width:3;stroke-linecap:round;' +
  'animation:fw-bloom 1.7s cubic-bezier(.15,.7,.3,1) both}' +
  '.fw-bloom.fw-shut{opacity:0}' +
  '@keyframes fw-bloom{0%{transform:scale(0);opacity:0}12%{opacity:1}65%{transform:scale(1);opacity:1}' +
  '100%{transform:scale(1.12);opacity:0}}' +
  '@media (prefers-reduced-motion: reduce){.fw-bloom{animation:none;opacity:0}}' +
  '</style>'

// In picture units (1600 wide) the words' column ends at about 1150 WITH THE RIGHT PANEL OPEN at 1200, 1680 and 1920
// wide, and at 1209 at 1440 wide: the three bursts that rest open begin at 1210, 1210 and 1330, so they clear it there
// by one unit, and a new burst is placed against 1210, not against this constant. With the panel shut the column runs
// further right (to about 1300, 1390 and 1470 to 1500 at 1680, 1440 and 1200 wide) and these three reach into it: no
// place clears the words in every state, and the veil under the column is what carries them there.
const WORDS_END_X = 1150

/** Whether a burst, held still, rests open: its whole reach to the right of the words' column with the right panel open. */
export function restsOpen(spot: { x: number; size: number }): boolean {
  return spot.x - spot.size > WORDS_END_X
}

/** One burst: eighteen spokes opening from a bright core. */
function burst(spot: Burst, lightness: number): string {
  const spokes: string[] = []

  for (let index = 0; index < 18; index += 1) {
    const angle = (index / 18) * Math.PI * 2
    const inner = spot.size * 0.18
    const outer = spot.size * (index % 2 === 0 ? 1 : 0.72)
    const fromX = (spot.x + Math.cos(angle) * inner).toFixed(1)
    const fromY = (spot.y + Math.sin(angle) * inner).toFixed(1)
    const toX = (spot.x + Math.cos(angle) * outer).toFixed(1)
    const toY = (spot.y + Math.sin(angle) * outer).toFixed(1)

    spokes.push(`<line x1="${fromX}" y1="${fromY}" x2="${toX}" y2="${toY}"/>`)
  }

  return (
    `<g class="${restsOpen(spot) ? 'fw-bloom' : 'fw-bloom fw-shut'}" style="transform-origin:${spot.x}px ${spot.y}px;` +
    `animation-delay:${spot.delay.toFixed(2)}s" stroke="hsl(${spot.hue} 95% ${lightness}%)">` +
    `<circle cx="${spot.x}" cy="${spot.y}" r="${(spot.size * 0.12).toFixed(1)}" ` +
    `fill="hsl(${spot.hue} 100% ${lightness + 17}%)" stroke="none"/>${spokes.join('')}</g>`
  )
}

/** The bursts alone, to lay over a scene: bright over a dark scene, deep over a pale one, so both read. */
function layer(window: Theme['window']): string {
  const lightness = window === 'dark' ? 68 : 40

  return STYLE + BURSTS.map(spot => burst(spot, lightness)).join('')
}

const built = new Map<string, string>()

/** A theme's own scene with the bursts drawn over it: one document still, the theme never taken away. */
export function sceneWithFireworks(theme: Theme, scene: string): string {
  const cached = built.get(theme.id)

  if (cached !== undefined) {
    return cached
  }

  const end = scene.lastIndexOf('</svg>')
  const whole = end === -1 ? scene : scene.slice(0, end) + layer(theme.window) + '</svg>'

  built.set(theme.id, whole)

  return whole
}

/** The show of a session with no theme: the bursts over a night sky of their own. */
export function nightScene(): string {
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="100%" height="100%" ' +
    'preserveAspectRatio="xMidYMid slice" font-family="system-ui,sans-serif" color="#e8ecff">' +
    '<defs><linearGradient id="fw-sky" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0" stop-color="#070b1c"/><stop offset="1" stop-color="#1a1436"/></linearGradient></defs>' +
    '<rect width="1600" height="1000" fill="url(#fw-sky)"/>' +
    layer('dark') +
    '</svg>'
  )
}

/** The theme id a show's backdrop id stands for, or nothing where the id is no show's. */
export function themeIdOfShow(id: string): string | undefined {
  const suffix = SHOW_SUFFIXES.find(candidate => id.endsWith(candidate))

  return suffix === undefined ? undefined : id.slice(0, id.length - suffix.length)
}
