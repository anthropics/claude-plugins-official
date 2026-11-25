import { sum, whole } from './numbers.mjs';
import { Widths } from './text.mjs';
export const LENSES = ['reachability', 'impact', 'defenses'];
export const SEVERITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
export const STAGES = ['Setup', 'Inventory', 'Sweep', 'Research', 'Panel', 'Report'];
const STATES = ['waiting', 'running', 'done', 'failed', 'skipped'];
const VOTES = ['pending', 'confirm', 'refute', 'abstain'];
const OUTCOMES = ['testing', 'confirmed', 'refuted', 'unsettled'];
const RECENT_TOUCHES = 600;
const RECENT_NOTES = 400;
const RANK = { running: 3, waiting: 2, failed: 1, done: 0, skipped: 0 };
export const fields = (json) => typeof json === 'object' && json !== null && !Array.isArray(json) ? json : {};
export const text = (json) => typeof json === 'string' ? json.replace(/[\ud800-\udfff]/gu, '\ufffd') : '';
const items = (json) => (Array.isArray(json) ? json : []);
const texts = (json) => items(json).map(text);
const number = (json) => typeof json === 'number' && Number.isFinite(json) ? json : undefined;
const count = (json) => whole(number(json) ?? 0);
export const index = (json, length) => typeof json === 'number' && json >= 0 && json < length ? json | 0 : undefined;
const oneOf = (names, json) => names.find(name => name === json) ?? names[0];
const pair = (json) => Array.isArray(json) && json.length === 2 ? [count(json[0]), count(json[1])] : undefined;
const readTarget = (json) => ({
	name: text(json.name),
	mode: text(json.mode),
	effort: text(json.effort),
	scope: texts(json.scope),
	branch: text(json.branch),
	commit: text(json.commit),
	dirty: json.dirty === true,
	model: text(json.model),
	version: text(json.version),
	sandboxed: json.sandboxed === true,
	hosts: texts(json.hosts),
	writable: texts(json.writable),
});
const readEnding = (json) => ({
	state: oneOf(STATES, json.state),
	message: text(json.message),
	reportDir: text(json.report_dir),
	files: texts(json.files),
	verification: text(json.verification),
});
const readPhase = (json) => ({
	stage: oneOf(STAGES, json.stage),
	state: oneOf(STATES, json.state),
	started: number(json.started),
	ended: number(json.ended),
});
const readTotals = (json) => ({
	agents: count(json.agents),
	running: count(json.running),
	done: count(json.done),
	failed: count(json.failed),
	tools: count(json.tools),
	tokens: count(json.tokens),
	files: count(json.files),
	filesRead: count(json.files_read),
	lines: count(json.lines),
	linesRead: count(json.lines_read),
	leads: count(json.leads),
	candidates: count(json.candidates),
	confirmed: count(json.confirmed),
	refuted: count(json.refuted),
});
const readComponent = (json, plots) => ({
	name: text(json.name),
	language: text(json.language),
	plots: items(json.plots).flatMap(plot => index(plot, plots) ?? []),
});
const readAgent = (json, plots) => ({
	id: count(json.id),
	label: text(json.label),
	name: text(json.name),
	role: text(json.role),
	component: text(json.component),
	lens: text(json.lens),
	state: oneOf(STATES, json.state),
	started: number(json.started),
	ended: number(json.ended),
	tools: count(json.tools),
	tokens: count(json.tokens),
	plot: index(json.plot, plots),
	activity: text(json.activity),
});
const readSpot = (json, plots) => ({
	plot: index(json.plot, plots),
	plotLine: count(json.plot_line),
});
const readCandidate = (json, plots) => ({
	id: text(json.id),
	path: text(json.path),
	line: count(json.line),
	...readSpot(json, plots),
	votes: LENSES.map(lens => oneOf(VOTES, fields(json.votes)[lens])),
	outcome: oneOf(OUTCOMES, json.outcome),
	settled: number(json.settled),
});
const readFinding = (json, plots) => ({
	id: text(json.id),
	title: text(json.title),
	severity: text(json.severity),
	confidence: text(json.confidence),
	file: text(json.file),
	line: count(json.line),
	...readSpot(json, plots),
	category: text(json.category),
	cwe: text(json.cwe),
	symbol: text(json.symbol),
	snippet: text(json.snippet),
	description: text(json.description),
	impact: text(json.impact),
	scenario: text(json.exploit_scenario),
	preconditions: texts(json.preconditions),
	recommendation: text(json.recommendation),
});
const readVisit = (json) => ({
	reads: count(json.reads),
	spans: items(json.spans).flatMap(held => {
		const span = pair(held);
		return span && span[0] <= span[1] ? [span] : [];
	}),
	rev: count(json.rev),
});
function readTouch(json, plots) {
	const [from, to] = pair(json.plots) ?? [0, 0];
	const end = Math.min(to, plots);
	const start = Math.min(from, end);
	return {
		rev: count(json.rev),
		at: number(json.at) ?? 0,
		agent: count(json.agent),
		start,
		end,
		file: json.kind === 'read' && start < end ? start : undefined,
		first: count(json.first),
		last: count(json.last),
	};
}
const readNote = (json) => ({ at: number(json.at) ?? 0, text: text(json.text) });
const column = (agent) => agent.lens || agent.role;
export const crossing = (component, heading) => `${component}\0${heading}`;
const outranks = (agent, other) => RANK[agent.state] === RANK[other.state] ? agent.label < other.label : RANK[agent.state] > RANK[other.state];
function renew(held, fresh) {
	const at = held.findIndex(old => old.id === fresh.id);
	if (at < 0)
		held.push(fresh);
	else
		held[at] = fresh;
}
export class Scan {
	plots;
	widths = new Widths();
	rev = 0;
	now = 0;
	target = readTarget({});
	result = readEnding({ state: 'running' });
	phases = STAGES.map(stage => readPhase({ stage }));
	totals = readTotals({});
	components = [];
	divisions = 0;
	agents = [];
	leads = [];
	candidates = [];
	findings = [];
	visits = [];
	touches = [];
	notes = [];
	verifiers = new Map();
	constructor(plots) {
		this.plots = plots;
	}
	get running() {
		return this.result.state === 'running';
	}
	get latest() {
		return this.phases.reduce((last, phase) => (phase.started === undefined ? last : phase));
	}
	took({ started, ended }) {
		return (ended ?? this.now) - (started ?? 0);
	}
	atWork() {
		return this.agents.filter(agent => agent.state === 'running');
	}
	verifier(id, lens) {
		return this.verifiers.get(crossing(id, lens));
	}
	team() {
		return this.agents.filter(agent => agent.role === 'research');
	}
	columns() {
		return [...new Set(this.team().map(column))];
	}
	cover() {
		const place = (agent) => crossing(agent.component, column(agent));
		const attempts = new Map(this.team().map(agent => [crossing(place(agent), agent.label), agent]));
		const cover = new Map();
		for (const agent of attempts.values()) {
			const best = cover.get(place(agent));
			if (!best || outranks(agent, best))
				cover.set(place(agent), agent);
		}
		return cover;
	}
	readOf(part) {
		const spans = part.plots.flatMap(plot => this.visits[plot]?.spans ?? []);
		return [sum(spans.map(([first, last]) => last - first + 1)), sum(part.plots.map(plot => this.plots[plot].lines))];
	}
	apply(delta) {
		const plots = this.plots.length;
		const each = (list, read) => items(list).map(item => read(fields(item), plots));
		this.widths.learn(text(delta.wide), text(delta.marks));
		this.rev = count(delta.rev);
		this.now = number(delta.now) ?? this.now;
		this.target = readTarget(fields(delta.target));
		this.result = readEnding(fields(delta.result));
		this.totals = readTotals(fields(delta.totals));
		for (const phase of each(delta.phases, readPhase))
			this.phases[STAGES.indexOf(phase.stage)] = phase;
		if (Array.isArray(delta.components)) {
			this.components = each(delta.components, readComponent);
			this.divisions++;
		}
		if (Array.isArray(delta.findings))
			this.findings = each(delta.findings, readFinding);
		for (const agent of each(delta.agents, readAgent))
			renew(this.agents, agent);
		this.verifiers = new Map(this.atWork().map(agent => [crossing(agent.component, agent.lens), agent]));
		for (const one of each(delta.candidates, readCandidate))
			renew(this.candidates, one);
		for (const lead of each(delta.leads, readSpot))
			this.leads.push(lead);
		for (const visit of items(delta.visits).map(fields)) {
			const plot = index(visit.plot, plots);
			if (plot !== undefined)
				this.visits[plot] = readVisit(visit);
		}
		this.touches = this.touches.concat(each(delta.touches, readTouch)).slice(-RECENT_TOUCHES);
		this.notes = this.notes.concat(each(delta.notes, readNote)).slice(-RECENT_NOTES);
	}
}
