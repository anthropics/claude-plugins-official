export const STAGES = ['Inventory', 'Sweep', 'Research', 'Panel', 'Report']
export const LENSES = ['reachability', 'impact', 'defenses']
const LAST_LENS = LENSES.at(-1)
export const SEVERITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const RECENT_TOUCHES = 300
const LEADS = 200
const NOT_VOTED = Object.fromEntries(LENSES.map(lens => [lens, 'pending']))
export const moment = () => performance.now() / 1000
export class Scan {
 #aborted = new Set()
 #askedAtOnce = new Set()
 constructor(target) {
  this.target = target
  this.began = Date.now()
  this.ended = undefined
  this.rev = 1
  this.result = { state: 'running', message: '', reportDir: '', verification: '' }
  this.phases = new Map(STAGES.map(stage => [stage, { state: 'waiting' }]))
  this.components = []
  this.mapped = -Infinity
  this.finished = -Infinity
  this.agents = []
  this.leads = []
  this.candidates = new Map()
  this.findings = []
  this.visits = new Map()
  this.touches = []
  this.forgotten = 0
  this.linesRead = 0
  this.quietSince = undefined
 }
 now() {
  return this.ended ?? ((this.quietSince ?? Date.now()) - this.began) / 1000
 }
 get running() {
  return this.result.state === 'running'
 }
 get reported() {
  return !this.running && Boolean(this.result.reportDir)
 }
 get stage() {
  return STAGES.findLast(stage => this.phases.get(stage)?.from !== undefined) ?? 'Setup'
 }
 spent(stage) {
  const { from, to } = this.phases.get(stage) ?? {}
  return from === undefined ? undefined : (to ?? this.now()) - from
 }
 get working() {
  return this.agents.filter(agent => agent.state === 'running')
 }
 openLeads(mapped) {
  if (this.stage === 'Report') return []
  const tried = new Set([...this.candidates.values()].map(({ path }) => path))
  return this.leads.slice(-LEADS).filter(({ path }) => mapped(path) && !tried.has(path))
 }
 totals() {
  const outcomes = [...this.candidates.values()].map(candidate => candidate.outcome)
  return {
   agents: this.agents.length,
   running: this.working.length,
   failed: this.agents.filter(agent => agent.state === 'failed').length,
   tools: this.agents.reduce((n, agent) => n + agent.tools, 0),
   files: this.target.files,
   filesRead: this.visits.size,
   linesRead: this.linesRead,
   leads: this.leads.length,
   candidates: outcomes.length,
   confirmed: outcomes.filter(outcome => outcome === 'confirmed').length,
   refuted: outcomes.filter(outcome => outcome === 'refuted').length,
   findings: this.findings.length,
  }
 }
 enter(stage) {
  if (!this.running) return
  const { from, to } = this.phases.get(stage) ?? {}
  const now = this.now()
  this.phases.set(stage, { state: 'running', from: (from ?? now) + (now - (to ?? now)) })
  this.#settle()
 }
 mapComponents(components) {
  this.components = components
  this.mapped = moment()
  this.rev++
 }
 start(facts) {
  let agent = this.agents.find(each => each.label === facts.label && each.state === 'failed')
  if (!agent) {
   const counts = { tools: 0, leads: 0, endedRev: 0, answered: false }
   agent = { ...facts, ...counts, id: this.agents.length, state: 'running', path: '', activity: '' }
   this.agents.push(agent)
  }
  agent.state = 'running'
  this.#aborted.delete(agent)
  if (!this.running || this.quietSince !== undefined) this.resume()
  this.enter(agent.stage)
  return agent
 }
 end(agent, state, aborted = false) {
  Object.assign(agent, { state, activity: '', endedRev: this.rev })
  if (aborted) this.#aborted.add(agent)
  this.#settle(this.stage !== 'Report')
 }
 read(agent, path, first, last) {
  const visit = this.visits.get(path) ?? { reads: 0, spans: [] }
  const before = covered(visit)
  visit.reads++
  visit.spans = joined([...visit.spans, [first, Math.max(first, last)]])
  this.linesRead += covered(visit) - before
  this.visits.set(path, visit)
  agent.path = path
  this.#touch(agent, 'read', path, first, last)
 }
 list(paths) {
  this.target.files = paths.size
  for (const [path, visit] of this.visits) {
   if (paths.has(path)) continue
   this.linesRead -= covered(visit)
   this.visits.delete(path)
  }
 }
 search(agent, path) {
  this.#touch(agent, 'search', path, 0, 0)
 }
 lead(agent, path, line) {
  agent.leads++
  this.leads.push({ path, line, at: moment() })
  this.rev++
 }
 admit(id, lens, path, line) {
  const votes = this.candidates.get(id)?.votes ?? NOT_VOTED
  if (lens === LAST_LENS && Object.values(votes).every(vote => vote === 'pending')) this.#askedAtOnce.add(id)
  const last = this.#askedAtOnce.has(id) ? {} : { [LAST_LENS]: 'pending' }
  this.candidates.set(id, { id, path, line, votes: { ...votes, ...last, [lens]: 'pending' }, outcome: 'testing' })
  this.rev++
 }
 vote(id, lens, vote) {
  const candidate = this.candidates.get(id)
  if (candidate?.votes[lens] !== 'pending') return
  candidate.votes[lens] = vote
  this.rev++
  if (this.#askedAtOnce.has(id) && candidate.outcome !== 'testing') return
  const votes = Object.values(candidate.votes)
  const outcome = outcomeOf(votes, this.#askedAtOnce.has(id))
  if (!votes.includes('pending') || outcome !== 'unsettled') {
   candidate.settled = moment()
   candidate.outcome = outcome
  }
 }
 finish(result, findings = []) {
  this.ended = ((this.quietSince ?? Date.now()) - this.began) / 1000
  this.quietSince = undefined
  this.finished = moment()
  this.result = result
  this.findings = findings
  for (const agent of this.working) this.end(agent, 'failed', true)
  const stopped = [this.stage, ...Array.from(this.#aborted, agent => agent.stage)]
  const cut = result.state === 'failed' && !result.verification
  for (const [stage, phase] of this.phases) {
   const failed = cut && (phase.state === 'failed' || stopped.includes(stage))
   if (failed || phase.state === 'running' || phase.state === 'failed') {
    phase.state = failed ? 'failed' : 'done'
    phase.to ??= this.ended
   } else if (phase.state === 'waiting') phase.state = 'skipped'
  }
  this.rev++
 }
 reopen() {
  this.#askedAtOnce.clear()
 }
 resume() {
  this.#aborted.clear()
  this.phases.set('Report', { state: 'waiting' })
  this.began = Date.now() - this.now() * 1000
  this.ended = undefined
  this.quietSince = undefined
  this.result = { ...this.result, state: 'running', message: '' }
  for (const phase of this.phases.values()) phase.state = phase.from === undefined ? 'waiting' : 'running'
  this.#settle(true)
 }
 #touch(agent, kind, path, first, last) {
  this.touches.push({ rev: ++this.rev, at: moment(), agent: agent.id, kind, path, first, last })
  if (this.touches.length > RECENT_TOUCHES) this.forgotten = this.touches.shift()?.rev ?? 0
 }
 #settle(furthest = false) {
  const busy = new Set(this.working.map(agent => agent.stage))
  for (const stage of STAGES.slice(0, Math.max(STAGES.indexOf(this.stage) + Number(furthest), 0))) {
   const phase = this.phases.get(stage)
   if (!phase) continue
   if (phase.from === undefined) phase.state = 'skipped'
   else if (phase.state === 'running' && !busy.has(stage)) {
    phase.state = 'done'
    phase.to ??= this.now()
   }
  }
  this.rev++
 }
}
function outcomeOf(votes, atOnce) {
 const cast = (kind) => votes.filter(each => each === kind).length
 if (cast('lost') && !atOnce) return 'unsettled'
 if (cast('confirm') + cast('older') >= 2) return 'confirmed'
 return cast('refute') >= 2 ? 'refuted' : 'unsettled'
}
const covered = visit => visit.spans.reduce((n, [low, high]) => n + high - low + 1, 0)
function joined(spans) {
 const out = []
 for (const [low, high] of spans.sort((a, b) => a[0] - b[0])) {
  const last = out.at(-1)
  if (last && low <= last[1] + 1) last[1] = Math.max(last[1], high)
  else out.push([low, high])
 }
 return out
}
