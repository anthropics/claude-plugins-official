import { BOLD, CHIP, ink, on } from './canvas.mjs';
import * as look from './look.mjs';
import { DIM, ELBOW, FAINT, FAULT, LIVE, PLACE, RULE, SOFT, STRONG, TEXT } from './look.mjs';
import { clamp, div, nearest, round } from './numbers.mjs';
import * as p from './palette.mjs';
import { crossing, LENSES } from './scan.mjs';
import { first, times } from './text.mjs';
import * as words from './words.mjs';
export const FINDINGS = 'Findings';
export const RESULT = 'Result';
export const PANEL = 'Panel';
export const AGENTS = 'Agents';
export const COMPONENTS = 'Components';
export const LEGEND = 'Map legend';
export const TARGET = 'Target';
export const NARRATION = 'Narration';
const MEANINGS = [
	['⣿⣷', p.SLATE, 'The shape of code that no agent has read'],
	['⣿⣷', p.CLAY, 'Lines that an agent reads now'],
	['⣿⣷', p.STONE, 'Lines that were read'],
	['⣿⣷', p.SKY, 'Files under a search'],
	['✻ ', p.IVORY, 'An agent'],
	['◆ ', p.AMBER, 'A lead that a researcher reported'],
	['●✕', p.VIOLET, 'A verifier confirms or refutes a candidate'],
];
const OUTCOME_INK = { testing: DIM, confirmed: TEXT, refuted: FAINT, unsettled: DIM };
const CANDIDATE_CELLS = 27;
const WIDEST_ID = 8;
const MOST_NEEDS = 50;
const LONGEST_BAR = 28;
const NAME_WIDTH = 11;
const CLOCK_WIDTH = 7;
export class Pane {
	name;
	sign;
	facts;
	rows;
	layout;
	constructor(name, sign, facts, rows, layout = {}) {
		this.name = name;
		this.sign = sign;
		this.facts = facts;
		this.rows = rows;
		this.layout = { head: [], focus: 0, across: 1, items: rows.length, lead: 0, notes: [], ...layout };
	}
	get height() {
		return 1 + this.layout.head.length + this.rows.length;
	}
	draw(canvas, area, moved = 0, held) {
		const { head, focus, across, items, lead, notes } = this.layout;
		const room = area.h - 1 - head.length;
		const last = Math.max(this.rows.length - Math.max(room, 0), 0);
		const near = clamp(focus - div(room, 3), 0, last);
		const home = notes.find(note => note >= near) ?? near;
		const top = clamp((held ?? home) + moved, 0, Math.max(last, home));
		const from = Math.max(top * across + 1 - lead, 1);
		const to = Math.min((top + room) * across, items) - lead;
		const range = last > 0 && notes.length === 0 ? ` ${from}-${to}` : '';
		const end = area.end - range.length;
		const title = [
			[this.sign, DIM],
			[this.name, STRONG],
			[' ', DIM],
		];
		const titled = canvas.whole(area.x, area.y, end - 1, [title, ...this.facts.map(fact => [fact])]);
		const ruled = canvas.put(titled + 1, area.y, times('─', area.w), RULE, end);
		canvas.put(ruled, area.y, range, FAINT);
		canvas.lines(area.below(1), head);
		canvas.lines(area.below(1 + head.length), this.rows.slice(top));
		if (moved === 0)
			return held === undefined ? undefined : top;
		return top === home ? undefined : top;
	}
}
export function table(canvas, rows, indent, room) {
	const gap = times(' ', indent);
	return rows.flatMap(([label, text, pen]) => canvas.widths
		.wrap(text, room - indent)
		.map((line, n) => [...(n ? [[gap, pen]] : label), [line, pen]]));
}
export const prose = (canvas, text, pen, room) => table(canvas, [[[], text, pen]], 0, room);
const widest = (canvas, texts) => texts.reduce((most, text) => Math.max(most, canvas.widths.width(text)), 0);
const idCells = (canvas, ids, gap) => clamp(widest(canvas, ids) + gap, 4, WIDEST_ID);
const placed = (path, line) => (line > 0 ? `${path}:${line}` : path);
function file(canvas, path, line, width, pen) {
	const sign = [look.kind(path), FAINT];
	const room = width - canvas.measure([sign]);
	const place = placed(path, line);
	const names = place.split('/');
	let tail = '';
	for (let n = names.length - 1; n >= 0; n--) {
		const longer = names.slice(n).join('/');
		if (canvas.widths.width(longer) > room)
			break;
		tail = longer;
	}
	return [sign, [canvas.widths.pad(tail || canvas.widths.fitEnd(place, room), room), pen]];
}
export function target(canvas, scan, room) {
	const facts = scan.target;
	const joined = (names, none) => (names.length ? names.join(', ') : none);
	const counted = (n, many) => `${words.grouped(n)} ${words.noun(n, many)}`;
	const limits = facts.sandboxed
		? [
			['Network', joined(facts.hosts, 'none')],
			['Writes to', joined(facts.writable, 'nothing')],
		]
		: [['Sandbox', 'none: agents run with your access']];
	const rows = [
		['Scope', joined(facts.scope, 'the whole repository')],
		['Repository', `${counted(scan.totals.files, 'files')}, ${counted(scan.totals.lines, 'lines')}`],
		...limits,
		['Scan', words.listed([facts.mode, facts.effort, facts.model, facts.version], ', ')],
	].map(([name, value]) => [[[name.padEnd(NAME_WIDTH), DIM]], canvas.widths.fit(value, 200), SOFT]);
	return new Pane(TARGET, look.TARGET, [], table(canvas, rows, NAME_WIDTH, room));
}
export function legend(canvas, room) {
	const rows = MEANINGS.map(([dots, colour, means]) => [[[dots + '  ', ink(colour)]], means, DIM]);
	return new Pane(LEGEND, look.MAP, [], table(canvas, rows, 4, room));
}
export function agents(canvas, scan, room, most, beat) {
	const { running, done, failed } = scan.totals;
	const facts = [[` ${running} at work`, LIVE]];
	if (failed > 0)
		facts.push([` · ${failed} failed`, FAULT]);
	facts.push([` · ${done} done`, DIM]);
	const ended = (one) => one.ended ?? Number.MAX_VALUE;
	const shown = scan.agents
		.filter(one => one.started !== undefined)
		.sort((a, b) => ended(b) - ended(a))
		.slice(0, most);
	const names = shown.map(one => agentName(scan, one));
	const wide = Math.min(widest(canvas, names), div(room, 2) - 2);
	const rows = shown.map(one => agent(canvas, scan, one, wide, room, beat));
	return new Pane(AGENTS, look.TEAM, facts, rows);
}
function agentName(scan, one) {
	if (scan.components.length !== 1)
		return one.name;
	const suffix = ` · ${scan.components[0].name}`;
	return one.name.endsWith(suffix) ? one.name.slice(0, -suffix.length) : one.name;
}
function agent(canvas, scan, one, nameWidth, room, beat) {
	const took = room > 46 ? (' ' + words.clock(scan.took(one))).padStart(6) : '';
	const rest = room - nameWidth - took.length - 4;
	const [glyph, pen] = look.state(one.state, beat, one.id);
	const name = ` ${canvas.widths.pad(agentName(scan, one), nameWidth)}  `;
	if (one.state !== 'running') {
		const did = `${one.tools} ${words.noun(one.tools, 'calls')} · ${nearest(one.tokens / 1000)}k tokens`;
		return [
			[glyph, one.state === 'done' ? FAINT : pen],
			[name + canvas.widths.pad(did, rest) + took, FAINT],
		];
	}
	return [[glyph, ink(p.lens(one.lens) ?? p.CLAY)], [name, SOFT], ...doing(canvas, one.activity, rest), [took, FAINT]];
}
function doing(canvas, activity, room) {
	const path = activity.slice(activity.indexOf(' ') + 1);
	if (activity.startsWith('Read '))
		return file(canvas, path, 0, room, DIM);
	if (!activity.startsWith('Search '))
		return [[canvas.widths.pad(activity || 'Starting', room), DIM]];
	const sign = [look.SEARCH, DIM];
	return [sign, [canvas.widths.pad(path, room - canvas.measure([sign])), DIM]];
}
export function components(canvas, scan, room, most, beat) {
	const lenses = scan.columns();
	const cover = scan.cover();
	const all = scan.components.map(part => part.name);
	const nameWidth = Math.min(widest(canvas, all), div(room, 3));
	const signWidth = canvas.measure([[look.kind(''), DIM]]);
	const spare = room - nameWidth - signWidth - 7;
	const uncut = Math.max(widest(canvas, lenses.map(words.lens)) + 1, 7);
	const step = [uncut, 7, 4].find(n => spare >= n * lenses.length + n - 1) ?? 2;
	const free = Math.min(spare - step * lenses.length, LONGEST_BAR);
	const heading = (lens) => {
		const short = first(words.lens(lens), step - 1);
		const left = Math.max(div(step - 1 - canvas.widths.width(short), 2), 0);
		return times(' ', left) + canvas.widths.pad(short, step - left);
	};
	const parts = scan.components.map(part => {
		const team = lenses.map(lens => cover.get(crossing(part.name, lens)));
		return { part, team, busy: team.some(one => one?.state === 'running') };
	});
	if (parts.length > most)
		parts.sort((a, b) => Number(b.busy) - Number(a.busy));
	const rows = parts.map(({ part, team, busy }) => {
		const [read, lines] = scan.readOf(part);
		const halves = round(2 * Math.max(free, 0) * Math.min(read / Math.max(lines, 1), 1));
		return [
			[look.kind(part.language), DIM],
			[canvas.widths.pad(part.name, nameWidth + 2), busy ? TEXT : SOFT],
			...team.flatMap((one) => [
				[times(' ', div(step, 2) - 1), DIM],
				one ? look.state(one.state, beat, one.id) : [' ', DIM],
				[times(' ', step - div(step, 2)), DIM],
			]),
			[times('━', div(halves, 2)) + times('╸', halves % 2), busy ? LIVE : SOFT],
			[times(lines ? '─' : ' ', free - div(halves + 1, 2)), RULE],
			[(free >= 0 ? ' ' : '') + words.percent(read, lines).padStart(4), DIM],
		];
	});
	const head = times(' ', nameWidth + 2 + signWidth) + lenses.map(heading).join('') + 'Read';
	return new Pane(COMPONENTS, look.LAYERS, [[` ${rows.length}`, DIM]], rows, { head: [[[head, FAINT]]] });
}
export function panel(canvas, scan, room, beat) {
	const across = Math.max(div(room, CANDIDATE_CELLS), 1);
	const span = div(room + 2, across);
	const ids = idCells(canvas, scan.candidates.map(one => one.id), 0);
	const rows = Array.from({ length: Math.ceil(scan.candidates.length / across) }, (_, row) => scan.candidates
		.slice(row * across, (row + 1) * across)
		.flatMap((one) => [...candidate(canvas, scan, one, ids, span - 2, beat), ['  ', DIM]]));
	const names = room > 50 ? LENSES : LENSES.map(lens => lens[0].toUpperCase());
	const facts = names.map((name, n) => [' ● ' + name, ink(p.LENS[n])]);
	const testing = scan.candidates.findIndex(one => one.outcome === 'testing');
	const focus = div(Math.max(testing, 0), across);
	return new Pane(PANEL, look.SCALES, facts, rows, { focus, across, items: scan.candidates.length });
}
function candidate(canvas, scan, one, ids, room, beat) {
	const refuted = one.outcome === 'refuted';
	const votes = one.votes.map((vote, n) => {
		const verifier = vote === 'pending' ? scan.verifier(one.id, LENSES[n]) : undefined;
		const glyph = verifier ? look.spinner(beat, verifier.id) : look.VOTE[vote];
		const colour = vote === 'pending' && !verifier ? p.SLATE : p.LENS[n];
		return [' ' + glyph, ink(p.mix(colour, p.PAPER, refuted ? 0.45 : 0))];
	});
	const settled = one.settled === undefined ? '' : one.outcome;
	const verdict = room > 40 ? settled.padStart(10) : '';
	const pen = OUTCOME_INK[one.outcome];
	return [
		[canvas.widths.pad(one.id, ids), refuted ? FAINT : STRONG],
		...votes,
		['  ', pen],
		...file(canvas, one.path, one.line, room - ids - 8 - verdict.length, pen),
		[verdict, one.outcome === 'confirmed' ? LIVE : FAINT],
	];
}
export function log(canvas, scan, room) {
	const rows = [];
	const notes = [];
	for (const note of scan.notes) {
		const stamp = [[words.clock(note.at).padStart(CLOCK_WIDTH) + '  ', FAINT]];
		notes.push(rows.length);
		for (const row of table(canvas, [[stamp, note.text, SOFT]], CLOCK_WIDTH + 2, room))
			rows.push(row);
	}
	return new Pane(NARRATION, look.NOTE, [], rows, { focus: rows.length, notes });
}
export function findings(canvas, listed, room, chosen) {
	const ids = idCells(canvas, listed.map(finding => finding?.id ?? ''), 1);
	const narrow = room < 60;
	const levelWidth = narrow ? 5 : 10;
	const rows = listed.map((finding, n) => {
		const paper = n === chosen ? p.LIFTED : p.PAPER;
		const bar = n === chosen ? '▎' : ' ';
		const title = n === chosen ? on(p.IVORY, paper) + CHIP : SOFT;
		if (!finding) {
			return [
				[bar + '✻   ', on(p.CLAY, paper)],
				[canvas.widths.pad('Summary and warnings', room - 5), title],
			];
		}
		const colour = p.severity(finding.severity);
		const level = narrow ? words.short(finding.severity) : finding.severity;
		return [
			[bar, on(colour, paper)],
			[canvas.widths.pad(finding.id, ids), on(p.IVORY, paper) + BOLD],
			[canvas.widths.pad(level, levelWidth), on(colour, paper) + BOLD],
			[canvas.widths.pad(finding.title, room - 1 - ids - levelWidth), title],
		];
	});
	const lead = listed[0] ? 0 : 1;
	return new Pane(FINDINGS, look.SHIELD, [[` ${listed.length - lead}`, DIM]], rows, { focus: chosen, lead });
}
export function record(canvas, finding, room) {
	const { widths } = canvas;
	const colour = p.severity(finding.severity);
	const code = widths.wrap(finding.snippet, room - 3).map((line) => [
		['▎ ', on(colour, p.RAISED)],
		[line + times(' ', room - 2 - widths.width(line)), on(p.CREAM, p.RAISED)],
	]);
	const needs = finding.preconditions.slice(0, MOST_NEEDS);
	const unlisted = finding.preconditions.length - needs.length;
	if (unlisted > 0)
		needs.push(`and ${unlisted} more in the report`);
	const parts = [
		['What is wrong', finding.description],
		['Impact', finding.impact],
		['How it is exploited', finding.scenario],
		['Preconditions', needs.map(need => '• ' + need).join('\n')],
		['Fix (not verified)', finding.recommendation],
	].filter(([, text]) => text);
	return [
		[
			...look.pill(colour, p.PAPER, widths.fit(finding.severity, 8)),
			['  ' + widths.fit(finding.id, 6), STRONG],
			[finding.confidence && `  ${widths.fit(finding.confidence, 12)} confidence`, DIM],
		],
		[],
		...prose(canvas, finding.title, STRONG, room),
		...prose(canvas, words.listed([placed(finding.file, finding.line), finding.symbol], ' · '), PLACE, room),
		...prose(canvas, words.listed([finding.cwe, finding.category], ' · '), DIM, room),
		...(code.length ? [[], ...code] : []),
		...parts.flatMap(([name, text]) => [[], [[name, DIM + BOLD]], ...prose(canvas, text, SOFT, room)]),
	];
}
export function outcome(canvas, scan, room) {
	const { state, message, reportDir, files } = scan.result;
	const clean = state === 'done' && !message && scan.findings.length === 0;
	const closing = prose(canvas, clean ? 'The panel confirmed no finding.' : message, SOFT, room);
	const written = files.map((name) => [[ELBOW], name, DIM]);
	return [
		...closing,
		...(closing.length && reportDir ? [[]] : []),
		...prose(canvas, reportDir, PLACE, room),
		...table(canvas, written, 5, room),
	];
}
export const result = (canvas, scan, room) => new Pane(RESULT, look.BOOK, [], outcome(canvas, scan, room));
