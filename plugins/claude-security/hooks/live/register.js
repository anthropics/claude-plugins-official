import { Atlas } from './atlas.js'
import { packed } from './canvas.js'
import { Chart } from './chart.js'
import { Listener, inside, parsed } from './listener.js'
import { CodeMap } from './map.js'
import { DARK, LIGHT, PLAIN } from './palette.js'
import { moment } from './scan.js'
import { band, pane, plainMap } from './view.js'
const PANE = 'claude-security'
const COMMAND = 'claude-security-view'
const REDACTOR = 'claude-security:scan-redactor'
const TOOLS = ['Read', 'Grep', 'Glob', 'Bash', 'StructuredOutput', 'SubagentHandback']
const RUN_DIR = /\/CLAUDE-SECURITY-[0-9][0-9-]*\/\.claude-security-run$/
const FIRST_VERSION = [2, 1, 292]
const FAST_MS = 50
const SLOW_MS = 250
const FAST_TEXT_S = 0.2
const SLOW_TEXT_S = 0.5
const CHECK_S = 2
const AFTERGLOW_S = 6
const FOLDERS = 2000
const FILE_BYTES = 256 * 1024
const TREE_BYTES = 24 * 1024 * 1024
const FILES_PER_S = 120
const GUESSED_BYTES = 4000
const CELL_WIDTH = 8
const CELL_HEIGHT = 20
const RESIZE_S = 0.1
let live
let lead = { id: undefined, idle: false, launched: 0 }
const runs = new Map()
const strangers = new Set()
let wanted = 'pane'
let mayShow = false
let placed = false
let seenIdle = false
let kept
let following = false
let ending = false
let atlas
let untraced = []
let budget = TREE_BYTES
const maps = new Map()
const charts = new Map()
let look = { inks: DARK, motion: true, plain: false, mono: false, solid: false }
let timer
let pace = SLOW_MS
let ticking = false
let checking = false
let realRoot = ''
const last = { drawn: 0, rev: 0, checked: 0, running: 0, mapRows: 0 }
const aside = work =>
 void Promise.resolve()
  .then(work)
  .catch(() => {})
