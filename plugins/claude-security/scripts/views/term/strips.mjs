import { BOLD, ink, Rect } from './canvas.mjs';
import * as look from './look.mjs';
import { DIM, ELBOW, FAINT, FAULT, LIVE, PLACE, SOFT, STRONG } from './look.mjs';
import { clamp, div, round, sum, tenths, whole } from './numbers.mjs';
import { beatOf, Motion } from './pace.mjs';
import * as p from './palette.mjs';
import { braille } from './raster.mjs';
import { SEVERITIES, STAGES } from './scan.mjs';
import { first, spelled, times } from './text.mjs';
import { clock, count, noun, short } from './words.mjs';
const VERBS = {
	Setup: ['Getting ready', 'Sizing the scan'],
	Inventory: ['Surveying the code', 'Drawing the borders'],
	Sweep: ['Sweeping the gaps', 'Looking where nobody looks'],
	Research: ['Tracing input to sink', 'Reading closely', 'Following the data', 'Trying every door'],
	Panel: ['Cross-examining', 'Trying to prove each one wrong', 'Weighing the evidence'],
	Report: ['Writing it up', 'Checking the report'],
};
const SHORT_COMMIT = 7;
const SECONDS_PER_BAR = 3;
const VERB_SECONDS = 9;
const LEFT_LEVELS = [0x00, 0x40, 0x44, 0x46, 0x47];
const RIGHT_LEVELS = [0x00, 0x80, 0xa0, 0xb0, 0xb8];
const SEPARATOR = [' · ', FAINT];
export function header(canvas, area, scan) {
	const { target } = scan;
	const right = [
		...(target.sandboxed
			? look.pill(p.mix(p.PAPER, p.GREEN, 0.2), p.GREEN, look.SANDBOXED, 'Sandboxed')
			: look.pill(p.AMBER, p.PAPER, look.OPEN, 'Not sandboxed')),
		[area.w > 50 ? '  ' : ' ', DIM],
		[look.CLOCK, FAINT],
		[clock(scan.now), STRONG],
	];
	const end = area.end - canvas.measure(right);
	canvas.spans(end, area.y, right, area.end);
	const left = [
		['✻ ', LIVE + BOLD],
		[area.w > 70 ? 'Claude Security plugin  ' : '', STRONG],
		[canvas.widths.fit(target.name, 32), PLACE],
	];
	const x = canvas.spans(area.x, area.y, left, end - 1);
	const revision = [];
	if (target.branch) {
		revision.push([look.BRANCH, FAINT], [canvas.widths.fit(target.branch, 28), DIM]);
		if (target.commit)
			revision.push([look.COMMIT, FAINT]);
	}
	revision.push([first(target.commit, SHORT_COMMIT) + (target.dirty ? ' (edited)' : ''), DIM]);
	const facts = [target.mode, target.effort, target.model].map((fact) => [[fact, DIM]]);
	const shown = [revision, ...facts].filter(fact => canvas.measure(fact) > 0).map(fact => [SEPARATOR, ...fact]);
	canvas.whole(x, area.y, end - 1, shown);
}
export function rail(canvas, area, scan, beat) {
	const { latest } = scan;
	const stop = (phase, detail) => {
		const took = clock(scan.took(phase));
		if (phase.state === 'running' && (detail > 0 || phase === latest)) {
			return look.pill(p.mix(p.PAPER, p.CLAY, 0.22), p.SHIMMER, `${look.spinner(beat, 0)} ${phase.stage} ${took}`);
		}
		const line = [look.state(phase.state, beat, 0)];
		if (detail > 0 || (phase === latest && !scan.running)) {
			line.push([' ' + phase.stage, phase.state === 'done' ? SOFT : FAINT]);
		}
		if (detail > 1 && phase.started !== undefined)
			line.push([' ' + took, FAINT]);
		return line;
	};
	const links = STAGES.length - 1;
	const plans = [2, 1, 0].map(detail => {
		const stops = scan.phases.map(phase => stop(phase, detail));
		return { stops, spare: area.w - sum(stops.map(line => canvas.measure(line))) };
	});
	const { stops, spare } = plans.find(plan => plan.spare >= links) ?? { stops: [stop(latest, 0)], spare: 0 };
	let x = area.x;
	stops.forEach((line, n) => {
		x = canvas.spans(x, area.y, line, area.end);
		if (n === links)
			return;
		const gap = div((n + 1) * spare, links) - div(n * spare, links);
		const link = spare >= 3 * links ? ` ${times('─', gap - 2)} ` : times(' ', gap);
		const { state } = scan.phases[n];
		const passed = state === 'done' || state === 'skipped';
		x = canvas.put(x, area.y, link, passed ? FAINT : ink(p.LIFTED));
	});
}
export class Pulse {
	seconds = new Map();
	rev = 0;
	follow(scan) {
		if (this.rev === scan.rev)
			return;
		for (const touch of scan.touches) {
			const second = whole(touch.at);
			if (touch.rev > this.rev)
				this.seconds.set(second, (this.seconds.get(second) ?? 0) + 1);
		}
		this.rev = scan.rev;
	}
	bars(scan, size) {
		const step = scan.running ? SECONDS_PER_BAR : Math.max(scan.now / size, 1);
		const recent = Math.trunc(scan.now / step) + 1 - size;
		const start = scan.running ? recent : Math.min(recent, 0);
		const bars = new Uint32Array(size);
		for (const [second, touches] of this.seconds) {
			const at = Math.trunc(second / step) - start;
			if (at >= 0)
				bars[Math.min(at, size - 1)] += touches;
		}
		return bars;
	}
	draw(canvas, area, scan) {
		const bars = this.bars(scan, 2 * area.w);
		const top = Math.max(...bars, 8);
		for (let x = 0; x < area.w; x++) {
			const fresh = tenths(((x + 1) / area.w) ** 1.5);
			const pen = ink(p.mix(p.HAIRLINE, p.CLAY, scan.running ? fresh : 0.6));
			for (const row of [0, 1]) {
				const level = (bar) => clamp(round((8 * bar) / top) - 4 * (1 - row), row, 4);
				const dots = LEFT_LEVELS[level(bars[2 * x])] | RIGHT_LEVELS[level(bars[2 * x + 1])];
				canvas.put(area.x + x, area.y + row, spelled(braille(dots)), pen);
			}
		}
	}
}
function counted(scan) {
	const { totals } = scan;
	const of = (part, all) => [
		[count(part), STRONG],
		['/' + count(all), FAINT],
	];
	const plain = (value, many) => [[[count(value), STRONG]], noun(value, many)];
	const shade = (value, colour) => [[count(value), ink(value > 0 ? colour : p.SLATE) + BOLD]];
	return [
		[
			[of(totals.filesRead, totals.files), 'files read'],
			[of(totals.linesRead, totals.lines), 'lines read'],
			plain(totals.agents, 'agents'),
			plain(totals.tools, 'tool calls'),
			plain(totals.tokens, 'tokens'),
		],
		[
			[shade(totals.leads, p.AMBER), noun(totals.leads, 'leads')],
			[shade(totals.candidates, p.IVORY), noun(totals.candidates, 'candidates')],
			[shade(totals.confirmed, p.CLAY), 'confirmed'],
			[shade(totals.refuted, p.ASH), 'refuted'],
		],
	];
}
export function funnel(canvas, area, side, scan, pulse) {
	const [work, proof] = counted(scan);
	const letters = sum(proof.map(([, name]) => name.length));
	const gap = Math.max(div(side - letters, 3), 3);
	const end = area.end - Math.max(side, letters + 9);
	let x = end;
	proof.forEach(([number, name], n) => {
		const link = times(' ', div(gap - 1, 2)) + '→→· '[n] + times(' ', div(gap, 2));
		const label = [
			[name, DIM],
			[link, FAINT],
		];
		canvas.spans(x, area.y, number, area.end);
		x = canvas.spans(x, area.y + 1, label, area.end);
	});
	x = area.x;
	for (const [number, name] of work) {
		const room = Math.max(canvas.measure(number), name.length) + 3;
		if (x + room > end)
			return;
		canvas.spans(x, area.y, number, end);
		canvas.put(x, area.y + 1, name, DIM);
		x += room;
	}
	if (end - x > 8)
		pulse.draw(canvas, new Rect(x + 1, area.y, end - x - 4, area.h), scan);
}
export function counts(canvas, area, scan) {
	const [work, proof] = counted(scan);
	const one = scan.candidates.length ? [...proof.slice(1), work[0]] : [work[0], proof[0], ...work.slice(2)];
	const rows = area.h === 1 ? [one] : [work, proof];
	rows.forEach((row, n) => {
		const parts = row.map(([number, name]) => [...number, [' ' + name, DIM]]);
		canvas.whole(area.x, area.y + n, area.end, parts, [['  ', DIM]]);
	});
}
function working(canvas, area, scan, frame) {
	const verbs = VERBS[scan.latest.stage];
	const verb = Array.from(canvas.widths.fit(verbs[whole(frame.now / VERB_SECONDS) % verbs.length] + '…', area.w - 2));
	const shine = frame.motion === Motion.Full ? ((frame.now * 14) % (verb.length + 24)) - 4 : -9;
	const lit = (n) => Math.max(1 - round(Math.abs(n - shine)) / 4, 0);
	const letters = verb.map((letter, n) => [letter, ink(p.mix(p.CLAY, p.PEACH, lit(n)))]);
	return canvas.spans(area.x, area.y, [[look.spinner(beatOf(frame), 0) + ' ', LIVE], ...letters], area.end);
}
export function status(canvas, area, scan, frame) {
	const { widths } = canvas;
	const narrow = area.w < 72;
	const x = scan.running
		? working(canvas, area, scan, frame)
		: canvas.whole(area.x, area.y, area.end, ending(canvas, scan, narrow), [narrow ? [' ', DIM] : SEPARATOR]);
	const note = scan.running ? (scan.notes.at(-1)?.text ?? '') : scan.result.reportDir || scan.result.message;
	if (area.h > 1 && note) {
		canvas.spans(area.x, area.y + 1, [ELBOW, [widths.fit(note, area.w - 5), DIM]], area.end);
	}
	else if (area.h === 1 && area.end - x > 16) {
		const room = area.end - x - 2;
		canvas.put(x + 2, area.y, note === scan.result.reportDir ? widths.fitEnd(note, room) : widths.fit(note, room), DIM);
	}
}
function headline(state, narrow) {
	if (state === 'done')
		return [narrow ? '✻ Done' : '✻ Scan complete', LIVE + BOLD];
	return state === 'skipped' ? ['✻ Nothing to scan', LIVE + BOLD] : ['✕ Scan not complete', FAULT + BOLD];
}
export function ending(canvas, scan, narrow) {
	const { state, verification } = scan.result;
	const parts = SEVERITIES.flatMap((level) => {
		const found = scan.findings.filter(finding => finding.severity === level).length;
		return found ? [[`${found} ${(narrow ? short(level) : level).toLowerCase()}`, ink(p.severity(level))]] : [];
	});
	if (state === 'done' && scan.findings.length === 0)
		parts.push(['no findings', SOFT]);
	const verified = verification ? [[canvas.widths.fit(verification, 24), SOFT]] : [];
	const facts = narrow ? [...parts, ...verified] : [...verified, ...parts];
	return [headline(state, narrow), ...facts].map(part => [part]);
}
