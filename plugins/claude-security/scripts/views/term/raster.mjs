import { divide, layout } from './atlas.mjs';
import { Rect } from './canvas.mjs';
import { clamp, div, partition, round, sum, whole } from './numbers.mjs';
import { cell } from './text.mjs';
export const DOT = [
	[0x01, 0x08],
	[0x02, 0x10],
	[0x04, 0x20],
	[0x40, 0x80],
];
const UP = 1;
const DOWN = 2;
const LEFT = 4;
const RIGHT = 8;
const LINES = Array.from(' │││─╯╮┤─╰╭├─┴┬┼', cell);
const CELLS_PER_REGION = 36;
const COLUMN_DOTS = 22;
const DOTS_FOR_A_NAME = 17;
const SHORTEST_LINE = 24;
const LONGEST_LINE = 96;
const TALLEST_LINE = 3;
const FOLDER_LEVELS = 5;
const PICKED_FIFTH = 3;
const WIDEST_FIFTH = 4;
const rowsByLength = new Uint32Array(256);
export const braille = (mask) => 0x2800 + mask;
export function dotOf({ dots, columns, lines }, line) {
	const high = Math.max(dots.h, 1);
	const slots = Math.max(dots.h * columns, 1);
	const slot = Math.min(whole(((Math.max(line, 1) - 1) * slots) / Math.max(lines, 1)), slots - 1);
	return [dots.x + div((2 * div(slot, high) + 1) * dots.w, 2 * columns), dots.y + (slot % high)];
}
export function between(strokes, first, last) {
	const start = partition(strokes, stroke => stroke.line < first);
	const end = partition(strokes, stroke => stroke.line <= last);
	const before = Math.max(start - 1, 0);
	return start < end ? strokes.slice(start, end) : strokes.slice(before, before + 1);
}
function byFolder(plots, chosen, depth) {
	const groups = new Map();
	for (const plot of chosen) {
		const name = plots[plot].path
			.split('/', depth + 1)
			.slice(0, -1)
			.join('/');
		const group = groups.get(name) ?? { name, plots: [], scanned: false };
		groups.set(name, group);
		group.plots.push(plot);
	}
	return [...groups.values()];
}
export function folders(plots, chosen, most) {
	let fitting = [];
	for (let depth = 0; depth < FOLDER_LEVELS; depth++) {
		const groups = byFolder(plots, chosen, depth);
		if (groups.length > most)
			break;
		fitting = groups;
	}
	return fitting;
}
export class Raster {
	cols;
	rows;
	masks;
	places;
	order = [];
	regions;
	borders = [];
	constructor(plots, groups, cols, rows) {
		this.cols = cols;
		this.rows = rows;
		this.masks = new Uint8Array(cols * rows);
		this.places = new Array(plots.length);
		this.regions = rooms(plots, groups, cols, rows);
		const joints = new Uint8Array(cols * rows);
		this.regions.forEach(({ plots: chosen, room }, region) => {
			for (const [plot, tile] of layout(plots, chosen, 2 * (room.w - 2) - 1, 4 * (room.h - 2), 0.5)) {
				this.places[plot] = this.draw(plots[plot], tile, room, region);
				this.order.push(plot);
			}
			addBorder(room, cols, joints);
		});
		addBorder(new Rect(0, 0, cols, rows), cols, joints);
		joints.forEach((arms, at) => {
			if (arms > 0)
				this.borders.push({ at, glyph: LINES[arms] });
		});
	}
	cell(plot, line) {
		const [x, y] = dotOf(this.places[plot], line);
		return [Math.min(div(x, 2), this.cols - 2), Math.min(div(y, 4), this.rows - 2)];
	}
	draw(plot, tile, room, region) {
		const left = 2 * (room.x + 1) + 1;
		const top = 4 * (room.y + 1);
		const x = left + round(tile.x);
		let y = top + round(tile.y);
		let w = left + round(tile.x + tile.w) - x;
		let h = top + round(tile.y + tile.h) - y;
		if (w > 2)
			w--;
		if (w > DOTS_FOR_A_NAME - 1)
			w -= 2;
		if (h > 2)
			h--;
		let name;
		if (Math.min(w, h) >= DOTS_FOR_A_NAME) {
			const row = div(y + 2, 4);
			name = new Rect(div(x + 1, 2), row, div(w, 2) - 1, 1);
			h -= 4 * row + 4 - y;
			y = 4 * row + 4;
		}
		const needed = Math.ceil(plot.outline.length / 2 / Math.max(h, 1));
		const columns = Math.max(Math.min(div(w, COLUMN_DOTS), needed), 1);
		const dots = new Rect(x, y, w, h);
		const runs = runsOf(plot, dots, columns);
		const strokes = [];
		const last = new Map();
		for (const run of runs) {
			for (let dot = run.start; dot < run.end; dot++) {
				const at = (run.y >> 2) * this.cols + (dot >> 1);
				if (at >= this.masks.length)
					continue;
				this.masks[at] |= DOT[run.y & 3][dot & 1];
				let stroke = last.get(at);
				if (stroke?.line !== run.line) {
					stroke = { line: run.line, cell: at, dots: 0 };
					last.set(at, stroke);
					strokes.push(stroke);
				}
				stroke.dots++;
			}
		}
		strokes.sort((a, b) => a.line - b.line || a.cell - b.cell);
		return { dots, columns, lines: plot.lines, region, name, runs, strokes };
	}
}
function rooms(plots, groups, cols, rows) {
	const weight = (group) => sum(group.plots.map(plot => plots[plot].weight));
	const total = (scanned) => sum(groups.filter(group => group.scanned === scanned).map(weight));
	const scanned = total(true);
	const rest = total(false);
	const shrink = scanned > 0 && rest > 0 ? Math.min(scanned / (2 * rest), 1) : 1;
	const least = ((scanned + rest * shrink) * CELLS_PER_REGION) / (cols * rows);
	const sized = groups.map(group => ({ ...group, size: weight(group) * (group.scanned ? 1 : shrink) }));
	for (;;) {
		sized.sort((a, b) => b.size - a.size || Number(b.name > a.name) - Number(b.name < a.name));
		if (sized.length < 2 || sized[sized.length - 1].size >= least)
			break;
		const pair = sized.splice(-2);
		const [lead, other] = pair[1].scanned && !pair[0].scanned ? pair.reverse() : pair;
		const more = lead.name && other.name && !lead.name.endsWith(' +') ? ' +' : '';
		const joined = lead.plots.concat(other.plots);
		sized.push({ name: lead.name + more, plots: joined, scanned: lead.scanned, size: lead.size + other.size });
	}
	const plan = divide(sized.map(group => group.size), { x: 0, y: 0, w: 2 * (cols - 1), h: 4 * (rows - 1) });
	return plan.map((area, n) => {
		const x = round(area.x / 2);
		const y = round(area.y / 4);
		const right = round((area.x + area.w) / 2);
		const bottom = round((area.y + area.h) / 4);
		return { ...sized[n], room: new Rect(x, y, right - x + 1, bottom - y + 1) };
	});
}
function addBorder(room, cols, joints) {
	const right = room.end - 1;
	const bottom = room.y + room.h - 1;
	for (let x = room.x; x < right; x++) {
		for (const y of [room.y, bottom]) {
			joints[y * cols + x] |= RIGHT;
			joints[y * cols + x + 1] |= LEFT;
		}
	}
	for (let y = room.y; y < bottom; y++) {
		for (const x of [room.x, right]) {
			joints[y * cols + x] |= DOWN;
			joints[(y + 1) * cols + x] |= UP;
		}
	}
}
function pick(outline, start, end) {
	if (end - start < 2)
		return start;
	rowsByLength.fill(0);
	for (let row = start; row < end; row++)
		rowsByLength[outline[2 * row + 1]]++;
	let before = div((end - start) * PICKED_FIFTH, 5);
	let length = 0;
	while (before >= rowsByLength[length]) {
		before -= rowsByLength[length];
		length++;
	}
	for (let row = start;; row++) {
		if (outline[2 * row + 1] !== length)
			continue;
		if (before === 0)
			return row;
		before--;
	}
}
function runsOf({ outline, lines }, area, columns) {
	const rows = outline.length / 2;
	const slots = Math.max(area.h * columns, 0);
	const runs = [];
	if (rows === 0) {
		for (let y = 0; y < area.h; y++) {
			const line = 1 + whole((y * lines) / area.h);
			for (let x = y % 2; x < area.w; x += 2)
				runs.push({ line, y: area.y + y, start: area.x + x, end: area.x + x + 1 });
		}
		return runs;
	}
	const step = div(area.w, columns);
	const span = columns > 1 ? step - 1 : step;
	if (slots === 0 || span <= 0)
		return runs;
	const rowAt = (slot) => whole((slot * rows) / slots);
	const length = (row) => outline[2 * row + 1];
	const picked = [];
	for (let slot = 0; slot < slots; slot++)
		picked.push(pick(outline, rowAt(slot), rowAt(slot + 1)));
	const longest = new Uint8Array(picked.map(length)).sort()[div(slots * WIDEST_FIFTH, 5)];
	const scale = span / clamp(longest, SHORTEST_LINE, LONGEST_LINE);
	picked.forEach((row, slot) => {
		const spare = slots >= 2 * rows && rowAt(slot + 1) !== row;
		const tall = slot >= TALLEST_LINE && rowAt(slot - TALLEST_LINE) === row;
		if (length(row) === 0 || spare || tall)
			return;
		const start = Math.min(whole(outline[2 * row] * scale), span - 1);
		const end = clamp(round(length(row) * scale), start + 1, span);
		const x = area.x + div(slot, area.h) * step;
		runs.push({ line: 1 + whole((row * lines) / rows), y: area.y + (slot % area.h), start: x + start, end: x + end });
	});
	return runs;
}
