export const CLAY = '#d97757'
export const SEVERITY = { __proto__: null, CRITICAL: '#d6455d', HIGH: CLAY, MEDIUM: '#d9b36c', LOW: '#6a9bcc' }
export const LENS = { __proto__: null, reachability: '#6a9bcc', impact: '#9d95d6', defenses: '#62a08d' }
export const TONE = { running: CLAY, done: '#788c5d', failed: SEVERITY.MEDIUM }
export const VOTE = { pending: '○', confirm: '●', older: '◐', refute: '✕', abstain: '–', lost: '·' }
export const PHASE = { waiting: '○', running: '◉', done: '●', failed: '✕', skipped: '–' }
export const BARE = 0x01000000
const RAMP = '·✢✳✶✻✽✽✻✶✳✢·'
export const DARK = {
 paper: 0x222222,
 unread: [0x555555, 0x555555, 0x666666],
 part: [0x777777, 0x999999],
 read: [0xaaaaaa, 0xccbbaa, 0xeeddcc],
 dusk: [0x444444, 0x555555, 0x666666, 0x888888],
 peak: 0xffffee,
 shimmer: 0xee9977,
 clay: 0xdd7755,
 hairline: 0x555555,
 raised: 0x333333,
 name: 0xbbbbbb,
 faint: 0x888888,
 ripple: 0x6699cc,
 lead: 0xddbb66,
 strong: 0xffffee,
 chip: 0x111111,
}
export const LIGHT = {
 paper: 0xeeeeee,
 unread: [0xcccccc, 0xcccccc, 0xbbbbbb],
 part: [0xaaaaaa, 0x888888],
 read: [0x777777, 0x555555, 0x333333],
 dusk: [0xdddddd, 0xcccccc, 0xbbbbbb, 0x999999],
 peak: 0x992200,
 shimmer: 0xcc5533,
 clay: 0xdd7755,
 hairline: 0xcccccc,
 raised: 0xdddddd,
 name: 0x444444,
 faint: 0x999999,
 ripple: 0x3377bb,
 lead: 0xaa7711,
 strong: 0x111111,
 chip: 0x111111,
}
export const THEME_KEYS = ['subtle', 'inactive', 'text', 'claude', 'warning', 'inverseText']
export const PLAIN = {
 paper: BARE,
 unread: [0, 0, 0],
 part: [1, 1],
 read: [1, 2, 2],
 dusk: [0, 0, 1, 1],
 peak: 3,
 shimmer: 3,
 clay: 3,
 hairline: 0,
 raised: BARE,
 name: 1,
 faint: 1,
 ripple: 1,
 lead: 4,
 strong: 2,
 chip: 5,
}
export const spinner = seconds => RAMP[Math.floor(seconds / 0.14) % RAMP.length]
export const rgb = code => parseInt(code.slice(1), 16)
export const hex = ink => '#' + ink.toString(16).padStart(6, '0')
export function mix(start, end, share) {
 const channel = (shift) => {
  const [a, b] = [(start >> shift) & 255, (end >> shift) & 255]
  return Math.round(a + (b - a) * share) << shift
 }
 return channel(16) | channel(8) | channel(0)
}
