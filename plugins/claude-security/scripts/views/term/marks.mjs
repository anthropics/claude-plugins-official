import { BOLD, colourOf, Grid, ink, on } from './canvas.mjs';
import { pill, STRONG, VOTE } from './look.mjs';
import { clamp, div, nearest, round, tenths } from './numbers.mjs';
import { Motion } from './pace.mjs';
import * as p from './palette.mjs';
import { braille, DOT } from './raster.mjs';
import { LENSES } from './scan.mjs';
import { SPACE } from './text.mjs';
const PING = 0.9;
const DUST = 2.4;
const LOCK = 0.7;
const ARRIVAL = 0.22;
const SLOT_W = 6;
const SLOT_H = 3;
const ROWS_FOR_RINGS = 18;
const TURNS = Array.from({ length: 96 }, (_, step) => (2 * Math.PI * step) / 96).map(turn => ({
	sin: Math.sin(turn),
	cos: Math.cos(turn),
}));
const circle = (radius) => TURNS.map(({ sin, cos }) => [round(5.5 + radius * sin), round(5.5 - radius * cos)]);
function band(radius, outer) {
	const dots = [...new Map(circle(radius).map(dot => [String(dot), dot])).values()];
	return dots.map(([across, down], n) => ({ across, down, outer, turn: n / dots.length }));
}
const RING = [...band(5.6, true), ...band(4.7, false)];
export class Layer {
	grid;
	over;
	constructor(cols, rows) {
		this.grid = new Grid(cols, rows);
		this.over = new Uint8Array(cols * rows);
	}
	begin(picture) {
		this.grid.text.set(picture.text);
		this.grid.inks.set(picture.inks);
		this.over.fill(0);
	}
	dot(x, y, pen) {
		const { cols, rows, text, inks } = this.grid;
		if (x < 2 || x >= 2 * cols - 2 || y < 4 || y >= 4 * rows - 4)
			return;
		const at = (y >> 2) * cols + (x >> 1);
		this.over[at] |= DOT[y & 3][x & 1];
		text[at] = braille(this.over[at]);
		inks[at] = pen;
	}
	tint(at, colour, share) {
		this.grid.inks[at] = ink(p.mix(colourOf(this.grid.inks[at]), colour, share));
	}
	clear(x, y, wide) {
		const { cols, rows, text, inks } = this.grid;
		for (let row = Math.max(y, 0); row < Math.min(y + SLOT_H, rows); row++) {
			for (let column = Math.max(x, 0); column < Math.min(x + wide, cols); column++) {
				const at = row * cols + column;
				text[at] = SPACE;
				inks[at] = ink(p.PAPER);
				this.over[at] = 0;
			}
		}
	}
	ping(x, y, age, colour) {
		if (!(age >= 0 && age < PING))
			return;
		const pen = ink(p.mix(colour, p.PAPER, tenths(age / PING)));
		for (const [across, down] of circle(3 + 9 * Math.sqrt(age / PING)))
			this.dot(2 * x + across, 4 * y + down, pen);
	}
}
const centred = (x, wide) => x + div(SLOT_W - wide - 1, 2);
export class Marks {
	rings;
	candidateSlots = new Map();
	findingSlots = new Map();
	seen = new Map();
	chosen;
	drawn = false;
	constructor(rows, hasBraille) {
		this.rings = rows >= ROWS_FOR_RINGS && hasBraille;
	}
	draw(layer, moment, chosen) {
		const { findings, candidates } = moment.scan;
		let labels;
		if (findings.length > 0)
			labels = this.findings(layer, moment, chosen);
		else if (candidates.length > 0) {
			labels = apart(candidates.flatMap((one, n) => this.candidate(layer, moment, n, one) ?? []), Number(this.rings));
		}
		else
			labels = this.leads(layer, moment);
		this.drawn = true;
		return labels;
	}
	dusk(moment) {
		return moment.scan.candidates.length === 0 ? 0 : nearest(Math.min(this.age('panel', moment) / 2, 1) * 50) / 100;
	}
	age(event, moment) {
		const since = this.seen.get(event) ?? (this.drawn && moment.motion === Motion.Full ? moment.now : -Infinity);
		this.seen.set(event, since);
		return moment.now - since;
	}
	slot(slots, n, { raster }, plot, line) {
		const kept = slots.get(n);
		if (kept)
			return kept;
		const [x, y] = raster.cell(plot, line);
		const { room } = raster.regions[raster.places[plot].region];
		const left = room.x + 1;
		const right = Math.max(room.end - 2 - SLOT_W, 1);
		const bottom = room.y + room.h - 3 - Number(this.rings);
		const top = Math.min(room.y + Number(this.rings), raster.rows - 1 - SLOT_H);
		const near = [0, 1, -1, 2, -2].flatMap(dy => [0, 3, -3, 7, -7].map((dx) => [clamp(x - 3 + dx, left, right), Math.max(Math.min(y - 1 + dy, bottom), top)]));
		const high = this.rings ? SLOT_H : 1;
		const clear = ([a, b]) => {
			for (const [c, d] of slots.values())
				if (Math.abs(a - c) <= SLOT_W && Math.abs(b - d) < high)
					return false;
			return true;
		};
		const found = near.find(clear) ?? near[0];
		slots.set(n, found);
		return found;
	}
	leads(layer, moment) {
		return moment.scan.leads.flatMap(({ plot, plotLine }, n) => {
			if (plot === undefined)
				return [];
			const [x, y] = moment.raster.cell(plot, plotLine);
			layer.ping(x - 3, y - 1, this.age(`lead ${n}`, moment), p.AMBER);
			const pulse = moment.motion === Motion.Full ? round(2 + 2 * Math.sin(moment.now * 2 + n)) / 8 : 0;
			return [{ x, y, line: [['◆', on(p.mix(p.AMBER, p.IVORY, pulse), p.EMBER) + BOLD]], pill: false }];
		});
	}
	candidate(layer, moment, n, one) {
		if (one.plot === undefined)
			return undefined;
		const [x, y] = this.slot(this.candidateSlots, n, moment, one.plot, one.plotLine);
		const name = moment.scan.widths.fit(one.id, 4);
		const wide = moment.scan.widths.width(name);
		const event = `settled ${n}`;
		let age = 0;
		if (one.settled === undefined)
			this.seen.delete(event);
		else
			age = this.age(event, moment);
		const start = centred(x, wide);
		if (one.outcome === 'refuted') {
			dust(layer, x, y, age / DUST);
			const pen = ink(p.mix(p.STONE, p.PAPER, tenths(Math.min((2 * age) / DUST, 1))));
			return age < DUST / 2 ? { x: start + 1, y: y + 1, line: [[name, pen]], pill: false } : undefined;
		}
		if (age > LOCK) {
			layer.ping(x, y, age - LOCK, p.CLAY);
			const line = one.outcome === 'confirmed' ? pill(p.CLAY, p.PAPER, name) : pill(p.LIFTED, p.AMBER, name);
			return { x: start, y: y + 1, line, pill: true };
		}
		const busy = LENSES.map(lens => moment.scan.verifier(one.id, lens) !== undefined);
		if (!busy.includes(true) && one.votes.every(vote => vote === 'pending')) {
			return { x: start, y: y + 1, line: pill(p.LIFTED, p.STONE, name), pill: true };
		}
		if (!this.rings) {
			const pips = one.votes.map((vote, arc) => [
				vote === 'pending' ? '·' : VOTE[vote],
				on(p.LENS[arc], p.LIFTED),
			]);
			return { x, y: y + 1, line: [[name, on(p.IVORY, p.LIFTED) + BOLD], ...pips], pill: false };
		}
		const odd = wide % 2;
		const spin = moment.motion === Motion.Full ? moment.now : 0;
		layer.clear(x, y, SLOT_W + odd);
		RING.forEach(({ across, down, outer, turn }, step) => {
			const upper = across + odd > 5 ? 0 : 2;
			const arc = down > 7 ? 1 : upper;
			const vote = one.votes[arc];
			const behind = (3 * turn - spin) % 1;
			const comet = (behind < 0 ? behind + 1 : behind) > 0.6;
			let colour;
			if (vote === 'confirm')
				colour = p.LENS[arc];
			else if (vote !== 'pending')
				colour = outer && step % 3 === 0 ? p.ASH : undefined;
			else if (busy[arc])
				colour = outer || comet ? p.mix(p.LENS[arc], p.PAPER, 0.3) : undefined;
			else
				colour = outer ? p.HAIRLINE : undefined;
			if (colour !== undefined)
				layer.dot(2 * x + across + odd, 4 * y + down, ink(colour));
		});
		return { x: start + 1, y: y + 1, line: [[name, STRONG]], pill: false };
	}
	findings(layer, moment, chosen) {
		const age = this.age('findings', moment);
		if (chosen !== this.chosen)
			this.seen.delete('chosen');
		this.chosen = chosen;
		return moment.scan.findings.flatMap(({ id, plot, plotLine, severity }, n) => {
			const since = age - 0.5 - n * ARRIVAL;
			if (plot === undefined || since < 0)
				return [];
			const colour = p.severity(severity);
			const pen = ink(p.mix(colour, p.PAPER, chosen === n ? 0 : 0.3));
			for (const stroke of moment.raster.places[plot].strokes)
				layer.grid.inks[stroke.cell] = pen;
			const [x, y] = this.slot(this.findingSlots, n, moment, plot, plotLine);
			layer.ping(x, y, since, colour);
			if (chosen === n) {
				const reach = 10 + this.age('chosen', moment) * 500;
				this.sight(layer, x, y, moment.motion > Motion.Still ? reach : 0, colour);
			}
			const name = moment.scan.widths.fit(id, 4);
			const start = centred(x, moment.scan.widths.width(name));
			return [{ x: start, y: y + 1, line: pill(colour, p.PAPER, name), pill: true }];
		});
	}
	sight(layer, x, y, reach, colour) {
		const pen = ink(p.mix(colour, p.PAPER, 0.35));
		const across = 2 * x + 6;
		const down = 4 * y + 6;
		for (let far = 10; far < Math.min(Math.trunc(reach), 2 * layer.grid.cols); far += 2) {
			layer.dot(across + far, down, pen);
			layer.dot(across - far, down, pen);
			layer.dot(across, down + far, pen);
			layer.dot(across, down - far, pen);
		}
		if (!this.rings)
			return;
		layer.clear(x, y, SLOT_W);
		for (const dot of RING)
			layer.dot(2 * x + dot.across, 4 * y + dot.down, ink(colour));
	}
}
function dust(layer, x, y, share) {
	const pen = ink(p.mix(p.STONE, p.LIFTED, tenths(Math.min(share, 1))));
	RING.forEach(({ across, down }, n) => {
		const chance = (n * 0.618) % 1;
		if (chance > share * 1.1) {
			const sideways = round((across - 5.5) * share * chance);
			const fall = round((down - 2) * share * chance + 9 * share * share);
			layer.dot(2 * x + across + sideways, 4 * y + down + fall, pen);
		}
	});
}
function apart(labels, rows) {
	const kept = [];
	for (const label of labels.sort((a, b) => Number(a.pill) - Number(b.pill))) {
		const touches = (other) => {
			const across = Math.abs(label.x - other.x);
			const down = Math.abs(label.y - other.y);
			return (down === 0 && across < 4) || (!other.pill && across < SLOT_W - 1 && down <= rows);
		};
		if (!kept.some(touches))
			kept.push(label);
	}
	return kept;
}
