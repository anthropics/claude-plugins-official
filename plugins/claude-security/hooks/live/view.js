import { BARE, LENS, PHASE, SEVERITY, THEME_KEYS, TONE, VOTE, hex, mix, rgb, spinner } from './palette.js'
import { LENSES, SEVERITIES, STAGES } from './scan.js'
import { WITHHELD, agentWords, clean, clock, count, filesOf, fit, halves, plural, tail, width } from './words.js'
const SIDE_BY_SIDE = 84
const SIDE = 46
const APP_FINDINGS = 30
const AGENT_ROWS = 4
const MARGIN = 2
const ID = 4
const [TALL, TILED] = [36, 64]
const [KEYS, KEYS_BESIDE] = [29, 64]
const SWAY = 2
const [TEXT, SOFT, FAINT, CLAY] = ['text', 'inactive', 'subtle', 'claude']
const ENDED = { done: 'Scan complete', failed: 'Scan not complete', skipped: 'Nothing to scan' }
const BRIEF = { CRITICAL: 'crit', HIGH: 'high', MEDIUM: 'med', LOW: 'low' }
const STATUS = {
 running: ['Scanning', CLAY, TONE.running],
 done: ['Complete', 'success', TONE.done],
 failed: ['Not complete', 'warning', TONE.failed],
 skipped: ['Skipped', SOFT],
}
const TOLD = {
 Setup: 'Sizing up the code',
 Inventory: 'Dividing the code into components',
 Sweep: 'Covering what the components leave out',
 Research: 'Hunting each class of flaw through each component',
 Panel: 'Trying to prove each candidate wrong',
 Report: 'Writing up what survived',
}
const lineWidth = line => line.reduce((sum, [text]) => sum + width(text), 0)
const spread = (left, right) => ({ columns: [[left], [right, lineWidth(right), 'flex-end']] })
function dotted(parts, cols) {
 const out = []
 for (const part of parts.filter(each => each.length)) {
  const next = out.length ? [[' · ', FAINT], ...part] : part
  if (lineWidth(out) + lineWidth(next) > cols) break
  out.push(...next)
 }
 return out
}
function text({ ui }, rows) {
 const span = ([words, color, style]) =>
  h(ui.Text, { color, ...style }, words.replace(/^(?=\p{M})/u, ' '))
 const line = (spans) =>
  h(ui.Text, { wrap: 'truncate' }, ...(spans.length ? spans : [[' ']]).map(span))
 const column = ([spans, minWidth, end]) =>
  h(
   ui.Box,
   minWidth === undefined ? { flexGrow: 1, flexShrink: 1 } : { minWidth, flexShrink: 0, justifyContent: end },
   line(spans),
  )
 return rows.map(row =>
  Array.isArray(row) ? line(row) : h(ui.Box, { flexDirection: 'row' }, ...row.columns.map(column)),
 )
}
const glyph = ({ scan, motion, terminal, now }, offset = 0) =>
 scan.running && motion && terminal ? spinner(now + offset) : '✻'
const holds = ({ terminal }, cells) => (terminal ? cells : Math.floor(cells * 1.15))
const figure = (n, noun, color = TEXT, shown = count(n)) => [
 [shown, n ? color : SOFT, { bold: Boolean(n) }],
 [' ' + (shown === '1' ? noun.replace(/s$/, '') : noun), SOFT],
]
function chip({ inks }, words, color, tone) {
 if (!inks || !tone) return [words, color, { bold: true }]
 const backgroundColor = hex(mix(inks.paper, rgb(tone), 0.2))
 return [' ' + words + ' ', hex(mix(rgb(tone), inks.strong, 0.3)), { bold: true, backgroundColor }]
}
const gapAfter = (spare, parts, n) =>
 n + 1 < parts ? Math.round((spare * (n + 1)) / (parts - 1)) - Math.round((spare * n) / (parts - 1)) : 0
const rounded = n => (n < 10_000 || n >= 100_000 ? count(n) : Math.round(n / 1000) + 'k')
const filesRead = t => figure(t.filesRead, 'files', TEXT, filesOf(t))
const linesRead = t => figure(t.linesRead, 'lines', TEXT, rounded(t.linesRead))
const tally = (scan, brief) =>
 SEVERITIES.flatMap(each => {
  const n = scan.findings.filter(found => found.severity === each).length
  return n ? [[[n + ' ' + (brief ? BRIEF[each] : each.toLowerCase()), SEVERITY[each]]]] : []
 })
