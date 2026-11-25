import { BOLD, colourOf, Grid, ink, ITALIC, on, RULE_CELL } from './canvas.mjs';
import { LIVE, RULE } from './look.mjs';
import { Layer, Marks } from './marks.mjs';
import { clamp, div, nearest, partition, round, sum, whole } from './numbers.mjs';
import { Motion } from './pace.mjs';
import * as p from './palette.mjs';
import { between, braille, dotOf, folders, Raster } from './raster.mjs';
import { cell, SPACE } from './text.mjs';
const SWEEP = 1;
const COOL = 5;
const RIPPLE = 1.1;
const FLIGHT = 0.7;
const REVEAL = 1.3;
const GLIDE = 1.8;
const STALE = 10;
const STEPS = 14;
const LONG_AGO = -Infinity;
const UNREAD = [0x3a3b3d, 0x434446, 0x4b4c4d];
const READ = [0x9c9a91, 0xb8b5aa, 0xd6d0c3];
const BAND = [0.1, 0.2, 0.3, 0.2, 0.1];
const RIPPLES = 6;
const REGIONS = 16;
const LEFT_OVER = 4;
const CORNERS = Array.from('╭╮╰╯', cell);
const UPRIGHT = cell('│');
const distance = (across, down) => Math.sqrt(across * across + down * down);
function along({ start: [x0, y0], end: [x1, y1], length }, share) {
	const lift = (Math.sin(share * Math.PI) * length) / 7;
	return [round(x0 + (x1 - x0) * share), round(y0 + (y1 - y0) * share - lift)];
}
function glow(base, heat) {
	let colour;
	if (heat > 0.85)
		colour = p.mix(p.SHIMMER, p.IVORY, (heat - 0.85) / 0.15);
	else if (heat > 0.55)
		colour = p.mix(p.CLAY, p.SHIMMER, (heat - 0.55) / 0.3);
	else
		colour = p.mix(base, p.CLAY, heat / 0.55);
	return on(colour, p.mix(p.PAPER, p.EMBER, heat));
}
const front = (age, map) => (age / REVEAL) * (map.cols + 2 * map.rows);
function groups(scan) {
	const seen = new Set();
	const found = [];
	for (const { name, plots } of scan.components) {
		const fresh = [...new Set(plots)].filter(plot => !seen.has(plot));
		fresh.forEach(plot => seen.add(plot));
		if (fresh.length > 0)
			found.push({ name, plots: fresh, scanned: true });
	}
	const rest = [...scan.plots.keys()].filter(plot => !seen.has(plot));
	return found.concat(folders(scan.plots, rest, Math.max(REGIONS - scan.components.length, LEFT_OVER)));
}
const inOrder = (a, b) => a.line < b.line || (a.line === b.line && a.cell <= b.cell);
class Film {
	map;
	grid;
	dots;
	lit;
	lastPlot;
	read = new Set();
	constructor(scan, map) {
		this.map = map;
		const size = map.masks.length;
		this.grid = new Grid(map.cols, map.rows);
		this.dots = new Uint32Array(size);
		this.lit = new Uint32Array(size);
		this.lastPlot = new Uint32Array(size);
		for (const plot of map.order) {
			for (const stroke of map.places[plot].strokes) {
				this.dots[stroke.cell] += stroke.dots;
				this.lastPlot[stroke.cell] = plot;
			}
		}
		map.masks.forEach((mask, at) => {
			this.grid.text[at] = mask > 0 ? braille(mask) : SPACE;
			this.grid.inks[at] = this.base(scan, at);
		});
		scan.visits.forEach((_, plot) => {
			this.develop(scan, plot, []);
		});
	}
	base(scan, at) {
		const plot = this.lastPlot[at];
		const reads = clamp(scan.visits[plot]?.reads ?? 1, 1, 3);
		const share = round((4 * this.lit[at]) / Math.max(this.dots[at], 1));
		return ink(p.mix(UNREAD[plot % 3], READ[reads - 1], share / 4));
	}
	light(scan, plot, stroke) {
		if (!this.read.has(stroke)) {
			this.read.add(stroke);
			this.lit[stroke.cell] += stroke.dots;
		}
		this.lastPlot[stroke.cell] = plot;
		this.grid.inks[stroke.cell] = this.base(scan, stroke.cell);
	}
	develop(scan, plot, sweeps) {
		const ahead = sweeps.filter(sweep => sweep.plot === plot && sweep.passed < sweep.strokes.length);
		const waits = (stroke) => ahead.some(({ strokes, passed }) => inOrder(strokes[passed], stroke) && inOrder(stroke, strokes[strokes.length - 1]));
		for (const [from, to] of scan.visits[plot]?.spans ?? []) {
			for (const stroke of between(this.map.places[plot].strokes, from, to)) {
				if (!waits(stroke))
					this.light(scan, plot, stroke);
			}
		}
	}
}
export class CodeMap {
	map;
	from;
	marks;
	film;
	layer;
	alike;
	named;
	divisions;
	parts;
	revealedAt;
	settledAt;
	rev;
	sweeps = [];
	ripples = [];
	flights = new Map();
	hot = new Map();
	static renewed(earlier, scan, area, frame, hasBraille) {
		const fits = earlier?.map.cols === area.w && earlier.map.rows === area.h && earlier.divisions === scan.divisions;
		return fits ? earlier : new CodeMap(earlier, scan, area, frame, hasBraille);
	}
	constructor(earlier, scan, area, frame, hasBraille) {
		const full = frame.motion === Motion.Full;
		this.map = new Raster(scan.plots, groups(scan), area.w, area.h);
		this.film = new Film(scan, this.map);
		this.layer = new Layer(area.w, area.h);
		this.marks = new Marks(area.h, hasBraille);
		const starts = this.map.regions.map(({ name, room }) => scan.widths.fit(name, room.w - 3));
		this.alike = starts.map(start => starts.indexOf(start) !== starts.lastIndexOf(start));
		this.named = [...scan.plots.keys()].filter(plot => this.map.places[plot].name);
		this.divisions = scan.divisions;
		this.parts = scan.components.length;
		this.rev = scan.rev;
		this.from = full && earlier?.parts !== this.parts ? earlier?.map : undefined;
		this.revealedAt = full && !earlier ? frame.now : LONG_AGO;
		this.settledAt = this.from ? frame.now + GLIDE : this.revealedAt;
		for (const touch of scan.touches)
			this.fly(touch, LONG_AGO);
	}
	draw(canvas, area, scan, { now, motion }, chosen) {
		const { layer } = this;
		const moment = { scan, raster: this.map, now, motion };
		this.follow(moment);
		this.advance(moment);
		layer.begin(this.film.grid);
		if (now >= this.settledAt)
			this.from = undefined;
		if (this.from)
			this.glide(this.from, moment);
		else {
			const dusk = this.marks.dusk(moment);
			if (dusk > 0)
				layer.grid.recolour(pen => ink(p.mix(colourOf(pen), p.PAPER, dusk)));
			this.lights(moment);
			this.trails(moment);
		}
		this.borders(now);
		const labels = this.from ? [] : this.marks.draw(layer, moment, chosen);
		const wave = front(now - this.revealedAt, this.map);
		for (let y = 0; y < area.h; y++) {
			const shown = round(clamp(wave - 2 * y, 0, area.w));
			canvas.grid.take(layer.grid, y * area.w, (area.y + y) * canvas.grid.cols + area.x, shown);
		}
		if (!this.from)
			this.agents(canvas, area, moment);
		this.names(canvas, area, moment);
		for (const label of labels)
			canvas.spans(area.x + label.x, area.y + label.y, label.line, area.end - 1);
	}
	follow({ scan, now, motion }) {
		const seen = this.rev;
		if (seen === scan.rev)
			return;
		this.rev = scan.rev;
		for (const touch of scan.touches) {
			if (touch.rev <= seen)
				continue;
			const moves = scan.now - touch.at > STALE ? Motion.Still : motion;
			this.fly(touch, moves === Motion.Full ? now : LONG_AGO);
			if (touch.file === undefined) {
				if (moves === Motion.Full && this.ripples.length < RIPPLES)
					this.ripples.push(this.ripple(touch, now));
				continue;
			}
			const strokes = between(this.map.places[touch.file].strokes, touch.first, touch.last);
			if (moves === Motion.Full)
				this.sweeps.push({ born: now + FLIGHT / 2, plot: touch.file, strokes, passed: 0 });
			else if (moves === Motion.Reduced)
				for (const stroke of strokes)
					this.hot.set(stroke.cell, now);
		}
		scan.visits.forEach((visit, plot) => {
			if (visit && visit.rev > seen)
				this.film.develop(scan, plot, this.sweeps);
		});
	}
	advance({ scan, now }) {
		for (const sweep of this.sweeps) {
			const reached = Math.ceil(sweep.strokes.length * clamp((now - sweep.born) / SWEEP, 0, 1));
			for (; sweep.passed < reached; sweep.passed++) {
				const stroke = sweep.strokes[sweep.passed];
				this.hot.set(stroke.cell, now);
				this.film.light(scan, sweep.plot, stroke);
			}
		}
		this.sweeps = this.sweeps.filter(sweep => sweep.passed < sweep.strokes.length);
		for (const [at, lit] of this.hot)
			if (now - lit >= COOL)
				this.hot.delete(at);
		this.ripples = this.ripples.filter(ripple => now - ripple.born < RIPPLE);
	}
	fly(touch, born) {
		if (touch.file === undefined)
			return;
		const end = dotOf(this.map.places[touch.file], touch.first);
		const start = this.flights.get(touch.agent)?.end ?? end;
		this.flights.set(touch.agent, { born, start, end, length: distance(end[0] - start[0], end[1] - start[1]) });
	}
	ripple(touch, born) {
		const { cols, places } = this.map;
		const strokes = places.slice(touch.start, touch.end).flatMap(place => place.strokes);
		const found = [...new Set(strokes.map(stroke => stroke.cell))];
		const x = sum(found.map(at => at % cols)) / found.length;
		const y = sum(found.map(at => div(at, cols))) / found.length;
		const near = found.map(at => ({ reach: distance((at % cols) - x, 2 * (div(at, cols) - y)), at }));
		return { born, near: near.sort((a, b) => a.reach - b.reach) };
	}
	glide(earlier, { scan, now }) {
		this.layer.grid.text.fill(SPACE);
		for (const plot of this.map.order) {
			const place = this.map.places[plot];
			const late = (0.5 * place.region) / this.map.regions.length;
			const share = clamp(1.5 * (1 - (this.settledAt - now) / GLIDE) - late, 0, 1);
			const left = (1 + Math.cos(share * Math.PI)) / 2;
			const [x0, y0] = dotOf(earlier.places[plot], 1);
			const [x1, y1] = dotOf(place, 1);
			const across = round((x0 - x1) * left);
			const down = round((y0 - y1) * left);
			const still = scan.visits[plot] ? READ[0] : UNREAD[plot % 3];
			const pen = ink(p.mix(still, p.CLAY, round(3 * Math.sin(share * Math.PI)) / 6));
			for (const run of place.runs) {
				for (let x = run.start; x < run.end; x++)
					this.layer.dot(x + across, run.y + down, pen);
			}
		}
	}
	lights({ scan, now, motion }) {
		const { cols, rows } = this.map;
		const { inks } = this.layer.grid;
		const full = motion === Motion.Full;
		const idle = !scan.agents.some(agent => agent.plot !== undefined && agent.ended === undefined);
		if (full && idle && scan.running) {
			const head = whole(now * 16) % (cols + 2 * rows + 30);
			for (let y = 0; y < rows; y++) {
				for (let behind = 0; behind < 2 * BAND.length; behind++) {
					const x = head - 2 * y - behind;
					if (x >= 0 && x < cols)
						this.layer.tint(y * cols + x, p.PEACH, BAND[behind >> 1]);
				}
			}
		}
		for (const { born, near } of this.ripples) {
			const far = near.at(-1)?.reach ?? 0;
			const band = Math.max(far / 3, 3);
			const wave = ((now - born) / RIPPLE) * (far + band);
			const inner = partition(near, ({ reach }) => reach <= wave - band);
			for (let n = inner; n < near.length && near[n].reach <= wave; n++) {
				this.layer.tint(near[n].at, p.SKY, round(6 * (1 - (wave - near[n].reach) / band)) / 8);
			}
		}
		this.hot.forEach((lit, at) => {
			inks[at] = full ? glow(colourOf(inks[at]), nearest(STEPS * (1 - (now - lit) / COOL) ** 1.6) / STEPS) : LIVE;
		});
	}
	trails({ scan, now }) {
		const flying = [...this.flights].filter(([, flight]) => (now - flight.born) / FLIGHT < 1.6);
		for (const [id, flight] of flying.sort(([a], [b]) => a - b)) {
			const age = (now - flight.born) / FLIGHT;
			const steps = nearest(flight.length);
			const colour = p.lens(scan.agents.find(agent => agent.id === id)?.lens ?? '') ?? p.SHIMMER;
			for (let step = whole((age - 0.6) * steps); step < whole(Math.min(age * steps, steps)); step++) {
				const share = step / steps;
				const [x, y] = along(flight, share);
				this.layer.dot(x, y, ink(p.mix(colour, p.EMBER, Math.min(round(10 * (age - share)) / 6, 1))));
			}
		}
	}
	borders(now) {
		const { cols, rows } = this.map;
		const { text, inks } = this.layer.grid;
		const wave = front(now - this.settledAt, this.map);
		for (const { at, glyph } of this.map.borders) {
			const x = at % cols;
			const y = div(at, cols);
			const behind = wave - (x + 2 * y);
			const side = x === 0 || x === cols - 1;
			if (behind <= 0 && !side && y !== 0 && y !== rows - 1)
				continue;
			if (behind > 0 || CORNERS.includes(glyph))
				text[at] = glyph;
			else
				text[at] = side ? UPRIGHT : RULE_CELL;
			inks[at] = behind > 0 && behind < 8 ? LIVE : RULE;
		}
	}
	names(canvas, area, { scan, now }) {
		const { widths } = canvas;
		const { places, regions } = this.map;
		const wave = front(now - this.settledAt, this.map);
		const atWork = scan.atWork().flatMap(agent => agent.plot ?? []);
		regions.forEach(({ name, scanned, room }, n) => {
			if (!(name && room.w > 6 && wave > room.x + 2 * room.y + 8))
				return;
			const busy = atWork.some(plot => places[plot].region === n);
			const edge = room.w > widths.width(name) + 5 ? 2 : 1;
			const most = room.w - 2 - edge;
			const fitted = this.alike[n] ? widths.fitEnd(name, most) : widths.fit(name, most);
			const calm = scanned ? p.STONE : p.SLATE;
			canvas.put(area.x + room.x + edge, area.y + room.y, ` ${fitted} `, ink(busy ? p.SHIMMER : calm));
		});
		for (const plot of this.named) {
			const label = places[plot].name;
			if (!(label && wave > label.x + 2 * label.y))
				continue;
			const { path } = scan.plots[plot];
			const name = widths.fit(path.slice(path.lastIndexOf('/') + 1), label.w);
			canvas.put(area.x + label.x, area.y + label.y, name, ink(atWork.includes(plot) ? p.PEACH : p.SLATE) + ITALIC);
		}
	}
	agents(canvas, area, { scan, now }) {
		for (const agent of scan.atWork()) {
			const flight = this.flights.get(agent.id);
			if (!flight)
				continue;
			const [x, y] = along(flight, Math.min((now - flight.born) / FLIGHT, 1));
			const pen = on(p.lens(agent.lens) ?? p.IVORY, p.EMBER) + BOLD;
			canvas.put(area.x + clamp(div(x, 2), 1, area.w - 2), area.y + clamp(div(y, 4), 1, area.h - 2), '✻', pen);
		}
	}
}