async function begin($, listener, agentId) {
 if (listener !== live) {
  rest()
  for (const [id, older] of runs) if (older !== listener) runs.delete(id)
  live = listener
  atlas = undefined
  untraced = []
  budget = TREE_BYTES
  wanted = 'pane'
  kept = undefined
  placed = false
  seenIdle = false
 }
 lead = { id: agentId, idle: false, launched: Date.now() }
 ending = false
 listener.scan.reopen()
 listener.scan.resume()
 const { version } = await $.session.version()
 const behind =
  version
   .split(/\D/)
   .map((part, n) => Number(part) - FIRST_VERSION[n])
   .find(Boolean) ?? 0
 if (behind < 0) live = undefined
 else await wake($)
}
async function wake($) {
 const surfaces = await $.session.surfaces()
 rest()
 if (kept && live?.scan.running) {
  wanted = kept
  kept = undefined
 }
 following = wanted !== 'off' && surfaces.length > 0
 mayShow ||= surfaces.includes('terminal')
 if (!live || !following) return
 const listener = live
 if (!atlas) {
  atlas = new Atlas([])
  const description = 'Show or hide the live view of the security scan'
  aside(async () => {
   await $.command.register({ name: COMMAND, description, immediate: true })
   if (!mayShow && surfaces.includes('vscode')) $.ui.log('Type /' + COMMAND + ' to watch the scan on a live map.')
  })
  await learnLook($).catch(() => {})
  aside(() => survey($, listener))
  if (!following || listener !== live) return
 }
 last.running = moment()
 pace = surfaces.includes('terminal') && look.motion && !look.plain ? FAST_MS : SLOW_MS
 timer ??= $.clock.every(pace, () => aside(() => tick($)))
 if (wanted === 'pane' && !placed && mayShow) await open($)
 $.ui.invalidate('ui.render')
 if (ending) await conclude($, listener)
}
async function open($) {
 const seat = { backgroundColor: 'transparent', rows: 18, columns: 72 }
 placed = (await $.ui.open({ id: PANE, title: 'Security scan', closeOnEscape: true, ...seat })).isPlaced
}
function rest() {
 timer?.cancel()
 timer = undefined
 maps.clear()
}
async function learnLook($) {
 const [settings, rows, noColor, depth, term, program, windows, ground] = await Promise.all([
  $.settings.read(),
  $.config.list(),
  $.env.get('NO_COLOR'),
  $.env.get('COLORTERM'),
  $.env.get('TERM'),
  $.env.get('TERM_PROGRAM'),
  $.env.get('WT_SESSION'),
  $.env.get('COLORFGBG'),
 ])
 const theme = String(rows.find(row => row.key === 'theme')?.value)
 const known = /^(dark|light)/.test(theme)
 const rich = /truecolor|24bit|direct|kitty|ghostty|alacritty|iTerm|vscode|WezTerm/.test([depth, term, program].join())
 look = {
  inks: (known ? theme.startsWith('light') : /;(7|15)$/.test(ground ?? '')) ? LIGHT : DARK,
  motion: settings.prefersReducedMotion !== true,
  plain: Boolean(noColor) || !(rich || windows) || theme.endsWith('ansi'),
  mono: Boolean(noColor) || term === 'dumb',
  solid: !known && !ground,
 }
}
async function survey($, listener) {
 aside(async () => listener.described(await $.fs.read(listener.runDir + '/scan-meta.json')))
 const listed = parsed(await $.fs.read(listener.runDir + '/target-files.json').catch(() => ''))
 const named = Array.isArray(listed) ? listed : listener.scan.components.flatMap(component => component.paths)
 const paths = named.filter(path => typeof path === 'string' && inside(path))
 const folders = [...new Set(paths.map(path => path.slice(0, path.lastIndexOf('/') + 1)))].slice(0, FOLDERS)
 const sizes = new Map()
 realRoot = (await $.fs.stat(listener.root, { resolve: true })).realPath ?? ''
 for (let at = 0; at < folders.length; at += 16) {
  const some = folders.slice(at, at + 16)
  const lists = await Promise.all(some.map(folder => entriesOf($, listener.root + '/' + folder).catch(() => [])))
  lists.forEach((entries, n) => {
   for (const { name, kind, size } of entries) if (kind === 'file') sizes.set(some[n] + name, size)
  })
 }
 if (listener !== live) return
 const found = new Atlas(paths.map(path => [path, sizes.get(path) ?? GUESSED_BYTES]))
 found.grows = !Array.isArray(listed)
 const known = new Set(paths)
 listener.linesOf = path => found.linesOf(path)
 listener.knows = path => known.has(path) || found.plots.some(plot => (plot.path + '/').startsWith(path + '/'))
 listener.listed = !found.grows
 if (listener.listed) listener.scan.list(known)
 const small = found.plots.filter(plot => sizes.get(plot.path) <= FILE_BYTES)
 untraced = found.folded ? [] : small.filter(spend)
 atlas = found
 $.ui.invalidate('ui.render')
}
async function entriesOf($, folder) {
 return held(await $.fs.stat(folder, { resolve: true })) ? $.fs.list(folder) : []
}
const held = ({ realPath = '' }) =>
 Boolean(realRoot) && realPath.startsWith(realRoot) && /^([/\\]|$)/.test(realPath.slice(realRoot.length))