function heading(view, cols) {
 const { scan } = view
 const { target } = scan
 const revision = [target.branch, target.commit].filter(Boolean).join(' ')
 const facts = [target.name, target.mode, target.effort, revision, target.scope.join(' ')].filter(Boolean)
 const title = [
  [glyph(view) + ' ', CLAY],
  ['Claude Security plugin', TEXT, { bold: true }],
 ]
 const time = [clock(scan.now()), TEXT, { bold: true }]
 const marked = [chip(view, ...STATUS[scan.result.state]), ['  '], time]
 const { failed } = scan.totals()
 const lost = failed ? [[' ' + count(failed) + plural(failed, ' agent') + ' failed', 'warning']] : []
 const room = cols - lineWidth(lost) - 1
 const known = facts.map((fact, n) => [[fit(fact, room), n ? SOFT : TEXT]])
 return [
  spread(title, lineWidth(title) + lineWidth(marked) < cols ? marked : [time]),
  spread(dotted(known, room), lost),
 ]
}
function rail(view, cols) {
 const { scan } = view
 const colors = { waiting: SOFT, running: CLAY, done: TEXT, failed: 'error', skipped: SOFT }
 const build = (name) =>
  STAGES.map(stage => {
   const state = scan.phases.get(stage)?.state ?? 'waiting'
   const words = PHASE[state] + (name(stage) && ' ' + name(stage))
   const leads = state === 'running' && stage === scan.stage
   return leads ? chip(view, words, CLAY, TONE.running) : [words, colors[state]]
  })
 const links = STAGES.length - 1
 const whole = build(stage => stage)
 const fits = (form, gap) => lineWidth(form) + gap * links <= cols
 const stops = fits(whole, 2) ? whole : build(stage => (stage === scan.stage ? stage : ''))
 const spare = Math.max(cols - lineWidth(stops), links)
 const gap = (n) => gapAfter(spare, stops.length, n)
 const link = (cells) =>
  cells && fits(stops, 3) ? ' ' + '─'.repeat(cells - 2) + ' ' : ' '.repeat(cells)
 const times = stops.map(([words], n) => {
  const [spent, name, room] = [scan.spent(STAGES[n]), words.search(/\w/), width(words) + gap(n)]
  const time = spent === undefined || name < 0 ? '' : clock(spent)
  return [time.padStart(Math.min(name + time.length, room)).padEnd(room), SOFT]
 })
 return [stops.flatMap((stop, n) => [stop, [link(gap(n)), FAINT]]), times]
}
function underWay({ stage, working }) {
 if (stage === 'Setup' || stage === 'Report') return TOLD[stage]
 const agent = working.find(each => each.stage === stage) ?? working.at(-1)
 return agent ? TOLD[agent.stage] : 'Waiting for the next step'
}
const told = ({ scan }) => [[scan.running ? underWay(scan) : ENDED[scan.result.state], SOFT, { italic: true }]]
const steady = ({ held }, rows, most) => Math.min(Math.abs(rows - held) <= SWAY ? held : rows, most)
function funnel(scan, cols) {
 const t = scan.totals()
 const arrow = [' › ', FAINT]
 const verdicts = [...figure(t.confirmed, 'confirmed', CLAY), [' · ', FAINT], ...figure(t.refuted, 'refuted')]
 const long = [...figure(t.leads, 'leads'), arrow, ...figure(t.candidates, 'candidates'), arrow, ...verdicts]
 const effort = [figure(t.agents, 'agents'), figure(t.tools, 'calls')]
 const read = [filesRead(t), linesRead(t)]
 if (cols >= 56) return [dotted([...read, ...effort], cols), long]
 return [dotted(read, cols), dotted(effort, cols), long.slice(0, 5), verdicts]
}
function tiles(scan, cols) {
 const t = scan.totals()
 const each = [
  filesRead(t),
  linesRead(t),
  figure(t.leads, 'leads'),
  figure(t.candidates, 'candidates'),
  figure(t.confirmed, 'confirmed', CLAY),
  figure(t.refuted, 'refuted'),
 ]
 let [even, start] = [0, 0]
 const widths = each.map(([[n]], at) => {
  even += gapAfter(cols - width('refuted'), each.length, at)
  const cell = Math.max(even - start, width(n) + 1)
  start += cell
  return cell
 })
 return [
  each.map(([[n, ...style]], at) => [n.padEnd(widths[at]), ...style]),
  each.map(([, [noun, ...style]], at) => [noun.trim().padEnd(widths[at]), ...style]),
 ]
}
function caption({ terminal }, title, note, cols) {
 const words = [[title, TEXT, { bold: true }], ...(note.length ? [['  '], ...note] : [])]
 return [...words, [terminal ? ' ' + '─'.repeat(Math.max(cols - lineWidth(words) - 1, 0)) : '', FAINT]]
}
function within(lines, rows) {
 if (lines.length <= rows) return lines
 const kept = lines.slice(0, Math.max(rows - 1, 0))
 return [...kept, [['and ' + (lines.length - kept.length) + ' more', SOFT]]]
}
function agents(view, cols, rows) {
 const { working, agents: all, running } = view.scan
 const longest = all.reduce((most, agent) => Math.max(most, width(agentWords(agent).filter(Boolean).join(' · '))), 0)
 const room = Math.min(Math.floor(cols * 0.64), longest + 1)
 const row = (agent, mark, doing) => {
  const [what, where] = agentWords(agent)
  const name = fit(what, room)
  const busy = agent.state === 'running'
  const who = [
   [name, busy ? TEXT : SOFT],
   [fit(where && ' · ' + where, holds(view, room) - width(name)), SOFT],
  ]
  return { columns: [[[mark], 2], [who, room + 1], [doing]] }
 }
 const lines = working.map(agent => {
  const [, verb = '', path = ''] = /^(?:Read |(Search |Run ))(.*)/.exec(agent.activity) ?? []
  const doing = [[verb + tail(path, holds(view, cols - room - 3) - width(verb)), SOFT]]
  return row(agent, [glyph(view, agent.id * 0.31), CLAY], doing)
 })
 const waits = [
  [glyph(view) + ' ', CLAY],
  [underWay(view.scan), SOFT],
 ]
 const busy = running ? within(lines.length ? lines : [waits], rows - 1) : []
 const gold = view.inks ? hex(view.inks.lead) : SEVERITY.MEDIUM
 const ended = all.filter(agent => agent.state !== 'running').sort((a, b) => b.endedRev - a.endedRev)
 const done = ended.slice(0, Math.max(rows - busy.length - 1, 0)).map(agent => {
  const leads = agent.leads ? [[agent.leads + plural(agent.leads, ' lead'), gold]] : []
  const mark = agent.state === 'done' ? ['✓', SOFT] : ['✕', 'warning']
  const calls = [[agent.tools + plural(agent.tools, ' call'), SOFT]]
  return row(agent, mark, dotted([calls, leads], cols - room - 3))
 })
 const finished = ended.filter(agent => agent.state === 'done').length
 const sums = [
  working.length ? [[working.length + ' at work', CLAY]] : [],
  finished ? [[finished + ' done', SOFT]] : [],
 ]
 if (!running && !done.length) return []
 return [caption(view, 'Agents', dotted(sums, cols - width('Agents') - 3), cols), ...busy, ...done]
}
function panel(view, cols, rows) {
 const { scan } = view
 const rank = { testing: 0, confirmed: 1, unsettled: 2, refuted: 3 }
 const voting = new Set(scan.working.map(agent => agent.component + ':' + agent.lens))
 const lines = [...scan.candidates.values()]
  .sort((a, b) => rank[a.outcome] - rank[b.outcome])
  .map(({ id, path, line, votes, outcome }) => {
   const gone = outcome === 'refuted'
   const word = outcome === 'testing' ? '' : outcome
   const cast = LENSES.map((lens, n) => {
    const turn = n * 0.4 + line * 0.13
    if (votes[lens] === 'pending')
     return [[voting.has(id + ':' + lens) ? [glyph(view, turn), LENS[lens]] : [VOTE.pending, SOFT]], 2]
    return [[[VOTE[votes[lens]], gone ? SOFT : LENS[lens]]], 2]
   })
   return {
    columns: [
     [[[id, gone ? SOFT : outcome === 'confirmed' ? CLAY : TEXT, { bold: !gone }]], ID],
     ...cast,
     [[[' ' + tail(clean(path, 400) + ':' + line, holds(view, cols - 12 - width(word))), SOFT]]],
     [[[word, outcome === 'confirmed' ? CLAY : SOFT]], width(word), 'flex-end'],
    ],
   }
  })
 const legend = LENSES.flatMap(lens => [
  ['● ', LENS[lens]],
  [lens + '  ', SOFT],
 ])
 return [caption(view, 'Panel', [['two or three votes each', SOFT]], cols), legend, ...within(lines, rows - 2)]
}
function findings(view, cols, rows) {
 const { scan, terminal } = view
 const { state, message, reportDir, verification } = scan.result
 const done = state === 'done'
 const why = done ? [] : [[[fit(message, cols), state === 'failed' ? 'warning' : SOFT]]]
 if (!reportDir) return [caption(view, ENDED[state], [], cols), ...why]
 const room = terminal ? rows - why.length - (rows < 8 ? 2 : 3) : 2 * APP_FINDINGS
 const tall = room >= 2 * scan.findings.length
 const slim = cols < 56
 const widest = Math.max(0, ...scan.findings.map(({ severity }) => severity.length))
 const titleAt = ID + widest + 3
 const across = holds(view, cols - (slim ? 0 : titleAt))
 const long = scan.findings.filter(({ title }) => width(title) > across).length
 const wraps = room >= 2 * scan.findings.length + long
 const lines = scan.findings.flatMap(({ id, title, severity, file, line }) => {
  const color = SEVERITY[severity] ?? SOFT
  const head = [
   [[[id, color, { bold: true }]], ID],
   [[chip(view, severity.padEnd(widest), color, SEVERITY[severity])], titleAt - ID],
  ]
  const place = [tail(clean(file, 400) + ':' + line, holds(view, cols - titleAt)), SOFT]
  if (!title || (title === WITHHELD && !tall)) return [{ columns: [...head, [[place]]] }]
  const [start, ...rest] = (wraps ? halves(title, across) : [title]).map(words => [words, TEXT])
  if (tall && slim) return [{ columns: [...head, [[place]]] }, ...[start, ...rest].map(span => [span])]
  const under = [...rest, place].map(span => ({ columns: [[[], titleAt], [[span]]] }))
  return [{ columns: [...head, [[start]]] }, ...(tall ? under : [])]
 })
 const status = verification ? [[verification, done && verification === 'verified' ? 'success' : 'warning']] : []
 const end = [...(rows < 8 ? [] : [[]]), dotted([status, [[reportDir + '/', SOFT]]], holds(view, cols))]
 const name = done ? 'Findings' : ENDED[state]
 const total = done || scan.findings.length ? [[String(scan.findings.length), TEXT]] : []
 const title = caption(view, name, dotted([total, ...tally(scan, slim)], cols - width(name) - 3), cols)
 const none = done ? [[['No finding survived the panel', SOFT]]] : []
 return [title, ...why, ...within(lines.length ? lines : none, room), ...end]
}
function detail(view, cols, rows) {
 const { scan } = view
 const pick = !scan.running ? findings : scan.candidates.size && scan.stage !== 'Report' ? panel : agents
 const listed = rows < 2 ? [] : pick(view, cols, rows)
 const left = pick === agents ? 0 : rows - listed.length
 const all = left < AGENT_ROWS ? listed : [...listed, [], ...agents(view, cols, left - 1)]
 return view.terminal ? Array.from({ length: Math.max(rows, 0) }, (_, n) => all[n] ?? []) : all
}
export function pane(view) {
 if (!view.terminal || !view.docked) return body(view)
 const paddingTop = view.rows < 12 ? 0 : 1
 const inner = body({ ...view, cols: Math.max(view.cols - 2 * MARGIN, 1), rows: view.rows - paddingTop })
 return h(view.ui.Box, { flexDirection: 'column', paddingX: MARGIN, paddingTop }, inner)
}
function body(view) {
 const { scan, ui, cols, rows } = view
 const column = (...children) => h(ui.Box, { flexDirection: 'column' }, ...children)
 if (!view.terminal) {
  const high = Math.max(Math.floor(rows * 0.45), 10)
  const list = column(...text(view, detail(view, cols, Math.max(rows - high - 12, 8))))
  return h(
   ui.Box,
   { flexDirection: 'column', rowGap: 1 },
   column(...text(view, [...heading(view, cols), told(view)])),
   view.map(cols, high),
   list,
  )
 }
 if (rows < 8) return band(view)
 const keys = h(ui.Box, { flexDirection: 'row', columnGap: 2 }, ...view.buttons)
 const wide = cols >= SIDE_BY_SIDE && rows < 30
 const map = wide && view.map(cols - SIDE - 2, steady(view, rows - 2, rows - 2))
 if (map) {
  const needed = (scan.running ? 0 : scan.findings.length) + (scan.result.state === 'done' ? 0 : 1)
  const counts = needed > rows - 12 ? [] : [...funnel(scan, SIDE), []]
  const top = [...heading(view, SIDE), [], ...counts]
  const side = [...top, ...detail(view, SIDE, rows - 1 - top.length)]
  return h(
   ui.Box,
   { flexDirection: 'row', columnGap: 2 },
   column(...text(view, [rail(view, cols - SIDE - 2)[0]]), map, keys),
   h(ui.Box, { flexDirection: 'column', width: SIDE }, ...text(view, side)),
  )
 }
 const roomy = rows >= 22 ? [[]] : []
 const [stages, times] = rail(view, cols)
 const top = [...heading(view, cols), ...roomy, stages, ...(rows >= TALL ? [times] : []), ...roomy]
 const figures = cols >= TILED ? tiles(scan, cols) : funnel(scan, cols)
 const free = rows - top.length - figures.length - 3 * roomy.length - 1
 const most = free - AGENT_ROWS
 const tall = steady(view, Math.min(Math.ceil(free * 0.6), Math.ceil(cols * 0.42), most), most)
 const stacked = tall >= 5 && cols >= 12 && view.map(cols, tall)
 const listed = detail(view, cols, stacked ? free - tall : free + roomy.length)
 const below = [...(stacked ? roomy : []), ...figures, ...roomy, ...listed, ...roomy]
 const said = text(view, cols >= KEYS_BESIDE ? [told(view)] : [])
 const foot = h(ui.Box, { flexDirection: 'row', justifyContent: 'space-between' }, keys, ...said)
 return h(ui.Box, { flexDirection: 'column', width: cols }, ...text(view, top), stacked, ...text(view, below), foot)
}
function summary(scan, cols) {
 const t = scan.totals()
 const { state, message } = scan.result
 if (!scan.running) {
  if (state === 'done' || t.findings) return [figure(t.findings, 'findings'), dotted(tally(scan, true), Infinity)]
  return [[[fit(message, cols), state === 'failed' ? 'warning' : SOFT]]]
 }
 if (t.candidates) {
  return [figure(t.candidates, 'candidates'), figure(t.confirmed, 'confirmed', CLAY), figure(t.refuted, 'refuted')]
 }
 return [figure(t.running, 'at work'), filesRead(t), t.leads ? figure(t.leads, 'leads') : []]
}
export function band(view) {
 const { scan, ui, cols } = view
 const stage = scan.running ? scan.stage : ENDED[scan.result.state]
 const head = [
  [glyph(view) + ' ', CLAY],
  [stage, TEXT, { bold: true }],
 ]
 const beside = cols >= KEYS_BESIDE
 const room = cols - (beside ? KEYS : 0)
 const parts = [head, ...summary(scan, room - lineWidth(head) - 3), [[clock(scan.now()), SOFT]]]
 const words = text(view, [dotted(parts, room)])
 const keys = h(ui.Box, { flexDirection: 'row', columnGap: 2, flexShrink: 0 }, ...view.buttons)
 if (!beside) return h(ui.Box, { flexDirection: 'column' }, ...words, keys)
 const first = h(ui.Box, { flexDirection: 'row', justifyContent: 'space-between' }, ...words, keys)
 return h(ui.Box, { flexDirection: 'column' }, first, view.terminal && view.rows > 1 && view.map(cols, 1))
}
export function plainMap(ui, cells, cols) {
 const named = (ink) => (ink === BARE ? undefined : (THEME_KEYS[ink] ?? hex(ink)))
 const rows = []
 for (let start = 0; start < cells.length; start += 3 * cols) {
  const runs = []
  for (let at = start; at < start + 3 * cols; at += 3) {
   const [ch, ink, paper] = [String.fromCharCode(cells[at]), cells[at + 1], cells[at + 2]]
   const run = runs.at(-1)
   if (run && run[2] === paper && (run[1] === ink || ch === ' ')) run[0] += ch
   else runs.push([ch, ink, paper])
  }
  const spans = runs.map(([words, ink, paper]) =>
   h(ui.Text, { color: named(ink), backgroundColor: named(paper) }, words),
  )
  rows.push(h(ui.Text, { wrap: 'truncate' }, ...spans))
 }
 return h(ui.Box, { flexDirection: 'column' }, ...rows)
}
