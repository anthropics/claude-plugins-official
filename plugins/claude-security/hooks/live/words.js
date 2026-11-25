export const WITHHELD = 'Not shown: the report can still hold credential values'
const ROLES = {
 __proto__: null,
 'inventory': 'Inventory',
 'history': 'History',
 'context': 'Context',
 'research': 'Research',
 'boundary': 'Trust boundary',
 'sweep': 'Sweep',
 'past-fixes': 'Past fixes',
 'pack': 'Close reading',
 'half': 'Close reading',
 'gap': 'Close reading',
 'lead': 'Lead',
 'duplicates': 'Duplicates',
 'load': 'Load',
 'root-flaws': 'Root flaws',
 'redactor': 'Redaction',
}
const COUNTED = { 'sweep': 'pass ', 'past-fixes': 'area ', 'boundary': 'pass ' }
const UNPRINTED = /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\u2800\uFE00-\uFE0F]/gu
const PILED_MARKS = /(?<=\p{M}{2})\p{M}+/gu
const MARK = /[\p{Mn}\p{Me}\u1160-\u11FF\uD7B0-\uD7FF]/u
const WIDE =
 /[\u1100-\u115F\u2329\u232A\u2E80-\u303E\u3041-\uA4CF\uA960-\uA97F\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE6F\uFF01-\uFF60\uFFE0-\uFFE6\u{1F000}-\u{3FFFD}]|\p{Emoji_Presentation}/u
export function clean(value, cap = 200) {
 if (typeof value !== 'string') return ''
 const line = value
  .slice(0, 4 * cap)
  .trim()
  .split(/\s+/)
  .join(' ')
  .replace(PILED_MARKS, '')
 const shown = line.replace(UNPRINTED, ch => '\\u{' + ch.codePointAt(0)?.toString(16) + '}')
 return [...shown].slice(0, cap).join('')
}
const cellsOf = ch => (ch < '\u0300' ? 1 : MARK.test(ch) ? 0 : WIDE.test(ch) ? 2 : 1)
export const width = text => [...text].reduce((sum, ch) => sum + cellsOf(ch), 0)
export function fit(text, room, keepEnd = false) {
 if (width(text) <= room) return text
 if (room < 1) return ''
 const kept = []
 let used = 1
 for (const ch of keepEnd ? [...text].reverse() : text) {
  used += cellsOf(ch)
  if (used > room) break
  kept.push(ch)
 }
 return keepEnd ? '…' + kept.reverse().join('') : kept.join('') + '…'
}
export function halves(text, room) {
 const cut = width(text) > room ? fit(text, room + 2).lastIndexOf(' ') : -1
 return cut > 0 ? [text.slice(0, cut), text.slice(cut + 1)] : [text]
}
export function tail(path, room) {
 const cut = fit(path, room, true)
 const slash = cut.indexOf('/')
 return cut === path || slash < 0 ? cut : '…' + cut.slice(slash)
}
export const narrow = text => text.replace(/[^\x20-\x7E\xA1-\xAC\xAE-\u024F…]/gu, '?')
function lensWord(name) {
 const [first] = name.split('-')
 return first.charAt(0).toUpperCase() + first.slice(1)
}
export function agentWords(agent) {
 const lensed = (agent.role === 'research' || agent.role === 'panel') && !['', 'all'].includes(agent.lens)
 const what = lensed ? lensWord(agent.lens) : ROLES[agent.role]
 if (!what) return [agent.label, '']
 const rest = agent.label.slice(agent.role.length + 1)
 const where = /^\d+$/.test(rest) ? (COUNTED[agent.role] ?? '') + rest : rest.replace(/^([a-z-]+):(\d+)$/, '$1 $2')
 return [what, agent.component || where]
}
export function clock(seconds) {
 const minutes = Math.floor(seconds / 60)
 const two = (n) => String(n).padStart(2, '0')
 const head = minutes < 60 ? minutes : Math.floor(minutes / 60) + ':' + two(minutes % 60)
 return head + ':' + two(Math.floor(seconds % 60))
}
export function count(n) {
 if (n < 100_000) return String(n).replace(/\B(?=(\d{3})+$)/g, ',')
 if (n < 999_500) return Math.round(n / 1e3) + 'k'
 return n < 999.5e6 ? (n / 1e6).toPrecision(3) + 'M' : (n / 1e9).toPrecision(3) + 'B'
}
export const plural = (n, noun) => (n === 1 ? noun : noun + 's')
export const filesOf = ({ filesRead, files }) => count(filesRead) + (files ? '/' + count(files) : '')
