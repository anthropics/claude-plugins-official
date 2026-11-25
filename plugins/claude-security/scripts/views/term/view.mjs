import { BOLD, Canvas, Grid, ink, Rect } from './canvas.mjs';
import { CodeMap } from './codemap.mjs';
import { DIM, FAINT, LINK, LIVE, SOFT, spinner, STRONG } from './look.mjs';
import { clamp, div, sum } from './numbers.mjs';
import { beatOf, Motion } from './pace.mjs';
import { Glyphs } from './paint.mjs';
import * as p from './palette.mjs';
import * as panes from './panes.mjs';
import * as strips from './strips.mjs';
import { times } from './text.mjs';
import { clock } from './words.mjs';
const KEY = SOFT + BOLD;
const KEY_WIDTH = 12;
const LEAST_COLS = 30;
const LEAST_ROWS = 8;
const BARE_COLS = 72;
const FUNNEL_COLS = 72;
const FUNNEL_ROWS = 26;
const TWO_ROW_COUNTS = 30;
const ROOM_FOR_KEYS = 44;
const SIDE_BY_SIDE = 92;
const MAP_OVER_PANE = 14;
const SMALLEST_PANE = 4;
const ROWS_FOR_AIR = [44, 38, 27, 29, 34, 31, 41, 46];
const MAP = 'Map';
const HELP = [
	['↑ ↓  j k', 'Choose a finding, or scroll'],
	['Enter', 'Read the chosen finding'],
	['Tab', 'Show the next panel'],
	['l', 'Show the narration log'],
	['m', 'Show the map in place of the panels'],
	['Esc', 'Go back'],
	['q  Ctrl-C', 'Quit. A running scan asks first'],
];
const listed = (scan) => scan.result.message || scan.findings.length === 0 ? [undefined, ...scan.findings] : scan.findings;
const keyed = (key, does) => [
	[key, KEY],
	[does, FAINT],
];
const mapped = (scan) => scan.plots.length > 0;
function asked(scan, key) {
	if (key.kind === 'enter')
		return scan.running ? 'none' : 'record';
	if (key.kind === 'esc')
		return 'none';
	if (key.kind !== 'letter')
		return undefined;
	switch (key.letter) {
		case 'l':
			return 'log';
		case '?':
			return 'help';
		case 'm':
			return mapped(scan) ? 'map' : undefined;
		default:
			return undefined;
	}
}
export class View {
	url;
	glyphs;
	pulse = new strips.Pulse();
	map;
	sheet = 'none';
	leading = '';
	names = [''];
	chosen = 0;
	led = '';
	running = true;
	scroll = 0;
	held;
	asking = false;
	pageRows = 0;
	mostRunning = 1;
	constructor(url, glyphs) {
		this.url = url;
		this.glyphs = glyphs;
	}
	press(scan, key) {
		const letter = key.kind === 'letter' ? key.letter : '';
		if (this.asking && scan.running) {
			this.asking = false;
			return letter === 'y' || letter === 'Y' || key.kind === 'interrupt';
		}
		if (letter === 'q' || key.kind === 'interrupt') {
			this.asking = true;
			return !scan.running;
		}
		let step = 0;
		switch (key.kind) {
			case 'step':
				step = key.rows;
				break;
			case 'page':
				step = key.pages * this.pageRows;
				break;
			case 'tab':
				this.leading = this.turned(key.forward ? 1 : -1);
				this.sheet = 'none';
				break;
			default: {
				const wanted = asked(scan, key);
				if (!wanted)
					return false;
				if (key.kind === 'esc' && this.sheet === 'none')
					this.leading = '';
				this.sheet = wanted === this.sheet ? 'none' : wanted;
			}
		}
		const choosing = this.choosing(scan);
		if (choosing)
			this.chosen = clamp(this.chosen + step, 0, listed(scan).length - 1);
		if (step === 0 || choosing)
			this.rewind();
		else
			this.scroll += step;
		return false;
	}
	turned(step) {
		const { names } = this;
		return names[(Math.max(names.indexOf(this.leading), 0) + names.length + step) % names.length];
	}
	rewind() {
		this.scroll = 0;
		this.held = undefined;
	}
	end() {
		this.leading = '';
		if (this.sheet === 'help')
			return;
		this.sheet = 'none';
		this.rewind();
	}
	draw(scan, frame) {
		const canvas = new Canvas(new Grid(frame.cols, frame.rows), this.glyphs === Glyphs.Nerd, scan.widths);
		this.chosen = Math.min(this.chosen, listed(scan).length - 1);
		this.pulse.follow(scan);
		if (!scan.running)
			this.asking = false;
		if (this.running && !scan.running)
			this.end();
		this.running = scan.running;
		if (frame.cols < LEAST_COLS || frame.rows < LEAST_ROWS) {
			this.notice(canvas, scan, frame);
		}
		else {
			this.page(canvas, scan, frame);
			this.overlay(canvas, scan, frame);
		}
		return canvas.grid;
	}
	page(canvas, scan, frame) {
		const margin = frame.cols > 100 ? 2 : 1;
		const full = frame.cols - 2 * margin;
		const page = new Rect(margin, 0, frame.motion === Motion.Bare ? Math.min(full, BARE_COLS) : full, frame.rows);
		const [top, overRail, overBody, overCounts, overStatus, note, overKeys, bottom] = ROWS_FOR_AIR.map(least => Number(frame.rows >= least));
		const keys = frame.rows - 1 - bottom;
		strips.header(canvas, page.below(top), scan);
		if ((this.sheet === 'log' || this.sheet === 'record') && overBody === 0) {
			this.body(canvas, scan, page.below(1).high(keys - 1), frame);
		}
		else {
			const wide = page.w >= FUNNEL_COLS && frame.rows >= FUNNEL_ROWS;
			const status = keys - overKeys - note - 1;
			const counts = status - overStatus - (wide || frame.rows >= TWO_ROW_COUNTS ? 2 : 1);
			const body = page.below(top + overRail + overBody + 2);
			strips.rail(canvas, page.below(top + 1 + overRail), scan, beatOf(frame));
			const side = this.body(canvas, scan, body.high(counts - overCounts - body.y), frame);
			if (wide)
				strips.funnel(canvas, page.below(counts), side, scan, this.pulse);
			else
				strips.counts(canvas, page.below(counts).high(status - overStatus - counts), scan);
			strips.status(canvas, page.below(status).high(1 + note), scan, frame);
		}
		this.hints(canvas, scan, page.below(keys), frame.slow);
	}
	choosing(scan) {
		const open = this.sheet === 'none' || this.sheet === 'map';
		return open && ['', panes.FINDINGS, MAP].includes(this.leading) && scan.findings.length > 0;
	}
	record(canvas, scan, room) {
		const finding = listed(scan)[this.chosen];
		return finding ? panes.record(canvas, finding, room) : panes.outcome(canvas, scan, room);
	}
	notice(canvas, scan, frame) {
		const line = scan.running
			? [[`${spinner(beatOf(frame), 0)} ${scan.latest.stage}`, LIVE]]
			: strips.ending(canvas, scan, true)[0];
		canvas.spans(0, 0, [...line, [' ' + clock(scan.now), DIM]], frame.cols);
		if (this.asking)
			canvas.put(0, Math.min(frame.rows - 1, 1), 'Stop the scan? y/n', KEY);
		else
			canvas.put(0, 1, 'The window is too small', FAINT);
	}
	body(canvas, scan, body, frame) {
		this.pageRows = Math.max(body.h - 2, 1);
		if (this.sheet === 'log') {
			this.moved(panes.log(canvas, scan, body.w), canvas, body);
			return 0;
		}
		const reading = this.sheet === 'record';
		const shown = mapped(scan) && frame.motion > Motion.Bare;
		const beside = shown && body.w >= SIDE_BY_SIDE;
		const high = shown && body.h >= MAP_OVER_PANE && !reading ? div(body.h + 1, 2) : 0;
		let chart = body.high(high);
		let side = body.below(high);
		if (beside) {
			const wide = reading ? Math.min(div(body.w, 2), 96) : Math.min(div(body.w * 5, 12) + 4, 74);
			chart = new Rect(body.x, body.y, body.w - wide - 3, body.h);
			side = new Rect(body.end - wide, body.y, wide, body.h);
		}
		this.mostRunning = Math.max(this.mostRunning, scan.totals.running);
		const panels = this.panelsFor(scan, side);
		const names = chart.h === 0 && mapped(scan) ? [...panels, MAP] : panels;
		const turn = Math.max(names.indexOf(this.leading), 0);
		if (turn === 0)
			this.leading = '';
		if (names[turn] !== this.led && !reading && this.sheet !== 'help')
			this.rewind();
		this.led = names[turn];
		this.names = names;
		if (this.sheet === 'map' || (names[turn] === MAP && !reading)) {
			chart = body;
			side = side.high(0);
		}
		if (chart.h > 0 && mapped(scan)) {
			const finding = this.chosen + scan.findings.length - listed(scan).length;
			this.map = CodeMap.renewed(this.map, scan, chart, frame, this.glyphs >= Glyphs.Braille);
			this.map.draw(canvas, chart, scan, frame, finding < 0 ? undefined : finding);
		}
		if (reading) {
			this.scrolled(canvas, side, this.record(canvas, scan, side.w - 2));
		}
		else if (side.h > 0) {
			this.stack(canvas, scan, side, [...panels.slice(turn), ...panels.slice(0, turn)], beatOf(frame));
		}
		return beside && side.h > 0 ? side.w : 0;
	}
	panelsFor(scan, side) {
		const parts = scan.components.length ? [panes.COMPONENTS] : [];
		const names = [];
		if (scan.findings.length)
			names.push(panes.FINDINGS);
		if (!scan.running)
			names.push(panes.RESULT);
		if (scan.candidates.length)
			names.push(panes.PANEL, panes.AGENTS, ...parts);
		else if (!parts.length && !scan.leads.length)
			names.push(panes.AGENTS, panes.LEGEND);
		else if (side.h >= 5 * SMALLEST_PANE)
			names.push(...parts, panes.AGENTS);
		else
			names.push(panes.AGENTS, ...parts);
		return [...names, panes.TARGET, panes.NARRATION];
	}
	pane(name, canvas, scan, side, beat) {
		switch (name) {
			case panes.FINDINGS:
				return panes.findings(canvas, listed(scan), side.w, this.chosen);
			case panes.RESULT:
				return panes.result(canvas, scan, side.w);
			case panes.PANEL:
				return panes.panel(canvas, scan, side.w, beat);
			case panes.AGENTS:
				return panes.agents(canvas, scan, side.w, this.mostRunning, beat);
			case panes.COMPONENTS:
				return panes.components(canvas, scan, side.w, div(side.h, 2), beat);
			case panes.LEGEND:
				return panes.legend(canvas, side.w);
			case panes.TARGET:
				return panes.target(canvas, scan, side.w);
			default:
				return panes.log(canvas, scan, side.w);
		}
	}
	stack(canvas, scan, side, names, beat) {
		const made = [];
		const pane = (n) => (made[n] ??= this.pane(names[n], canvas, scan, side, beat));
		const first = pane(0);
		const reading = names[0] === panes.FINDINGS && side.h >= 5 * SMALLEST_PANE;
		let own = side.h;
		if (reading)
			own -= div(side.h * 2, 3);
		else if (side.h >= 4 * SMALLEST_PANE)
			own -= Math.min(div(side.h, 2), pane(1).height + 1);
		const high = first.height <= Math.min(own + 2, side.h) ? first.height : own;
		if (this.sheet === 'help') {
			first.draw(canvas, side.high(high));
		}
		else {
			this.moved(first, canvas, side.high(high));
			this.pageRows = Math.max(high - 2, 1);
		}
		let left = side.below(high + 1);
		if (reading) {
			const record = this.record(canvas, scan, left.w);
			if (record.length > left.h) {
				record.length = Math.max(left.h - 1, 0);
				record.push(keyed('enter', ' read the rest'));
			}
			canvas.lines(left, record);
			return;
		}
		for (let n = 1; n < names.length && left.h > 1; n++) {
			const rows = Math.min(pane(n).height, left.h);
			if (rows > 1 && rows >= Math.min(pane(n).height, SMALLEST_PANE + 1)) {
				pane(n).draw(canvas, left.high(rows));
				left = left.below(rows + 1);
			}
		}
	}
	moved(pane, canvas, area) {
		this.held = pane.draw(canvas, area, this.scroll, this.held);
		this.scroll = 0;
	}
	scrolled(canvas, area, rows) {
		const hidden = rows.length - area.h;
		this.scroll = Math.max(Math.min(this.scroll, hidden), 0);
		canvas.lines(area, rows.slice(this.scroll));
		if (hidden <= 0)
			return;
		const size = Math.max(div(area.h * area.h, rows.length), 1);
		const top = div(this.scroll * (area.h - size), hidden);
		for (let y = 0; y < area.h; y++) {
			canvas.put(area.end - 1, area.y + y, '│', y >= top && y < top + size ? LIVE : ink(p.LIFTED));
		}
	}
	hints(canvas, scan, area, slow) {
		const roomy = area.w > 50;
		let hints = [];
		const add = (rank, ...line) => hints.push({ rank, line, cells: canvas.measure(line) });
		const hint = (rank, key, does) => add(rank, ...keyed(key, does));
		if (this.choosing(scan))
			hint(3, '↑↓', roomy ? ' choose' : '');
		if (this.sheet === 'none') {
			if (!scan.running)
				hint(2, 'enter', ' read');
			hint(4, 'tab', roomy || scan.running ? ' ' + this.turned(1).replace(/^.* /, '').toLowerCase() : '');
			hint(7, 'l', ' log');
			if (mapped(scan))
				hint(8, 'm', ' map');
		}
		else {
			if (this.sheet !== 'map')
				hint(2, '↑↓', ' scroll');
			hint(0, 'esc', ' back');
		}
		hint(6, '?', ' help');
		hint(1, 'q', scan.running ? ' stop' : ' quit');
		if (slow)
			add(5, ['slow link: less motion', ink(p.AMBER)]);
		const link = [
			[LINK, ink(p.SKY)],
			[this.url, ink(p.SKY)],
		];
		let end = area.end;
		if (this.url && canvas.measure(link) + ROOM_FOR_KEYS < area.w) {
			end -= canvas.measure(link);
			canvas.spans(end, area.y, link, area.end);
		}
		const gap = area.w > 60 ? 3 : 2;
		for (let last = 8; last >= 0; last--) {
			const needed = sum(hints.map(({ cells }) => cells + gap));
			if (needed > end - area.x + gap)
				hints = hints.filter(({ rank }) => rank !== last);
		}
		const shown = hints.map(({ line }) => line);
		canvas.whole(area.x, area.y, end, shown, [[times(' ', gap), FAINT]]);
	}
	help(canvas, scan, room) {
		const labelled = (key, does, pen) => [[[key.padEnd(KEY_WIDTH), KEY]], does, pen];
		const keys = HELP.filter(([key]) => key !== 'm' || mapped(scan)).map(([key, does]) => labelled(key, does, SOFT));
		return [
			...panes.table(canvas, keys, KEY_WIDTH, room),
			[],
			...panes.legend(canvas, room).rows,
			...(this.url ? [[]] : []),
			...panes.table(canvas, [labelled('Link', this.url, ink(p.SKY))], KEY_WIDTH, room),
		];
	}
	overlay(canvas, scan, frame) {
		if (this.sheet !== 'help' && !this.asking)
			return;
		const room = Math.min(frame.cols - 6, 58);
		const rows = this.asking ? question(canvas, room) : this.help(canvas, scan, room);
		if (frame.motion === Motion.Full)
			canvas.fade(0.6);
		const air = Number(rows.length + 4 < frame.rows && frame.cols > room + 12);
		const w = rows.reduce((most, row) => Math.max(most, canvas.measure(row)), 0) + 6 + 4 * air;
		const h = Math.min(rows.length + 2 + 2 * air, frame.rows - 1);
		const area = new Rect(div(frame.cols - w, 2), div(frame.rows - h, 2), w, h);
		canvas.frame(area, LIVE);
		const inside = area.inset(2 + 2 * air, 1 + air);
		if (this.asking)
			canvas.lines(inside, rows);
		else
			this.scrolled(canvas, inside, rows);
	}
}
const question = (canvas, room) => [
	...panes.prose(canvas, 'Stop the scan?', STRONG, room),
	...panes.prose(canvas, 'It has not finished its report.', DIM, room),
	[],
	[...keyed('y', ' stop   '), ...keyed('n', ' go on')],
];
