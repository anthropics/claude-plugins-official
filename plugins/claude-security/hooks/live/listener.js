import { BYTES_PER_LINE, LAST_SLASHES } from './atlas.js'
import { LENSES, Scan } from './scan.js'
import { WITHHELD, clean, plural } from './words.js'
const STAGE_OF = {
 __proto__: null,
 'inventory': 'Inventory',
 'history': 'Inventory',
 'sweep': 'Sweep',
 'past-fixes': 'Research',
 'panel': 'Panel',
 'root-flaws': 'Panel',
 'load': 'Panel',
 'redactor': 'Report',
}
const MODES = { __proto__: null, scan: 'Codebase scan', changes: 'Change scan', commit: 'Commit scan' }
const TIERS = { __proto__: null, low: 'low', high: 'high', max: 'high' }
const RETRY = /:retry\d+| \(retry \d+\)/g
const QUESTIONS = ['present', 'ships', 'reachable', 'gain']
const PANEL = /^panel:(C\d+):v([123])$/
const PLACE = /^file: (.+)\nline: (\d+)$/m
const SED_SPANS = /(?<=[\s'";])(\d{1,9})(?:,(\d{1,9}|\/?\$))?p(?=[\s'";]|$)/g
const END_LINES = /\b(head|tail)\s+-([nc]?)\s*(\+?)(\d{1,9})\b/g
const READERS = /(^|[\s/;|&(])(cat|head|tail|sed|nl|awk|less|more)(\s|$)/
const SEARCHERS = /(^|[\s/;|&(])(grep|egrep|rg|ugrep|find|bfs|ls|git|wc|tree)(\s|$)/
const FILTERS = /(^|[\s/|&(])(grep|egrep|rg|ugrep|wc|git(\s+-[Cc]\s+\S+|\s+--\S+){0,8}\s+(log|grep))(\s(?!-E?vE?\s)|$)/
const QUOTED = /'[^']*'|"(\\.|[^"\\])*"|\\./gs
const WORDS = /'([^']*)'|"([^"]*)"|[^\s'"]+/g
const PIPELINES = new RegExp(String.raw`(${QUOTED.source}|[<>|]&|&>|(?<!\|)\|(?!\|)\s*|[^;&|\n])+`, 'gs')
const LOOP = /\b(?:for|read(?:\s+-r)?)\s+(\w+)/
const VARIABLES = /(?<=\$\{?)\w+/g
const MAX_READS = 200
const ASSIGNMENTS = new RegExp(String.raw`^(\s*[A-Za-z_]\w*=(${QUOTED.source}|\S)*)+`, 's')
const LITERAL = /^:\(literal\)/
const PROGRAM = /^(?!-)[\w./+-]*[\w+]$/
const OUTSIDE = /^(\/|~|[a-zA-Z]:|[a-zA-Z][a-zA-Z0-9+.-]*:\/)/
const ABSOLUTE = /^(\/|[a-zA-Z]:)/
const REFUSED_NAME = /[\r\n\t]|^.{401}/s
const WHOLE = 'research:repository'
const REVISION = /^(?![a-z]:).*:/is
const SOME_LINES = 120
const record = value => (value && typeof value === 'object' ? (value) : {})
const list = value => (Array.isArray(value) ? value : [])
function entries(value) {
 if (typeof value !== 'string') return list(value)
 try {
  const given = JSON.parse(value)
  if (typeof given === 'object') return list(given)
 } catch {}
 return value.split(',')
}
const whole = value => (Number.isSafeInteger(value) && Number(value) > 0 ? Number(value) : 0)
const countOf = value => whole(typeof value === 'string' && /^\d+$/.test(value.trim()) ? Number(value) : value)
const slashed = value => (typeof value === 'string' ? value.replaceAll('\\', '/').replace(LAST_SLASHES, '') : '')
const wordsOf = text => Array.from(text.matchAll(WORDS), ([word, single, double]) => single ?? double ?? word).filter(Boolean)
const leaf = path => path.slice(path.lastIndexOf('/') + 1)
export function parsed(given) {
 try {
  return record(typeof given === 'string' ? JSON.parse(given) : given)
 } catch {
  return {}
 }
}
export class Listener {
 #agents = new Map()
 #helpers = new Set()
 #cut = []
 #handbacks = new Map()
 #redactor = ''
 #ofChange = false
 constructor(args, strangers = new Set()) {
  this.root = slashed(args.scanRoot)
  this.runDir = slashed(args.runDir)
  this.reportDir = this.runDir.slice(0, this.runDir.lastIndexOf('/'))
  this.reportName = leaf(this.reportDir)
  this.redacted = false
  this.linesOf = () => 0
  this.knows = () => false
  this.strangers = strangers
  this.listed = false
  this.#ofChange = (args.mode || 'scan') !== 'scan'
  this.scan = new Scan({
   name: clean(leaf(this.root)),
   mode: MODES[String(args.mode)] ?? 'Scan',
   scope: entries(args.scope).map(entry => clean(entry)).filter(Boolean),
   branch: '',
   commit: '',
   files: countOf(args.fileCount) || countOf(args.scopeFileCount),
   ...effortOf(args),
  })
  const changed = list(parsed(args.changedFiles)).map(file => this.#relative(file))
  if (changed.length && this.#ofChange) this.scan.mapComponents([{ name: 'the change', paths: changed, literal: true }])
 }
 #researched(rest) {
  if (this.#ofChange) {
   const cut = rest.lastIndexOf(':')
   return cut < 0 ? [rest, ''] : [rest.slice(0, cut), rest.slice(cut + 1)]
  }
  if (this.scan.components.some(part => part.name === rest)) return [rest, '']
  return rest.endsWith(':all') ? [rest.slice(0, -':all'.length), 'all'] : [rest.replace(/:2$/, ''), '']
 }
 spawned(agentId, description, prompt) {
  const label = clean(String(description ?? '').replace(RETRY, ''))
  const role = label.split(':')[0]
  const rest = label.slice(role.length + 1)
  const panel = PANEL.exec(label)
  const named = role === 'research' ? this.#researched(rest) : ['', '']
  const [component, lens] = panel ? [panel[1], LENSES[Number(panel[2]) - 1]] : named
  const { components } = this.scan
  if (label === WHOLE && components.length && !components.some(each => each.name === component)) this.scan.mapComponents([])
  if (panel) {
   const [, file, line = 0] = PLACE.exec(prompt) ?? []
   this.scan.admit(component, lens, this.#relative(file), Number(line))
  }
  const sweeping = role === 'context' && this.scan.phases.get('Inventory').from !== undefined
  const stage = sweeping ? 'Sweep' : stageOf(label, role)
  const agent = this.scan.start({ label, stage, role, component, lens })
  this.#agents.set(agentId, agent)
  this.#cut = this.#cut.filter(each => each !== agent)
  if (role === 'redactor') {
   this.#redactor = agentId
   this.redacted = false
  }
 }
 owns(prompt) {
  return prompt.includes(this.reportName)
 }
 helps(agentId, parentId = '') {
  const parent = this.#agents.get(parentId)
  if (parent) {
   this.#agents.set(agentId, parent)
   this.#helpers.add(agentId)
  }
  return Boolean(parent)
 }
 called(agentId, tool, given, result) {
  const agent = this.#agents.get(agentId) ?? this.#again(agentId, this.#relative(given.file_path))
  if (!agent) return
  agent.tools++
  if (tool === 'SubagentHandback') {
   if (agent.role === 'redactor' && record(result).success === true) this.#handbacks.set(agentId, given.message)
   return
  }
  if (tool === 'StructuredOutput') return this.#answered(agent, given)
  if (agent.role === 'redactor') return
  if (tool === 'Read') agent.activity = this.#read(agent, given, record(result))
  else if (tool === 'Bash') agent.activity = this.#shell(agent, String(given.command ?? ''))
  else agent.activity = this.#search(agent, this.#relative(given.path))
 }
 ended(agentId = '', reason, answer) {
  const agent = this.#agents.get(agentId)
  if (!agent || this.#helpers.has(agentId) || agent.state !== 'running') return false
  const outcome = this.scan.candidates.get(agent.component)?.outcome
  const leftBehind = reason === 'aborted' && agent.role === 'panel' && (outcome === 'confirmed' || outcome === 'refuted')
  if (agent.role === 'redactor') {
   const word = String(this.#handbacks.get(agentId) ?? answer).trim()
   agent.answered = reason === 'answer' && word === 'finished'
   if (agentId === this.#redactor) this.redacted = agent.answered
  } else if (!agent.answered && !leftBehind) {
   this.#cut.push(agent)
   this.scan.vote(agent.component, agent.lens, 'lost')
  }
  const done = agent.answered || leftBehind
  this.scan.end(agent, done ? 'done' : 'failed', reason === 'aborted' && !done)
  return true
 }
 stopped(coverage) {
  const { emptyDiff, emptyScope } = parsed(coverage)
  const empty = whyEmpty(emptyDiff, emptyScope)
  const message = empty || 'The scan stopped before its report'
  this.scan.finish({ state: empty ? 'skipped' : 'failed', message, reportDir: '', verification: '' })
 }
 reported(jsonl, stamp) {
  const records = (jsonl ?? '')
   .split('\n')
   .filter(line => line.trim())
   .map(parsed)
  const reportDir = clean(this.reportName)
  const { verification: stamped, run_shape: shape, findings: counted } = parsed(stamp)
  const empty = whyEmpty(record(shape).empty_diff, record(shape).empty_scope)
  if (empty) return this.scan.finish({ state: 'skipped', message: empty, reportDir, verification: '' })
  if (jsonl === undefined || !stamped || records.some(found => typeof found.id !== 'string')) {
   const message = 'The report could not be read'
   return this.scan.finish({ state: 'failed', message, reportDir, verification: '' })
  }
  const findings = records.map(found => ({
   id: clean(found.id, 12),
   title: this.redacted ? clean(found.title) : WITHHELD,
   severity: clean(found.severity, 12).toUpperCase(),
   file: unquoted(String(found.file ?? '')),
   line: whole(found.line),
  }))
  const check = record(stamped)
  const verification = clean(check.status, 24)
  const message = missing(check, record(counted).total, findings.length)
  this.scan.finish({ state: message ? 'failed' : 'done', message, reportDir, verification }, findings)
 }
 described(text) {
  const revision = record(parsed(text).revision)
  Object.assign(this.scan.target, { branch: clean(revision.branch, 40), commit: clean(revision.commit, 7) })
 }
 #again(agentId, read) {
  const { candidates, components } = this.scan
  const homes = (name) =>
   components.find(each => each.name === name)?.paths ??
   (candidates.has(name) || !name ? [candidates.get(name)?.path ?? ''] : undefined)
  const holds = (home) => home && (read + '/').startsWith(home + '/')
  const listed = this.#cut.filter(each => homes(each.component)?.some(holds))
  const unlisted = this.#cut.filter(each => read && !homes(each.component) && each.stage === this.scan.stage)
  const near = this.#cut.length === 1 ? this.#cut : listed.length ? listed : unlisted
  const parts = new Set(near.map(each => homes(each.component) && each.component))
  const [agent] = near
  if (this.strangers.has(agentId) || !inside(read) || parts.size !== 1) return undefined
  this.#cut = this.#cut.filter(each => each !== agent)
  const tried = candidates.get(agent.component)
  if (tried) this.scan.admit(tried.id, agent.lens, tried.path, tried.line)
  this.#agents.set(agentId, this.scan.start(agent))
  return agent
 }
 #read(agent, given, result) {
  const path = this.#relative(given.file_path)
  if (result.type === 'file_unchanged') return 'Read ' + clean(path)
  const shown = record(result.file)
  const first = whole(shown.startLine) || whole(given.offset) || 1
  if (first > 1 && shown.numLines === 0) return 'Read ' + clean(path)
  const over = first + whole(shown.numLines) - 1 === shown.totalLines && String(shown.content).endsWith('\n')
  const lines = whole(shown.numLines) - Number(over) || whole(given.limit) || this.linesOf(path) || SOME_LINES
  if (inside(path) && (this.linesOf(path) || !this.listed)) this.scan.read(agent, path, first, first + lines - 1)
  return 'Read ' + clean(path)
 }
 #search(agent, path) {
  if (inside(path)) this.scan.search(agent, path)
  return 'Search ' + (clean(path) || 'the repository')
 }
 #shell(agent, command) {
  const text = command.slice(0, 2000)
  const [set = ''] = ASSIGNMENTS.exec(text) ?? []
  const rest = text.slice(set.length)
  const reads = this.#reads(rest).slice(0, MAX_READS)
  for (const [path, first, last] of reads) this.scan.read(agent, path, first, last)
  if (reads.length) return 'Read ' + clean(reads.at(-1)[0])
  if (SEARCHERS.test(slashed(command))) {
   const known = this.#named(rest).findLast(path => this.knows(path))
   const said = this.#search(agent, known ?? '')
   if (known) return said
  }
  const broken = /['"]/.test(text.replace(QUOTED, '')) || /[({`;|&]/.test(set)
  const [program = ''] = wordsOf(rest)
  return 'Run ' + (!broken && PROGRAM.test(program) ? clean(leaf(program), 24) : 'a command')
 }
 #named(text) {
  return wordsOf(text)
   .slice(1)
   .map(word => word.replace(LITERAL, ''))
   .flatMap(word => (this.knows(this.#relative(word)) ? [word] : word.split(/[\s;|&]/)))
   .filter(word => !word.includes('='))
   .map(word => this.#relative(word.replace(REVISION, '')))
 }
 #reads(command) {
  const loops = new Map()
  return (command.match(PIPELINES) ?? []).flatMap(pipeline => {
   const files = () => this.#named(pipeline).filter(path => this.linesOf(path))
   const [, each] = LOOP.exec(pipeline) ?? []
   if (each) loops.set(each, files())
   const spelled = slashed(pipeline.replace(ASSIGNMENTS, ''))
   if (!READERS.test(spelled) || FILTERS.test(spelled)) return []
   const looped = [...new Set(pipeline.match(VARIABLES))].flatMap(name => loops.get(name) ?? [])
   return [...looped, ...files()].flatMap(path => linesShown(spelled, this.linesOf(path)).map(span => [path, ...span]))
  })
 }
 #answered(agent, answer) {
  agent.answered = true
  if (agent.role === 'panel') {
   const older = this.scan.target.olderCounts ? 'older' : 'refute'
   const unread = this.#namesNoFile(answer.unopenedFile) ? 'refute' : 'abstain'
   const votes = { __proto__: null, TRUE_POSITIVE: 'confirm', PREDATES_CHANGE: older, COULD_NOT_READ: unread }
   const word = String(answer.verdict)
   const sure = QUESTIONS.every(question => record(answer[question]).answer === 'YES')
   const real = word === 'TRUE_POSITIVE' || word === 'PREDATES_CHANGE'
   this.scan.vote(agent.component, agent.lens, real && !sure ? 'refute' : (votes[word] ?? 'refute'))
  } else if (agent.role === 'inventory') {
   const parts = list(answer.components).map(record)
   if (!parts.length) return
   this.scan.mapComponents(
    parts.map(part => ({ name: clean(part.name), paths: list(part.paths).map(path => this.#relative(path)) })),
   )
  } else {
   for (const { file, line } of list(answer.findings).map(record)) {
    this.scan.lead(agent, this.#relative(file), whole(line))
   }
  }
 }
 #namesNoFile(name) {
  const written = typeof name === 'string' ? name.trim() : ''
  const spelled = slashed(written)
  const path = (this.#below(spelled) ?? spelled).replace(/^\.\//, '')
  const leaves = path.split('/').some(part => part.trim() === '..')
  return !path || path === '.' || REFUSED_NAME.test(written) || OUTSIDE.test(path) || leaves
 }
 #below(path) {
  const [spelled, root] = [path, this.root].map(each => each.replace(/^[a-z]:/, drive => drive.toUpperCase()))
  if (spelled === root) return ''
  return spelled.startsWith(root + '/') ? spelled.slice(root.length + 1) : undefined
 }
 #relative(given) {
  const path = slashed(given)
  if (path === '.') return ''
  const rest = this.#below(this.root[1] === ':' ? path.replace(/^\/([a-z])\//i, '$1:/') : path)
  if (rest !== undefined) return rest
  const name = this.root.slice(this.root.lastIndexOf('/')) + '/'
  const below = path.slice(path.indexOf(name) + name.length)
  return ABSOLUTE.test(path) && path.includes(name) && this.knows(below) ? below : path.replace(/^\.\//, '')
 }
}
export const inside = path => !/^(\/|\\|[A-Za-z]:|CLAUDE-SECURITY-)|(^|[/\\])\.\.([/\\]|$)/.test(path)
function effortOf(args) {
 const high = Boolean(clean(args.range)) && clean(args.changeScanEffort).toLowerCase() === 'high'
 return { effort: high ? 'high' : (TIERS[clean(args.effort).toLowerCase()] ?? 'medium'), olderCounts: high }
}
function stageOf(label, role) {
 if (label.startsWith('load:1:')) return 'Setup'
 if (/^load:(changed|packs|paths):/.test(label)) return 'Research'
 return STAGE_OF[role] ?? 'Research'
}
function linesShown(pipeline, lines) {
 const found = [...pipeline.matchAll(SED_SPANS)]
 const ends = [...pipeline.slice(found.at(-1)?.index).matchAll(END_LINES)]
 const spans = found.map(([, first, last = first]) =>
  [Number(first), last.endsWith('$') ? lines : Number(last)].map(line => Math.min(Math.max(line, 1), lines)),
 )
 return (spans.length ? spans : [[1, lines]]).map(([first, last]) => {
  for (const [, end, unit, plus, digits] of ends) {
   const count = Math.max(unit === 'c' ? Math.ceil(Number(digits) / BYTES_PER_LINE) : Number(digits), 1)
   if (end === 'head') last = Math.min(first + count - 1, last)
   else first = plus ? Math.min(first + count - 1, last) : Math.max(last - count + 1, first)
  }
  return [first, last]
 })
}
function whyEmpty(emptyDiff, emptyScope) {
 if (emptyDiff === true) return 'No file has changed'
 return emptyScope === true ? 'The scope holds no tracked file' : ''
}
function missing(check, total, listed) {
 const back = whole(check.researchers_returned)
 const lost = back && whole(check.researchers_dispatched) - back
 return [
  check.status !== 'verified' && 'The report is not verified: ' + (clean(check.reason, 400) || 'it gives no reason') + '.',
  lost > 0 && 'The reading of ' + lost + plural(lost, ' researcher') + ' is missing.',
  list(check.refused_findings).length > 0 && 'A refused finding is not in the list.',
  listed !== total && "A finding may be missing: the report's counts do not agree.",
 ]
  .filter(Boolean)
  .join(' ')
}
function unquoted(name) {
 try {
  return decodeURIComponent(name)
 } catch {
  return name
 }
}