function spend(plot) {
 budget -= plot.bytes
 return budget > 0
}
async function tick($) {
 if (!live || ticking) return
 ticking = true
 try {
  const { scan, root } = live
  const now = moment()
  for (const plot of untraced.splice(0, (FILES_PER_S * pace) / 1000)) {
   aside(async () => atlas?.trace(plot, await $.fs.read(root + '/' + plot.path)))
  }
  if (scan.running) last.running = now
  if (scan.running && !checking && now - last.checked >= CHECK_S) {
   last.checked = now
   checking = true
   aside(() => check($).finally(() => (checking = false)))
  }
  const due = now - last.drawn >= (pace === FAST_MS ? FAST_TEXT_S : SLOW_TEXT_S)
  if (mayShow && due && (scan.running || scan.rev !== last.rev)) {
   Object.assign(last, { drawn: now, rev: scan.rev })
   $.ui.invalidate('ui.render')
  }
  for (const [requestId, mounted] of maps) {
   const cells = !look.plain && mounted.shown && packed(mounted.map.draw(now))
   if (!cells || cells === mounted.sent) continue
   mounted.sent = cells
   mounted.shown = !(await $.ui.blit({ requestId, key: 'map', cells })).deny
  }
  if (now - last.running > AFTERGLOW_S) rest()
 } finally {
  ticking = false
 }
}
async function check($) {
 if (!live) return
 const { scan, root, runDir } = live
 const map = atlas
 for (const path of scan.visits.keys()) {
  if (!map?.grows) break
  if (map.find(path) !== undefined) continue
  const found = await $.fs.stat(root + '/' + path, { resolve: true }).catch(() => undefined)
  const plot = map.add(path, found?.size ?? GUESSED_BYTES)
  const small = found?.kind === 'file' && held(found) && found.size <= FILE_BYTES
  if (small && map === atlas && spend(plot)) untraced.push(plot)
 }
 if (scan.working.length || scan.stage === 'Report') return
 if ((await $.fs.stat(runDir + '/votes.json')).mtimeMs > lead.launched) scan.enter('Report')
}
async function conclude($, listener) {
 if (listener.scan.reported || listener.scan.working.length) return
 ending = !following
 if (ending) {
  listener.scan.quietSince ??= Date.now()
  return
 }
 const names = (await $.fs.list(listener.reportDir).catch(() => [])).map(entry => entry.name)
 const stamp = names.find(name => /^CLAUDE-SECURITY-REVISION-.*\.json$/.test(name))
 if (!stamp && !listener.scan.running) return
 const read = (name) => $.fs.read(listener.reportDir + '/' + name)
 const jsonl = stamp && (await read('CLAUDE-SECURITY-RESULTS.jsonl').catch(() => undefined))
 const text = await (stamp ? read(stamp) : $.fs.read(listener.runDir + '/coverage.json')).catch(() => '')
 if (listener.scan.working.length) return
 if (stamp) listener.reported(jsonl, text)
 else if (listener.scan.running) listener.stopped(text)
 $.ui.invalidate('ui.render')
}
async function show($, choice) {
 wanted = choice === 'band' && !live?.scan.running ? 'off' : choice
 placed = false
 kept = undefined
 seenIdle = false
 mayShow ||= choice === 'pane'
 await (choice === 'pane' ? open($) : $.ui.close({ id: PANE }))
 await wake($)
 $.ui.invalidate('ui.render')
}
function viewOf($, e, scan, rows, keys) {
 const ui = $.ui.resolve(e)
 const terminal = e.surface === 'terminal'
 const picture = (cols, high) => {
  const width = Math.min(Math.max(cols * CELL_WIDTH, 300), 720)
  const height = Math.min(high * CELL_HEIGHT, 520)
  const motion = look.motion && e.surface !== 'mobile'
  let chart = charts.get(e.surface)
  if (!chart?.fits(scan, atlas, width, height, motion)) {
   chart = new Chart(scan, atlas, width, height, motion)
   charts.set(e.surface, chart)
  }
  return h(ui.Svg, { source: chart.source(moment()), alt: 'Map of the scanned code. Stage: ' + scan.stage })
 }
 const cells = (cols, high) => {
  if (!atlas?.plots.length || e.props.isCollapsed) return undefined
  let mounted = maps.get(e.requestId)
  if (!mounted?.map.fits(scan, atlas, cols, high)) {
   if (mounted && scan.running && moment() - mounted.built < RESIZE_S) {
    const { map, sent } = mounted
    if (look.plain) return plainMap(ui, map.draw(moment()), map.cols)
    return h(ui.Raster, { key: 'map', columns: map.cols, rows: map.rows, cells: sent })
   }
   const drawn = look.plain ? { inks: PLAIN, motion: false, solid: false, mono: look.mono } : look
   mounted = { map: new CodeMap(scan, atlas, cols, high, drawn), sent: '', shown: true, built: moment() }
   maps.set(e.requestId, mounted)
  }
  if (high > 1) last.mapRows = high
  if (look.plain) return plainMap(ui, mounted.map.draw(moment()), cols)
  mounted.shown = true
  mounted.sent = packed(mounted.map.draw(moment()))
  return h(ui.Raster, { key: 'map', columns: cols, rows: high, cells: mounted.sent })
 }
 const buttons = keys.map(([chord, label, action, choice]) => {
  const shown = terminal
   ? { label: chord + ' ' + label.toLowerCase(), action, plain: true, dimColor: true }
   : { label }
  return h(ui.Button, { key: choice, onPress: () => show($, choice).catch(() => {}), ...shown })
 })
 const cols = Math.min(e.props.bodyColumns, 220)
 const motion = pace === FAST_MS
 const docked = e.props.placement === 'dock'
 const inks = terminal && !look.plain && !look.solid ? look.inks : undefined
 const map = terminal ? cells : picture
 return { scan, ui, cols, rows, now: moment(), motion, terminal, docked, inks, map, held: last.mapRows, buttons }
}
async function rewake($, e, next) {
 const answered = await next(e)
 if (live && wanted !== 'off' && (mayShow || !live.scan.reported)) aside(() => wake($))
 return answered
}
export const register = (on, options) => {
 if (options.live_view === false) return
 on('tool.call', { tool: 'Workflow', name: 'claude-security:scan' }, async ($, e, next) => {
  const given = new Listener(parsed(e.args), strangers)
  if (!RUN_DIR.test(given.runDir)) return next(e)
  const listener = given.runDir === live?.runDir ? live : given
  runs.set(e.tool_use_id, listener)
  const started = await next(e)
  aside(() => {
   if (started.deny !== undefined || started.isError) return runs.delete(e.tool_use_id)
   runs.set(parsed(started.result).runId, listener)
   return begin($, listener, e.agentId)
  })
  return started
 })
 on('agent.spawn', async ($, e, next) => {
  const run = e.workflow && (runs.get(e.tool_use_id) ?? runs.get(e.workflow.runId))
  const listener = run ?? live
  const started = await next(e)
  aside(() => {
   const { agentId } = started
   if (!agentId) return
   if (!listener) return strangers.add(agentId)
   if (listener.helps(agentId, e.parentAgentId)) return
   const stopped = !listener.scan.running
   if (run) listener.spawned(agentId, e.description, e.prompt)
   else if (e.subagentType === REDACTOR && listener.owns(e.prompt)) listener.spawned(agentId, 'redactor', '')
   else strangers.add(agentId)
   if (stopped && listener.scan.running) return wake($)
  })
  return started
 })
 on('tool.call', { tool: TOOLS, agentId: /./ }, async ($, e, next) => {
  if (!live || live.scan.reported) return next(e)
  const listener = live
  const answered = await next(e)
  aside(() => {
   if (answered.deny !== undefined || answered.isError || e.agentId === lead.id) return
   const stopped = !listener.scan.running
   listener.called(String(e.agentId), e.tool, e, answered.result)
   if (stopped && listener.scan.running) return wake($)
  })
  return answered
 })
 on('turn.complete', ($, e, next) => {
  if (!live) return next(e)
  const listener = live
  aside(() => {
   if (e.agentId === lead.id) lead.idle = true
   else if (!listener.ended(e.agentId, e.reason, e.answer)) return
   if (e.agentId === lead.id || listener.redacted || (lead.idle && e.isAborted)) return conclude($, listener)
  })
  return next(e)
 })
 on('command.run', { command: COMMAND }, async $ => {
  if (live) await show($, placed ? 'off' : 'pane')
  return {}
 })
 on('ui.close', { id: PANE }, async ($, e, next) => {
  const closed = await next(e)
  if (wanted === 'pane') aside(() => show($, 'band'))
  return closed
 })
 on('session.attach', rewake)
 on('session.detach', rewake)
 on('ui.render', { component: 'Pane', requestId: PANE }, ($, e, next) => {
  if (!live) return next(e)
  placed = wanted === 'pane'
  const view = viewOf($, e, live.scan, e.props.scroll.bodyRows, [['ctrl+x x', 'Close', 'pane:close', 'band']])
  return e.props.placement === 'widget' ? band({ ...view, buttons: [] }) : pane(view)
 })
 on('ui.render', { component: 'AbovePrompt' }, ($, e, next) => {
  if (!live || !mayShow || wanted === 'off' || placed || e.props.hasSurvey) return next(e)
  if (!live.scan.running && seenIdle && e.props.isWorking) {
   const choice = wanted
   aside(() => show($, 'off').then(() => (kept = choice)))
   return next(e)
  }
  seenIdle = !live.scan.running && !e.props.isWorking
  const view = viewOf($, e, live.scan, e.props.maxRows, [
   ['ctrl+x ↑', 'Map', 'pane:grow', 'pane'],
   ['ctrl+x x', 'Hide', 'pane:close', 'off'],
  ])
  return band(view)
 })
}
